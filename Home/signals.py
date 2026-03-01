# # tykttApp/signals.py

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# import json

# from .models import Corporate_Business  # Replace with your actual Corporate_Business model

# @receiver(post_save, sender=Corporate_Business)
# def corporate_user_registered(sender, instance, created, **kwargs):
#     if created:
#         channel_layer = get_channel_layer()
#         user_data = {
#             "company_reg_name": instance.company_reg_name,
#             "company_email": instance.company_email,
#             "company_phone_number": f"{instance.company_phone_number_dial_code} {instance.company_phone_number}",
#             "date_joined": instance.date_joined.strftime("%b. %d, %Y") if instance.date_joined else None,
#             "business_type": instance.business_type,
#             "status": instance.status,
#             # Add other relevant fields
#         }
#         message = "New Corporate User Registered"
#         async_to_sync(channel_layer.group_send)(
#             "user_registration",
#             {
#                 'type': 'notify_users',
#                 'message': message,
#                 'user_data': user_data
#             }
#         )
