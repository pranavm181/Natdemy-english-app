import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import WritingTask
from .serializers import WritingTaskSerializer

try:
    from core_api.permissions import IsApprovedStudent, IsSuperUser
except ImportError:
    from rest_framework.permissions import IsApprovedStudent
    from rest_framework.permissions import IsAdminUser as IsSuperUser

class WritingMixin:
    @action(detail=False, methods=['get'])
    def current_writing(self, request):
        """Writing: Scrambled sentences for drag-and-drop."""
        profile = request.user.profile
        tasks = WritingTask.objects.filter(level=profile.current_level)
        
        if not tasks.exists():
            return Response({"message": "No writing tasks available."}, status=status.HTTP_404_NOT_FOUND)
            
        task = random.choice(tasks)
        return Response({
            "id": task.id,
            "malayalam_hint": task.malayalam_meaning,
            "correct_sentence": task.correct_sentence,
            "extra_words": task.extra_words,
        })

from rest_framework.pagination import PageNumberPagination

class WritingViewSet(viewsets.ModelViewSet, WritingMixin):
    queryset = WritingTask.objects.all()
    serializer_class = WritingTaskSerializer
    pagination_class = PageNumberPagination
    search_fields = ['malayalam_meaning', 'correct_sentence', 'level']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'current_writing']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]
