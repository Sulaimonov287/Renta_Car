import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.dogovor_id = self.scope['url_route']['kwargs']['dogovor_id']
        self.room_group_name = f'chat_{self.dogovor_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('text')
        username = data.get('username')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'text': event['message'],
            'sender_username': event['username']
        }))