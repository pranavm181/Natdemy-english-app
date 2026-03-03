from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core_api.views import (
    StudentViewSet, get_auto_lesson, get_learning_session, 
    get_reading_story, get_writing_task, get_recent_calls, 
    save_call_recording, get_call_history
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
    path('get-listening/', get_auto_lesson),
    path('get-learning/', get_learning_session),
    path('get-reading/', get_reading_story),
    path('get-writing/', get_writing_task),
    path('speaking/recent/', get_recent_calls, name='recent_calls'),
    path('speaking/history/', get_call_history, name='call_history'),
    path('speaking/save/', save_call_recording, name='save_recording'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)