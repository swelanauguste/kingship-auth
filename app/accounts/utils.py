from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse

SIGNER_SALT = "accounts.activation"
# TTL in seconds (default 48 hours)
ACTIVATION_MAX_AGE = getattr(settings, "ACTIVATION_MAX_AGE", 60 * 60 * 48)


def make_activation_token(user, client_id=None, redirect_uri=None, state=None):
    """
    Create a signed token containing the user PK and optional OAuth parameters.
    """
    payload = {
        "user_pk": int(user.pk),
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return signing.dumps(payload, salt=SIGNER_SALT)


def load_activation_token(token, max_age=ACTIVATION_MAX_AGE):
    """
    Load and verify a signed activation token.
    Returns a dict with user_pk, client_id, redirect_uri, state if valid, else None.
    """
    try:
        payload = signing.loads(token, salt=SIGNER_SALT, max_age=max_age)
        return payload
    except (signing.SignatureExpired, signing.BadSignature):
        return None


def send_activation_email(user, client_id=None, redirect_uri=None, state=None):
    """
    Send an activation email containing a link with a signed token.
    """
    token = make_activation_token(
        user, client_id=client_id, redirect_uri=redirect_uri, state=state
    )
    activation_path = reverse("activate_and_continue", args=[token])
    activation_link = settings.SITE_BASE_URL.rstrip("/") + activation_path
    subject = "Activate your account"
    body = (
        f"Hello {user.username},\n\n"
        f"Click the link below to activate and continue:\n\n{activation_link}\n\n"
        f"This link expires in 48 hours."
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
    return token
