from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializers import AdminRegistrationSerializer

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def dashboard_view(request):
    """
    Native Django view to serve the Admin Dashboard SPA.
    """
    return render(request, 'core_api/dashboard.html')


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_register_student(request):
    """
    CRITICAL: Admin-only endpoint to create student accounts.
    """
    serializer = AdminRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Auto-approve students created by admin
        profile = user.profile
        profile.is_approved = True
        profile.save()
        
        return Response({
            "message": "Student account created by admin successfully.",
            "username": user.username,
            "student_id": profile.student_id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
