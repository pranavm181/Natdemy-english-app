from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Chapter, GrammarExample, GrammarQuiz
from .serializers import ChapterSerializer, GrammarExampleSerializer, GrammarQuizSerializer

try:
    from core_api.permissions import IsApprovedStudent, IsSuperUser
except ImportError:
    from rest_framework.permissions import IsApprovedStudent
    from rest_framework.permissions import IsAdminUser as IsSuperUser

class LearningMixin:
    @action(detail=False, methods=['get'])
    def current_learning(self, request):
        """Learning: Gets current Chapter with Primary and Backup examples."""
        profile = request.user.profile
        try:
            chapter = Chapter.objects.get(order=profile.unlocked_chapter)
        except Chapter.DoesNotExist:
            return Response({"message": "You have completed all available chapters!"}, status=status.HTTP_404_NOT_FOUND)
        
        examples = chapter.examples.filter(is_backup=False)[:5]
        backups = chapter.examples.filter(is_backup=True)[:5]
        quiz = chapter.quizzes.all()[:3]
        
        return Response({
            "chapter_title": chapter.title,
            "grammar_logic": getattr(chapter, 'grammar_rule_malayalam', ""),
            "primary_examples": [{"en": e.english_text, "ml": e.malayalam_explanation} for e in examples],
            "backup_examples": [{"en": b.english_text, "ml": b.malayalam_explanation} for b in backups],
            "quiz": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "options": [q.option_a, q.option_b, q.option_c, q.option_d],
                    "correct": q.correct_option
                } for q in quiz
            ]
        })

from rest_framework.pagination import PageNumberPagination

class ChapterViewSet(viewsets.ModelViewSet, LearningMixin):
    queryset = Chapter.objects.all().order_by('order')
    serializer_class = ChapterSerializer
    pagination_class = PageNumberPagination
    search_fields = ['title', 'grammar_rule_malayalam']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'current_learning']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]

class GrammarExampleViewSet(viewsets.ModelViewSet):
    queryset = GrammarExample.objects.all()
    serializer_class = GrammarExampleSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]

class GrammarQuizViewSet(viewsets.ModelViewSet):
    queryset = GrammarQuiz.objects.all()
    serializer_class = GrammarQuizSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsApprovedStudent()]
        return [IsSuperUser()]
