import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class ClientApp(models.Model):
    """
    Represents a client application that can integrate with your SSO.
    """

    name = models.CharField(max_length=100, unique=True)
    client_id = models.CharField(max_length=100, unique=True)
    allowed_origin = models.URLField()  # where redirects are allowed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Represents a role that can be assigned to a user for a client app.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    Assigns a role to a user within a specific client app.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(ClientApp, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "app", "role")


class OneTimeSSOToken(models.Model):
    """
    Token used for SSO handoff between auth server and client app.
    """

    token = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(ClientApp, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    nonce = models.UUIDField(default=uuid.uuid4, editable=False)

    def is_valid(self):
        return (not self.used) and (timezone.now() < self.expires_at)
