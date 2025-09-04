from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

# Custom User model (optional, but recommended for extensibility)
class User(AbstractUser):
    pass  # Use Django's default fields: username, email, password, etc.

# Device info model to track where user logs in from
class DeviceInfo(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.device_id

# Master token representing user's core identity for SSO
class MasterToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(DeviceInfo, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MasterToken({self.token}) for User({self.user.username})"

# Session token for a single login session, generated from MasterToken
class SessionToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    master_token = models.ForeignKey(MasterToken, on_delete=models.CASCADE)
    device = models.ForeignKey(DeviceInfo, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Session token valid for 1 hour (adjust as needed)
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"SessionToken({self.token}) for User({self.user.username})"

# Logs for auditing login and token usage
class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    device = models.ForeignKey(DeviceInfo, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    success = models.BooleanField(default=True)
    action = models.CharField(max_length=50)  # 'login', 'logout', 'sso_login', etc.

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
