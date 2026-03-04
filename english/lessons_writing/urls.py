from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WritingViewSet

router = DefaultRouter()
router.register(r'', WritingViewSet, basename='writing')

urlpatterns = [
    path('', include(router.urls)),
]
