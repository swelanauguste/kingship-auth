from django.conf import settings
from django.core import signing
from django.utils import timezone
from datetime import timedelta
from .models import OneTimeSSOToken, ClientApp
import uuid

SSO_SALT = "accounts.sso"


def create_one_time_token(user, app):
    """
    Create a DB-backed one-time SSO token tied to a specific client app.
    Returns the signed token string.
    """
    expires_at = timezone.now() + timedelta(seconds=settings.SSO_TOKEN_TTL)
    raw = str(uuid.uuid4())

    record = OneTimeSSOToken.objects.create(
        token=raw,
        user=user,
        app=app,
        expires_at=expires_at
    )

    payload = {"record_id": record.pk, "nonce": str(record.nonce)}
    signed = signing.dumps(payload, salt=settings.SSO_SALT)
    return signed


def verify_and_mark_token(signed_token):
    """
    Verify signed token, check DB record, mark as used, and return (user, app, error).
    """
    try:
        payload = signing.loads(signed_token, salt=settings.SSO_SALT, max_age=settings.SSO_TOKEN_TTL)
    except signing.SignatureExpired:
        return None, None, "token_expired"
    except signing.BadSignature:
        return None, None, "bad_token"

    record_id = payload.get("record_id")
    nonce = payload.get("nonce")

    try:
        record = OneTimeSSOToken.objects.select_for_update().get(pk=record_id)
    except OneTimeSSOToken.DoesNotExist:
        return None, None, "no_record"

    if str(record.nonce) != str(nonce):
        return None, None, "nonce_mismatch"
    if not record.is_valid():
        return None, None, "invalid_or_used"

    record.used = True
    record.save(update_fields=["used"])

    return record.user, record.app, None
