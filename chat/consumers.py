import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        if self.user.is_anonymous:
            await self.close()
            return

        # Check if user is a participant
        is_participant = await self.is_participant(self.user.id, self.conversation_id)
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')
        
        if not message_content:
            return

        # Save message to database
        saved_message = await self.save_message(self.user.id, self.conversation_id, message_content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'content': saved_message['content'],
                'sender_id': saved_message['sender_id'],
                'sender_username': saved_message['sender_username'],
                'timestamp': saved_message['timestamp'],
                'id': saved_message['id'],
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event['id'],
            'content': event.get('content', event.get('message')),
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def is_participant(self, user_id, conversation_id):
        try:
            conv = Conversation.objects.get(id=conversation_id)
            return conv.participants.filter(id=user_id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user_id, conversation_id, message):
        from django.utils import timezone
        user = User.objects.get(id=user_id)
        msg = Message.objects.create(
            conversation_id=self.conversation_id,
            sender=user,
            content=message
        )
        Conversation.objects.filter(id=self.conversation_id).update(updated_at=timezone.now())
        return {
            'id': msg.id,
            'content': msg.content,
            'sender_id': user.id,
            'sender_username': user.username,
            'timestamp': msg.timestamp.isoformat(),
        }
