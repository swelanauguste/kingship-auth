from django.urls import path

from . import views

urlpatterns = [
    path("sso/login/", views.sso_login, name="sso_login"),
    path("sso/verify/", views.sso_verify, name="sso_verify"),
]
