from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CallLog, FriendRequest, SpeakingTopic, ActiveCall

class UserMinimalSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(source='profile.profile_photo', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_photo']

class SpeakingTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingTopic
        fields = '__all__'

class ActiveCallSerializer(serializers.ModelSerializer):
    caller_details = UserMinimalSerializer(source='caller', read_only=True)
    receiver_details = UserMinimalSerializer(source='receiver', read_only=True)
    topic_details = SpeakingTopicSerializer(source='topic', read_only=True)

    class Meta:
        model = ActiveCall
        fields = ['id', 'caller', 'receiver', 'topic', 'caller_details', 'receiver_details', 'topic_details', 'is_active', 'created_at']

class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = '__all__'

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user_details = UserMinimalSerializer(source='from_user', read_only=True)
    to_user_details = UserMinimalSerializer(source='to_user', read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'from_user_details', 'to_user_details', 'status', 'timestamp']
        read_only_fields = ['id', 'from_user', 'status', 'timestamp']
