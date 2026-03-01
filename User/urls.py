from django.urls import path, re_path
from django.contrib.auth import views as auth_views

from .views import (create_team, update_team, verify_otp, resend_password, update_team_business,
                    profile, delete_user, assign_user, change_password, update_team_info)

urlpatterns = [
    path('create_team/', create_team, name='create_team'),
    path('update_team/<int:user_id>', update_team, name='update_team'),
    path('update_team_info/', update_team_info, name='update_team_info'),
    path('update_team_business/<int:team_id>/<int:company_id>', update_team_business, name='update_team_business'),
    path('verify_otp', verify_otp, name='verify_otp'),
    path('profile', profile, name='profile'),
    path('assign_user/<int:user_id>', assign_user, name='assign_user'),
    path('delete_user/<int:user_id>', delete_user, name='delete_user'),
    path('change_password', change_password, name='change_password'),
    path('resend_password/<int:user_id>', resend_password, name='resend_password'),


    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

