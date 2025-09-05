from django.contrib import admin
from .models import User, DeviceInfo, MasterToken, SessionToken

admin.site.register(User)
admin.site.register(DeviceInfo)
admin.site.register(MasterToken)
admin.site.register(SessionToken)