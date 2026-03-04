from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Core Admin & Auth
    path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 2. Included App URLs
    path('api/', include('core_api.urls')),
    path('api/listening/', include('lessons_listening.urls')),
    path('api/reading/', include('lessons_reading.urls')),
    path('api/writing/', include('lessons_writing.urls')),
    path('api/learning/', include('lessons_learning.urls')),
    path('api/social/', include('social.urls')),
    path('api/', include('social.urls')), # For legacy speaking/ endpoints
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)