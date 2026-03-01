from django.db.models.signals import pre_migrate, post_migrate
from django.dispatch import receiver
from .utils import create_default_group



# For Websocket
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import CustomUser 


@receiver(pre_migrate)
def run_before_migrations(sender, **kwargs):
    # print("This runs before any migration.")
    # Add your custom code here
    pass


@receiver(post_migrate)
def run_after_migrations(sender, **kwargs):
    create_default_group()
    # Add your custom code here




# User/signals.py
# @receiver(post_save, sender=CustomUser)
# def private_user_registered(sender, instance, created, **kwargs):
#     if created:
#         channel_layer = get_channel_layer()
#         user_data = {            
#             "company_reg_name": f"{instance.first_name} {instance.last_name}",
#             "company_email": instance.email,
#             "company_phone_number": f"{instance.phone_number_dial_code} {instance.phone}",
#             "date_joined": instance.created_on.strftime("%b. %d, %Y") if instance.created_on else None,
#             "business_type": 'Private',
#             "status": instance.status,
#             # Add other relevant fields
#         }
#         message = "New Private User Registered"
#         async_to_sync(channel_layer.group_send)(
#             "user_registration",
#             {
#                 'type': 'notify_users',
#                 'message': message,
#                 'user_data': user_data
#             }
#         )
