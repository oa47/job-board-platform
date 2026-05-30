import json
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.db.models import Q, Prefetch
from .models import Conversation, Message

User = get_user_model()

class UserSearchView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse({'users': []})
            
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        data = []
        for u in users:
            data.append({
                'id': u.id,
                'username': u.username,
                'name': u.get_full_name(),
                'role': getattr(u, 'role', ''),
            })
            
        return JsonResponse({'users': data})

class ChatIndexView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'chat/index.html')

@method_decorator(csrf_exempt, name='dispatch')
class ConversationListView(LoginRequiredMixin, View):
    def get(self, request):
        conversations = request.user.conversations.prefetch_related(
            'participants',
            Prefetch('messages', queryset=Message.objects.order_by('-timestamp'), to_attr='ordered_messages')
        ).all()
        
        data = []
        for conv in conversations:
            # Fix N+1: Use list comprehension on prefetched data instead of .exclude() which hits DB
            other_participants = [p for p in conv.participants.all() if p.id != request.user.id]
            if not other_participants:
                continue
            other_user = other_participants[0]
            
            # Fix N+1: Use prefetched ordered_messages instead of .last()
            last_message = conv.ordered_messages[0] if conv.ordered_messages else None
            unread_count = sum(1 for m in conv.ordered_messages if m.sender_id != request.user.id and not m.is_read)
            
            profile_pic_url = None
            try:
                if other_user.profile and other_user.profile.profile_picture:
                    profile_pic_url = other_user.profile.profile_picture.url
            except Exception:
                pass

            data.append({
                'id': conv.id,
                'other_user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'role': getattr(other_user, 'role', ''),
                    'profile_picture_url': profile_pic_url,
                },
                'updated_at': conv.updated_at.isoformat(),
                'last_message': last_message.content if last_message else None,
                'is_read': last_message.is_read if last_message else True,
                'unread_count': unread_count,
            })
        return JsonResponse({'conversations': data})

    def post(self, request):
        try:
            body = json.loads(request.body)
            target_user_id = body.get('user_id')
            target_username = body.get('username')
            
            if target_user_id:
                target_user = get_object_or_404(User, id=target_user_id)
            elif target_username:
                target_user = User.objects.filter(username=target_username).first()
                if not target_user:
                    return JsonResponse({'error': f"User '{target_username}' not found."}, status=404)
            else:
                return JsonResponse({'error': 'user_id or username is required'}, status=400)
                
            if target_user == request.user:
                return JsonResponse({'error': 'Cannot create conversation with yourself'}, status=400)
                
            # Check if conversation already exists
            existing_conv = request.user.conversations.filter(participants=target_user).first()
            if existing_conv:
                return JsonResponse({'id': existing_conv.id, 'created': False})
                
            # Create new conversation
            conv = Conversation.objects.create()
            conv.participants.add(request.user, target_user)
            
            return JsonResponse({'id': conv.id, 'created': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

class MessageListView(LoginRequiredMixin, View):
    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        
        # Verify user is participant
        if not conv.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        messages = conv.messages.select_related('sender').all()
        
        # Mark as read
        unread = messages.exclude(sender=request.user).filter(is_read=False)
        if unread.exists():
            unread.update(is_read=True)
            
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_username': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'is_read': msg.is_read,
            })
            
        return JsonResponse({'messages': data})

@method_decorator(csrf_exempt, name='dispatch')
class ConversationDetailView(LoginRequiredMixin, View):
    def delete(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        
        # Verify user is participant
        if not conv.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        conv.delete()
        return JsonResponse({'success': True})
