from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import FriendRequest, CallLog, SpeakingTopic, ActiveCall
from .serializers import FriendRequestSerializer, CallLogSerializer, SpeakingTopicSerializer, ActiveCallSerializer
import random

class SocialViewSet(viewsets.ReadOnlyModelViewSet):
    """Handles Friend Requests, Online Status, and DND Toggle."""
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        from django.db.models import Q
        return FriendRequest.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        )

    @action(detail=False, methods=['post'])
    def send_request(self, request):
        to_username = request.data.get('username')
        try:
            to_user = User.objects.get(username=to_username)
            if to_user == request.user:
                return Response({"error": "You cannot add yourself."}, status=400)
            
            FriendRequest.objects.create(from_user=request.user, to_user=to_user)
            return Response({"message": f"Request sent to {to_username}!"})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        except Exception:
            return Response({"error": "Request already exists or failed."}, status=400)

    @action(detail=True, methods=['post'])
    def respond_request(self, request, pk=None):
        req = self.get_object()
        action_type = request.data.get('action') # 'ACCEPT' or 'REJECT'

        if req.to_user != request.user:
            return Response({"error": "Unauthorized."}, status=403)

        if action_type == 'ACCEPT':
            req.status = 'ACCEPTED'
            req.from_user.profile.friends.add(req.to_user)
            req.to_user.profile.friends.add(req.from_user)
            req.save()
            return Response({"message": "Friend request accepted!"})
        elif action_type == 'REJECT':
            req.status = 'REJECTED'
            req.save()
            return Response({"message": "Friend request rejected."})
        
        return Response({"error": "Invalid action."}, status=400)
    
    @action(detail=False, methods=['post'])
    def remove_friend(self, request):
        """Removes a friend and cleans up the friendship bi-directionally."""
        from django.db.models import Q
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required."}, status=400)

        try:
            target_user = User.objects.get(username=username)
            profile = request.user.profile
            target_profile = target_user.profile

            # Check if they are actually friends
            if not profile.friends.filter(id=target_user.id).exists():
                return Response({"error": "This user is not in your friend list."}, status=400)

            # Bi-directional removal from ManyToMany
            profile.friends.remove(target_user)
            target_profile.friends.remove(request.user)

            # Clean up accepted requests
            FriendRequest.objects.filter(
                Q(from_user=request.user, to_user=target_user) |
                Q(from_user=target_user, to_user=request.user),
                status='ACCEPTED'
            ).delete()

            return Response({"message": f"Successfully removed {username} from friends."})

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def toggle_status(self, request):
        """Toggle Online or DND status."""
        profile = request.user.profile
        status_type = str(request.data.get('type', '')).upper() # Handle case-insensitive
        
        if status_type == 'ONLINE':
            profile.is_online = not profile.is_online
        elif status_type == 'DND':
            profile.is_dnd = not profile.is_dnd
        else:
            return Response({"error": "Invalid type. Use ONLINE or DND."}, status=400)
        
        profile.save()
        return Response({
            "is_online": profile.is_online,
            "is_dnd": profile.is_dnd
        })

    @action(detail=False, methods=['get'])
    def list_friends(self, request):
        """Lists friends with their online/DND status."""
        friends = request.user.profile.friends.all()
        data = []
        for f in friends:
            f_profile = f.profile
            data.append({
                "username": f.username,
                "is_online": f_profile.is_online,
                "is_dnd": f_profile.is_dnd,
                "can_call": f_profile.is_online and not f_profile.is_dnd,
                "photo": request.build_absolute_uri(f_profile.profile_photo.url) if f_profile.profile_photo else None
            })
        return Response(data)


class SpeakingTopicViewSet(viewsets.ModelViewSet):
    """Admin-only CRUD for speaking topics."""
    queryset = SpeakingTopic.objects.all()
    serializer_class = SpeakingTopicSerializer
    permission_classes = [permissions.IsAdminUser]

