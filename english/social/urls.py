from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SocialViewSet, CallLogViewSet

router = DefaultRouter()
router.register(r'requests', SocialViewSet, basename='social')
router.register(r'calls', CallLogViewSet, basename='calls')

urlpatterns = [
    path('', include(router.urls)),
    
    # Custom actions (some remain for student dashboard compatibility if needed, 
    # but CallLogViewSet now handles the primary speaking logic via router)
    path('list-friends/', SocialViewSet.as_view({'get': 'list_friends'}), name='list_friends'),
    path('send-request/', SocialViewSet.as_view({'post': 'send_request'}), name='send_request'),
    path('respond-request/<int:pk>/', SocialViewSet.as_view({'post': 'respond_request'}), name='respond_request'),
    path('toggle-status/', SocialViewSet.as_view({'post': 'toggle_status'}), name='toggle_status'),
    
    # Re-routing speaking actions to the new ViewSet if wanted, but keeping old paths for compatibility
    path('speaking/recent/', CallLogViewSet.as_view({'get': 'speaking_recent'}), name='speaking_recent'),
    path('speaking/history/', CallLogViewSet.as_view({'get': 'speaking_history'}), name='speaking_history'),
    path('speaking/save/', CallLogViewSet.as_view({'post': 'speaking_save'}), name='speaking_save'),
]
