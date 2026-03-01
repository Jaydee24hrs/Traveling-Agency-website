from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class RememberMeBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user and request.session.get('remember_password'):
            # Add custom logic to generate and validate remember me token
            # For demonstration purposes, we assume a simple check on username for now
            if request.session.get('email') == username:
                return user
        return None