class SpeakingMixin:
    @action(detail=False, methods=['get'])
    def random_topic(self, request):
        """Fetches a random topic, ideally matching student level."""
        level = 'BEGINNER'
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            level = profile.get_section_level(profile.speaking_xp)
        
        topics = SpeakingTopic.objects.filter(level=level)
        if not topics.exists():
            topics = SpeakingTopic.objects.all()
        
        if topics.exists():
            topic = random.choice(topics)
            return Response(SpeakingTopicSerializer(topic).data)
        return Response({"error": "No topics found"}, status=404)

    @action(detail=False, methods=['post'])
    def initiate_call(self, request):
        """Creates an active call session with a specific topic."""
        receiver_name = request.data.get('receiver_name')
        topic_id = request.data.get('topic_id')

        try:
            receiver = User.objects.get(username=receiver_name)
            topic = SpeakingTopic.objects.get(id=topic_id)
            
            # Deactivate any existing calls for either user
            ActiveCall.objects.filter(caller=request.user, is_active=True).update(is_active=False)
            ActiveCall.objects.filter(receiver=request.user, is_active=True).update(is_active=False)
            ActiveCall.objects.filter(caller=receiver, is_active=True).update(is_active=False)
            ActiveCall.objects.filter(receiver=receiver, is_active=True).update(is_active=False)

            call = ActiveCall.objects.create(
                caller=request.user,
                receiver=receiver,
                topic=topic
            )
            return Response(ActiveCallSerializer(call).data)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=['get'])
    def current_call(self, request):
        """Checks for any active call where user is caller or receiver."""
        from django.db.models import Q
        call = ActiveCall.objects.filter(
            Q(caller=request.user) | Q(receiver=request.user),
            is_active=True
        ).first()

        if call:
            return Response(ActiveCallSerializer(call).data)
        return Response({"is_active": False})

    @action(detail=False, methods=['post'])
    def end_call(self, request):
        """Ends the active call session."""
        from django.db.models import Q
        ActiveCall.objects.filter(
            Q(caller=request.user) | Q(receiver=request.user),
            is_active=True
        ).update(is_active=False)
        return Response({"message": "Call session ended."})

    @action(detail=False, methods=['get'])
    def speaking_recent(self, request):
        """Returns the 5 most recent unique contacts for quick dial."""
        recent_calls = CallLog.objects.filter(student=request.user).order_by('-timestamp')
        frequent = []
        seen = set()
        for call in recent_calls:
            if call.contact_name not in seen and len(frequent) < 5:
                frequent.append({
                    "id": call.id,
                    "name": call.contact_name,
                    "number": call.contact_number,
                    "type": call.call_type,
                    "last_called": call.timestamp,
                    "recording_url": request.build_absolute_uri(call.recording_file.url) if call.recording_file else None
                })
                seen.add(call.contact_name)
        return Response(frequent)

    @action(detail=False, methods=['get'])
    def frequent_calls(self, request):
        """Returns the top 5 most frequently called contacts (AI or Friends)."""
        from django.db.models import Count
        frequent_logs = CallLog.objects.filter(student=request.user) \
            .values('contact_name', 'call_type', 'contact_number') \
            .annotate(call_count=Count('contact_name')) \
            .order_by('-call_count')[:5]
        
        return Response(list(frequent_logs))

    @action(detail=False, methods=['get'])
    def speaking_history(self, request):
        """Returns all call history with recording playback links."""
        history = CallLog.objects.filter(student=request.user).order_by('-timestamp')
        data = []
        for call in history:
            data.append({
                "id": call.id,
                "name": call.contact_name,
                "type": call.call_type,
                "duration": call.duration_seconds,
                "timestamp": call.timestamp,
                "recording_url": request.build_absolute_uri(call.recording_file.url) if call.recording_file else None
            })
        return Response(data)

    @action(detail=False, methods=['post'])
    def speaking_save(self, request):
        """Saves a call log with duration and audio recording."""
        duration = request.data.get('duration_seconds', 0)
        contact_name = request.data.get('contact_name', 'Unknown')
        audio_file = request.FILES.get('audio')

        if not audio_file:
            return Response({"error": "Recording is required to save call log."}, status=400)

        if contact_name != "Gemini":
            friend_exists = request.user.profile.friends.filter(username=contact_name).exists()
            if not friend_exists:
                return Response({"error": "You can only call students you have added as friends."}, status=403)

        try:
            duration_int = int(duration)
        except (ValueError, TypeError):
            duration_int = 0

        CallLog.objects.create(
            student=request.user,
            contact_name=contact_name,
            duration_seconds=duration_int,
            recording_file=audio_file,
            call_type='FRIEND' if contact_name != "Gemini" else 'AI'
        )
        return Response({"message": "Call log saved successfully!"})

class CallLogViewSet(viewsets.ModelViewSet, SpeakingMixin):
    """Provides full CRUD for Call Logs."""
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CallLog.objects.filter(student=self.request.user).order_by('-timestamp')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
