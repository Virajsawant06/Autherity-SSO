from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.conf import settings

class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authsystem_user'
        app_label = 'authsystem'

    def __str__(self):
        return self.username

class DeviceInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'device_id')

    def __str__(self):
        return f"Device {self.device_id} for {self.user.username}"

# Master token representing user's core identity for SSO
class MasterToken(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    device = models.ForeignKey('DeviceInfo', on_delete=models.CASCADE, null=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and timezone.now() <= self.expires_at

    def __str__(self):
        return f"{str(self.token)}"

# Session token for a single login session, generated from MasterToken
class SessionToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and timezone.now() <= self.expires_at

    def __str__(self):
        return f"SessionToken({self.token}) for {self.user.username}"

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
