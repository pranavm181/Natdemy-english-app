from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StudentProfile, ActivityLog, GlobalXPConfig, StudentState

class StudentStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentState
        fields = ['last_activity_type', 'last_item_id', 'live_data', 'updated_at']
        read_only_fields = ['updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, required=False)
    profile_photo = serializers.ImageField(required=False)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'username', 'email', 'password', 'student_id', 'profile_photo', 'is_approved',
            'is_online', 'is_dnd', 'total_xp', 'current_level', 'unlocked_chapter',
            'listening_xp', 'speaking_xp', 'reading_xp', 'writing_xp', 'learning_xp',
            'listening_level', 'speaking_level', 'reading_level', 'writing_level', 'learning_level'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password', None)
        user = instance.user
        
        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        if password:
            user.set_password(password)
        user.save()
        
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.is_approved:
            data['message'] = "Your account is pending approval. Please contact your institute."
        else:
            data['message'] = "Welcome to Natdemy!"
        return data

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'activity_type', 'duration_minutes', 'quiz_score', 'xp_earned', 'item_id', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class AdminRegistrationSerializer(serializers.ModelSerializer):
    """Only used by Admins to create student accounts."""
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class GlobalXPConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalXPConfig
        fields = '__all__'
