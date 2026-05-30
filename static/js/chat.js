document.addEventListener("DOMContentLoaded", () => {
    // Determine context (Full page or floating widget)
    const mainContainer = document.getElementById('chat-container-main');
    const floatingContainer = document.getElementById('chat-container-floating');

    // We only initialize if user is logged in (detect via data attribute)
    const currentUserId = document.body.dataset.userId;
    if (!currentUserId) return;

    let activeConversationId = null;
    let chatSocket = null;
    let conversations = [];

    // Elements
    const convListEl = document.getElementById('chat-conversations-list');
    const msgListEl = document.getElementById('chat-messages-list');
    const chatInputArea = document.getElementById('chat-input-area');
    const chatActiveName = document.getElementById('chat-active-name');
    const chatForm = document.getElementById('chat-message-form');
    const chatInput = document.getElementById('chat-message-input');

    // Floating Widget Elements
    const chatFab = document.getElementById('chat-fab');
    const chatWidget = document.getElementById('chat-floating-widget');
    const closeWidgetBtn = document.getElementById('close-chat-widget');

    if (chatFab) {
        chatFab.addEventListener('click', () => {
            if (chatWidget.style.display === 'none' || chatWidget.style.display === '') {
                chatWidget.style.display = 'flex';
                loadConversations();
            } else {
                chatWidget.style.display = 'none';
            }
        });
    }

    if (closeWidgetBtn) {
        closeWidgetBtn.addEventListener('click', () => {
            chatWidget.style.display = 'none';
        });
    }

    // Search input listener
    const searchInput = document.getElementById('chat-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            renderConversationsFiltered(query);
        });
    }



    // New Chat Button Handler with Autocomplete Search
    const handleNewChat = () => {
        Swal.fire({
            title: 'Search Users',
            html: `
                <input type="text" id="user-search-input" class="swal2-input" placeholder="Search by name, username, or email..." autocomplete="off">
                <div id="user-search-results" style="max-height: 250px; overflow-y: auto; text-align: left; margin-top: 15px; border-radius: 8px;"></div>
            `,
            showConfirmButton: false,
            showCancelButton: true,
            cancelButtonText: 'Cancel',
            didOpen: () => {
                const searchInput = document.getElementById('user-search-input');
                const searchResults = document.getElementById('user-search-results');

                searchInput.focus();

                // Debounce timer
                let timeout = null;

                searchInput.addEventListener('input', (e) => {
                    clearTimeout(timeout);
                    const q = e.target.value.trim();

                    if (q.length < 2) {
                        searchResults.innerHTML = '<div style="padding: 10px; color: #888; text-align: center;">Type at least 2 characters to search...</div>';
                        return;
                    }

                    searchResults.innerHTML = '<div style="padding: 10px; color: #888; text-align: center;">Searching...</div>';

                    timeout = setTimeout(async () => {
                        try {
                            const res = await fetch(`/chat/api/users/search/?q=${encodeURIComponent(q)}`);
                            const data = await res.json();

                            searchResults.innerHTML = '';
                            if (data.users.length === 0) {
                                searchResults.innerHTML = '<div style="padding: 10px; color: #888; text-align: center;">No users found.</div>';
                                return;
                            }

                            data.users.forEach(u => {
                                const div = document.createElement('div');
                                div.style = "padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; flex-direction: column; transition: background 0.2s;";
                                div.onmouseover = () => div.style.background = '#f8f9fa';
                                div.onmouseout = () => div.style.background = 'transparent';

                                const nameDisplay = u.name ? `${u.name} (@${u.username})` : `@${u.username}`;
                                const roleBadge = u.role ? `<span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-left: 8px; color: #495057;">${u.role}</span>` : '';

                                div.innerHTML = `<div style="font-weight: 500; color: #333; display: flex; align-items: center;">${nameDisplay} ${roleBadge}</div>`;

                                div.onclick = () => {
                                    Swal.close();
                                    startChatWithUser(u.id);
                                };
                                searchResults.appendChild(div);
                            });
                        } catch (err) {
                            searchResults.innerHTML = '<div style="padding: 10px; color: red; text-align: center;">Error searching users.</div>';
                        }
                    }, 300);
                });
            }
        });
    };

    // Attach to any element with .new-chat-btn
    document.querySelectorAll('.new-chat-btn').forEach(btn => {
        btn.addEventListener('click', handleNewChat);
    });

    // Determine target elements (fallback to floating if main not present)
    const getTargetEl = (mainId, floatId) => {
        return document.getElementById(mainId) || document.getElementById(floatId);
    };

    const targetConvList = getTargetEl('chat-conversations-list', 'chat-floating-conversations');
    const targetMsgList = getTargetEl('chat-messages-list', 'chat-floating-messages');
    const targetInputArea = getTargetEl('chat-input-area', 'chat-floating-input-area');
    const targetActiveName = getTargetEl('chat-active-name', 'chat-floating-name');
    const targetForm = getTargetEl('chat-message-form', 'chat-floating-form');
    const targetInput = getTargetEl('chat-message-input', 'chat-floating-input');
    const floatBackBtn = document.getElementById('chat-floating-back');

    // Initial load
    if (mainContainer || (chatWidget && !chatWidget.classList.contains('d-none'))) {
        loadConversations();
    }

    async function loadConversations() {
        if (!targetConvList) return;
        try {
            const res = await fetch('/chat/api/conversations/');
            const data = await res.json();
            conversations = data.conversations || [];
            renderConversations();
        } catch (e) {
            console.error("Failed to load conversations", e);
        }
    }

    function renderConversations() {
        const searchInput = document.getElementById('chat-search-input');
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        renderConversationsFiltered(query);
    }

    function renderConversationsFiltered(query = '') {
        if (!targetConvList) return;
        targetConvList.innerHTML = '';
        
        const filtered = conversations.filter(conv => {
            const nameMatch = conv.other_user.username.toLowerCase().includes(query);
            const msgMatch = (conv.last_message || '').toLowerCase().includes(query);
            return nameMatch || msgMatch;
        });

        if (filtered.length === 0) {
            targetConvList.innerHTML = '<div class="p-4 text-center text-muted small">No conversations found</div>';
            return;
        }

        filtered.forEach(conv => {
            const div = document.createElement('div');
            const isFloating = targetConvList.id === 'chat-floating-conversations';
            
            if (isFloating) {
                div.className = `chat-conv-item ${conv.id === activeConversationId ? 'active' : ''}`;
                
                let avatarHtml = '';
                if (conv.other_user.profile_picture_url) {
                    avatarHtml = `<img src="${conv.other_user.profile_picture_url}" class="chat-conv-avatar" alt="${conv.other_user.username}">`;
                } else {
                    const initial = conv.other_user.username.charAt(0).toUpperCase();
                    avatarHtml = `<div class="chat-conv-avatar-placeholder">${initial}</div>`;
                }

                const timeStr = new Date(conv.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const unreadBadge = conv.unread_count > 0 ? `<span class="chat-conv-unread-badge">${conv.unread_count}</span>` : '';

                div.innerHTML = `
                    <div class="chat-conv-item-left">
                        ${avatarHtml}
                    </div>
                    <div class="chat-conv-item-middle">
                        <span class="chat-conv-name">${conv.other_user.username}</span>
                        <span class="chat-conv-lastmsg">${conv.last_message || '<i>No messages</i>'}</span>
                    </div>
                    <div class="chat-conv-item-right">
                        <span class="chat-conv-time">${timeStr}</span>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            ${unreadBadge}
                            <button class="list-delete-btn" style="background:none; border:none; color: #dc3545; cursor:pointer; padding: 2px; font-size: 0.85rem;" title="Delete Chat"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                `;
            } else {
                div.className = `p-3 border-bottom cursor-pointer conversation-item ${conv.id === activeConversationId ? 'bg-light' : 'bg-white'}`;
                div.style.cursor = 'pointer';

                const timeStr = new Date(conv.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-dark">${conv.other_user.username}</strong>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <small class="text-muted" style="font-size: 0.7rem;">${timeStr}</small>
                            <button class="list-delete-btn" style="background:none; border:none; color: #dc3545; cursor:pointer; padding: 2px;"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                    <div class="text-muted text-truncate small" style="max-width: 90%;">
                        ${conv.last_message || '<i>No messages</i>'}
                    </div>
                `;
            }

            div.addEventListener('click', (e) => {
                if (e.target.closest('.list-delete-btn')) {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                } else {
                    openConversation(conv);
                }
            });
            targetConvList.appendChild(div);
        });
    }

    async function openConversation(conv) {
        conv.unread_count = 0;
        activeConversationId = conv.id;
        renderConversations(); // highlight active

        if (targetActiveName) targetActiveName.textContent = conv.other_user.username;
        if (targetInputArea) targetInputArea.style.display = 'block';
        document.querySelectorAll('.delete-chat-btn').forEach(b => b.style.display = 'inline-block');

        // UI for floating widget (hide list, show chat)
        const floatListPanel = document.getElementById('chat-floating-list-panel');
        const floatChatPanel = document.getElementById('chat-floating-chat-panel');
        if (floatListPanel && floatChatPanel) {
            floatListPanel.style.display = 'none';
            floatChatPanel.style.display = 'flex';
        }

        // Fetch messages
        targetMsgList.innerHTML = '<div class="text-center p-3 text-muted">Loading messages...</div>';
        try {
            const res = await fetch(`/chat/api/conversations/${conv.id}/messages/`);
            const data = await res.json();
            renderMessages(data.messages || []);
            connectWebSocket(conv.id);
        } catch (e) {
            targetMsgList.innerHTML = '<div class="text-danger p-3">Error loading messages.</div>';
        }
    }

    if (floatBackBtn) {
        floatBackBtn.addEventListener('click', () => {
            document.getElementById('chat-floating-list-panel').style.display = 'flex';
            document.getElementById('chat-floating-chat-panel').style.display = 'none';
            document.querySelectorAll('.delete-chat-btn').forEach(b => b.style.display = 'none');
            if (chatSocket) chatSocket.close();
            activeConversationId = null;
        });
    }

    // Reusable Delete Function
    async function deleteConversation(id) {
        const result = await Swal.fire({
            title: 'Delete Conversation?',
            text: "This will permanently delete the chat history for both users.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!'
        });

        if (result.isConfirmed) {
            try {
                const res = await fetch(`/chat/api/conversations/${id}/`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();

                if (data.success) {
                    if (activeConversationId === id) {
                        if (chatSocket) chatSocket.close();
                        activeConversationId = null;

                        document.querySelectorAll('.delete-chat-btn').forEach(b => b.style.display = 'none');
                        if (targetActiveName) targetActiveName.textContent = 'Select a conversation';
                        if (targetInputArea) targetInputArea.style.display = 'none';

                        const emptyStateHtml = '<div class="text-center mt-5 text-muted"><i class="fas fa-comments fa-3x mb-3"></i><p>Select a conversation from the left to start messaging</p></div>';
                        if (targetMsgList) targetMsgList.innerHTML = emptyStateHtml;

                        const floatListPanel = document.getElementById('chat-floating-list-panel');
                        const floatChatPanel = document.getElementById('chat-floating-chat-panel');
                        if (floatListPanel && floatChatPanel && chatWidget && chatWidget.style.display !== 'none') {
                            floatListPanel.style.display = 'flex';
                            floatChatPanel.style.display = 'none';
                        }
                    }

                    await loadConversations();
                    Swal.fire('Deleted!', 'The conversation has been deleted.', 'success');
                } else {
                    Swal.fire('Error', data.error || 'Failed to delete', 'error');
                }
            } catch (e) {
                console.error(e);
                Swal.fire('Error', 'An error occurred.', 'error');
            }
        }
    }

    // Delete Chat Handler (Active Chat Header)
    document.querySelectorAll('.delete-chat-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (activeConversationId) {
                deleteConversation(activeConversationId);
            }
        });
    });

    function renderMessages(messages) {
        targetMsgList.innerHTML = '';
        if (messages.length === 0) {
            targetMsgList.innerHTML = '<div class="text-center mt-4 text-muted small">Send a message to start the conversation!</div>';
            return;
        }

        messages.forEach(msg => appendMessage(msg));
        scrollToBottom();
    }

    function appendMessage(msg) {
        const isMe = msg.sender_id.toString() === currentUserId.toString();
        const isFloating = targetMsgList.id === 'chat-floating-messages';
        const div = document.createElement('div');
        const timeStr = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (isFloating) {
            div.className = `chat-bubble-container ${isMe ? 'me' : 'other'}`;
            div.innerHTML = `
                <div class="chat-bubble">
                    ${msg.content || msg.message}
                </div>
                <span class="chat-bubble-time">${timeStr}</span>
            `;
        } else {
            div.className = `d-flex flex-column mb-3 ${isMe ? 'align-items-end' : 'align-items-start'}`;
            div.innerHTML = `
                <div class="px-3 py-2 rounded-3 text-white" style="max-width: 80%; background-color: ${isMe ? '#4F46E5' : '#6c757d'};">
                     ${msg.content || msg.message}
                </div>
                <small class="text-muted mt-1" style="font-size: 0.65rem;">${timeStr}</small>
            `;
        }
        targetMsgList.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        targetMsgList.scrollTop = targetMsgList.scrollHeight;
    }

    function connectWebSocket(convId) {
        if (chatSocket) {
            chatSocket.close();
        }

        const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
        const wsUrl = `${wsScheme}://${window.location.host}/ws/chat/${convId}/`;

        chatSocket = new WebSocket(wsUrl);

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            if (data.type === 'chat_message') {
                // Remove empty state message if it exists
                if (targetMsgList.innerHTML.includes('Send a message to start')) {
                    targetMsgList.innerHTML = '';
                }
                appendMessage(data);

                // Update conversation list preview
                const conv = conversations.find(c => c.id === activeConversationId);
                if (conv) {
                    conv.last_message = data.content || data.message;
                    conv.updated_at = data.timestamp;
                    renderConversations();
                }
            }
        };

        chatSocket.onclose = function (e) {
            console.error('Chat socket closed unexpectedly');
        };
    }

    if (targetForm) {
        targetForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const message = targetInput.value.trim();
            if (message && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({
                    'message': message
                }));
                targetInput.value = '';
            }
        });
    }

    // Expose global function to start chat with a specific user (e.g. from job detail page)
    window.startChatWithUser = async function (userId) {
        try {
            const res = await fetch('/chat/api/conversations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId })
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
                return;
            }

            if (chatWidget && !mainContainer) {
                chatWidget.style.display = 'flex';
                await loadConversations();
                const conv = conversations.find(c => c.id === data.id);
                if (conv) openConversation(conv);
            } else if (mainContainer) {
                await loadConversations();
                const conv = conversations.find(c => c.id === data.id);
                if (conv) openConversation(conv);
            } else {
                window.location.href = `/chat/?conv_id=${data.id}`;
            }
        } catch (e) {
            console.error(e);
        }
    };

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
