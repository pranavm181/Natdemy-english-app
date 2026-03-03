from rest_framework import permissions

class IsApprovedStudent(permissions.BasePermission):
    """
    Custom permission to only allow students approved by the admin 
    to access the Antigravity app data.
    """
    
    def has_permission(self, request, view):
        # Step 1: Check if the user is even logged in
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Step 2: Check if the user has a profile and if that profile is approved
        # This prevents the app from crashing if a user exists without a profile
        try:
            return request.user.profile.is_approved
        except AttributeError:
            # If the user has no profile, they are definitely not approved
            return False

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user