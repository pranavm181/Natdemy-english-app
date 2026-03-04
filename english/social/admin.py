from django.contrib import admin
from .models import CallLog, FriendRequest

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'contact_name', 'call_type', 'duration_seconds', 'timestamp')
    list_filter = ('call_type', 'timestamp')

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'timestamp')
    list_filter = ('status',)
