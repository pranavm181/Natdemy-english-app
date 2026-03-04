from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChapterViewSet, GrammarExampleViewSet, GrammarQuizViewSet

router = DefaultRouter()
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'examples', GrammarExampleViewSet, basename='example')
router.register(r'quizzes', GrammarQuizViewSet, basename='quiz')

urlpatterns = [
    path('', include(router.urls)),
]
