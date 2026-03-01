# import json
# from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
# # Django Channels imports
# from asgiref.sync import async_to_sync  # To synchronize async code in the view


# class TransactionConsumer(WebsocketConsumer):
#     def connect(self):
#         self.user = self.scope['user']
#         self.user_group_name = f'user_{self.user.id}'

#         # Join user's personal group
#         async_to_sync(self.channel_layer.group_add)(
#             self.user_group_name,
#             self.channel_name
#         )

#         self.accept()

#     def disconnect(self, close_code):
#         # Leave user's personal group
#         async_to_sync(self.channel_layer.group_discard)(
#             self.user_group_name,
#             self.channel_name
#         )

#     def send_transaction(self, event):
#         transaction = event['transaction']

#         # Send transaction data to WebSocket
#         self.send(text_data=json.dumps({
#             'transaction': transaction
#         }))
