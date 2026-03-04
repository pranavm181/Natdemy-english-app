import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ListeningLesson
from .serializers import ListeningLessonSerializer

try:
    from core_api.permissions import IsApprovedStudent, IsSuperUser
except ImportError:
    from rest_framework.permissions import IsAuthenticated as IsApprovedStudent
    from rest_framework.permissions import IsAdminUser as IsSuperUser

class ListeningMixin:
    @action(detail=False, methods=['get'])
    def current_listening(self, request):
        """Listening: Picks random video based on XP Level."""
        profile = request.user.profile
        user_level = profile.current_level  
        lessons = ListeningLesson.objects.filter(level=user_level)
        
        if not lessons.exists():
            return Response({"message": f"No lessons for {user_level} yet."}, status=status.HTTP_404_NOT_FOUND)
        
        lesson = random.choice(lessons)
        questions = lesson.questions.all()
        
        return Response({
            "lesson_id": lesson.id,
            "video_url": lesson.youtube_url,
            "quiz": [
                {
                    "text": q.text,
                    "options": [q.option_1, q.option_2, q.option_3],
                    "correct": q.correct
                } for q in questions
            ]
        })

from rest_framework.pagination import PageNumberPagination

class ListeningViewSet(viewsets.ModelViewSet, ListeningMixin):
    queryset = ListeningLesson.objects.all()
    serializer_class = ListeningLessonSerializer
    pagination_class = PageNumberPagination
    search_fields = ['title', 'level']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'current_listening']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]
