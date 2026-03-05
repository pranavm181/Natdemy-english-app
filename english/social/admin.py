from .models import CallLog, FriendRequest, SpeakingTopic, ActiveCall

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'contact_name', 'call_type', 'duration_seconds', 'timestamp')
    list_filter = ('call_type', 'timestamp')

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'timestamp')
    list_filter = ('status',)

@admin.register(SpeakingTopic)
class SpeakingTopicAdmin(admin.ModelAdmin):
    list_display = ('text', 'level', 'created_at')
    list_filter = ('level',)

@admin.register(ActiveCall)
class ActiveCallAdmin(admin.ModelAdmin):
    list_display = ('caller', 'receiver', 'topic', 'is_active', 'created_at')
    list_filter = ('is_active',)
