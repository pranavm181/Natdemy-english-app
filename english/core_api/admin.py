from django.contrib import admin
from .models import StudentProfile, ActivityLog, GlobalXPConfig

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'total_xp', 'current_level', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'student_id')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity_type', 'duration_minutes', 'quiz_score', 'timestamp')
    list_filter = ('activity_type', 'timestamp')

@admin.register(GlobalXPConfig)
class GlobalXPConfigAdmin(admin.ModelAdmin):
    list_display = ('points_per_activity', 'overall_intermediate', 'overall_professional')