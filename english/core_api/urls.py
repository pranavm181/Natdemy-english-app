from django.urls import path
from . import views, views_admin

urlpatterns = [
    path('admin/register-student/', views_admin.admin_register_student, name='admin_register_student'),
    path('students/', views.StudentViewSet.as_view({'get': 'list'})),
    path('students/<int:pk>/', views.StudentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('students/<int:pk>/student_report/', views.StudentViewSet.as_view({'get': 'student_report'})),
    path('students/dashboard/', views.StudentViewSet.as_view({'get': 'detailed_dashboard'})),
    path('students/detailed_dashboard/', views.StudentViewSet.as_view({'get': 'detailed_dashboard'})),
    
    # Admin Dashboard (Template Driven)
    path('admin-dashboard/', views_admin.dashboard_view, name='admin-dashboard'),
    path('students/admin_stats/', views.StudentViewSet.as_view({'get': 'admin_stats'})),
    path('students/bulk-import/', views.StudentViewSet.as_view({'post': 'bulk_import'})),
    path('students/reports/', views.StudentViewSet.as_view({'get': 'section_reports'})),
    path('students/log-activity/', views.StudentViewSet.as_view({'post': 'log_activity'})),
    path('students/update-photo/', views.StudentViewSet.as_view({'post': 'update_photo'})),
    path('students/analytics/weekly/', views.StudentViewSet.as_view({'get': 'weekly_analytics'})),
    path('students/wellbeing/', views.StudentViewSet.as_view({'get': 'digital_wellbeing'})),
]
