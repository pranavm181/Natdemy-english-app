from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListeningViewSet

router = DefaultRouter()
router.register(r'', ListeningViewSet, basename='listening')

urlpatterns = [
    path('', include(router.urls)),
]
