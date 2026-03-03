from rest_framework import serializers
from .models import StudentProfile, ActivityLog

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['username', 'student_id', 'is_approved', 'total_xp', 'current_streak', 'daily_goal_minutes']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add a custom message based on approval status
        if instance.is_approved:
            data['message'] = "Welcome back to Natdemy!"
        else:
            data['message'] = "Your account is pending approval. Please contact your institute."
        return data

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'activity_type', 'duration_minutes', 'quiz_score', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    # This ensures the app gets the full http://127.0.0.1:8000/media/... link
    profile_photo = serializers.ImageField(required=False)

    class Meta:
        model = StudentProfile
        fields = [
            'username', 'student_id', 'profile_photo', 'total_xp', 'current_level', 'unlocked_chapter',
            'listening_xp', 'speaking_xp', 'reading_xp', 'writing_xp', 'learning_xp',
            'listening_level', 'speaking_level', 'reading_level', 'writing_level', 'learning_level'
        ]