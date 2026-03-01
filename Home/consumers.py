# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class UserRegistrationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Join the user_registration group
#         await self.channel_layer.group_add(
#             "user_registration",
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave the user_registration group
#         await self.channel_layer.group_discard(
#             "user_registration",
#             self.channel_name
#         )

#     # Receive message from group
#     async def notify_users(self, event):
#         message = event['message']
#         user_data = event['user_data']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'message': message,
#             'user_data': user_data
#         }))
