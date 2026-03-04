import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ReadingStory
from .serializers import ReadingStorySerializer

try:
    from core_api.permissions import IsApprovedStudent, IsSuperUser
except ImportError:
    from rest_framework.permissions import IsApprovedStudent
    from rest_framework.permissions import IsAdminUser as IsSuperUser

class ReadingMixin:
    @action(detail=False, methods=['get'])
    def current_reading(self, request):
        """Reading: Story with background and point-reduction logic."""
        profile = request.user.profile
        stories = ReadingStory.objects.filter(level=profile.current_level)
        
        if not stories.exists():
            return Response({"message": "No stories available."}, status=status.HTTP_404_NOT_FOUND)
            
        story = random.choice(stories)
        questions = story.questions.all()
        
        return Response({
            "id": story.id,
            "title": story.title,
            "content": story.story_content,
            "background": story.background_image_url,
            "quiz": [
                {
                    "text": q.text,
                    "options": [q.option_1, q.option_2, q.option_3],
                    "correct": q.correct
                } for q in questions
            ]
        })

from rest_framework.pagination import PageNumberPagination

class ReadingViewSet(viewsets.ModelViewSet, ReadingMixin):
    queryset = ReadingStory.objects.all()
    serializer_class = ReadingStorySerializer
    pagination_class = PageNumberPagination
    search_fields = ['title', 'level', 'story_content']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'current_reading']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]
