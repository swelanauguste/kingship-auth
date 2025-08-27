from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from oauth2_provider.models import Application

from .forms import RegistrationForm, SetPasswordForm
from .models import User
from .utils import make_activation_token, load_activation_token, send_activation_email


def register(request):
    """User registration view."""
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send activation email
            send_activation_email(user)
            return render(
                request, "accounts/registration_done.html", {"email": user.email}
            )
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def activate_and_set_password(request, token):
    """Activation link where user sets their password."""
    payload = load_activation_token(token)
    if not payload:
        return render(request, "accounts/activation_invalid.html")

    user_pk = payload.get("user_pk")
    user = get_object_or_404(User, pk=user_pk)

    if request.method == "POST":
        form = SetPasswordForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user.is_active = True
            user.save()
            login(request, user)
            # Optionally redirect to a default page or client
            return redirect(settings.LOGIN_REDIRECT_URL or "/")
    else:
        form = SetPasswordForm(instance=user)

    return render(request, "accounts/activation_set_password.html", {"form": form})


def activate_and_continue(request, token):
    """Activation + OAuth continuation flow."""
    payload = load_activation_token(token)
    if not payload:
        return render(request, "accounts/activation_invalid.html", status=400)

    user_pk = payload.get("user_pk")
    client_id = payload.get("client_id")
    redirect_uri = payload.get("redirect_uri")
    state = payload.get("state")

    user = get_object_or_404(User, pk=user_pk)

    if not user.is_active:
        user.is_active = True
        user.save()

    login(request, user)

    if client_id:
        try:
            app = Application.objects.get(client_id=client_id)
        except Application.DoesNotExist:
            return render(
                request,
                "accounts/activation_invalid.html",
                {"error": "Invalid client_id"},
                status=400,
            )

        # Validate redirect_uri if provided
        if redirect_uri:
            allowed_uris = [u.strip() for u in app.redirect_uris.split() if u.strip()]
            if redirect_uri not in allowed_uris:
                return render(
                    request,
                    "accounts/activation_invalid.html",
                    {"error": "redirect_uri not allowed"},
                    status=400,
                )

        # Build OAuth2 authorize URL
        authorize_path = reverse("oauth2_provider:authorize")
        authorize_url = request.build_absolute_uri(authorize_path)
        params = {"response_type": "code", "client_id": client_id}
        if redirect_uri:
            params["redirect_uri"] = redirect_uri
        if state:
            params["state"] = state
        query_string = urlencode(params)
        return redirect(f"{authorize_url}?{query_string}")

    # Default fallback
    return redirect(settings.LOGIN_REDIRECT_URL or "/")


