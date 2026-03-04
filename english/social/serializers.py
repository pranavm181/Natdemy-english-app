from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CallLog, FriendRequest

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

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
