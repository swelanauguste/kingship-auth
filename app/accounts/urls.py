# accounts/urls.py
from django.urls import path
from .views import activate_and_continue, register, activate_and_set_password

urlpatterns = [
    path("activate/<str:token>/", activate_and_set_password, name="activate_and_continue"),
    path("register/", register, name="register"),
]
