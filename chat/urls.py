from django.urls import path
from .views import ConversationListView, MessageListView, ChatIndexView, UserSearchView, ConversationDetailView

app_name = 'chat'

urlpatterns = [
    path('', ChatIndexView.as_view(), name='index'),
    path('api/users/search/', UserSearchView.as_view(), name='users_search_api'),
    path('api/conversations/', ConversationListView.as_view(), name='conversations_api'),
    path('api/conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail_api'),
    path('api/conversations/<int:pk>/messages/', MessageListView.as_view(), name='messages_api'),
]
