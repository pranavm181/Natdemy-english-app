from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import FriendRequest, CallLog
from .serializers import FriendRequestSerializer, CallLogSerializer

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

class SpeakingMixin:
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
