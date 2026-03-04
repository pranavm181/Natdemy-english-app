from rest_framework import permissions

class IsApprovedStudent(permissions.BasePermission):
    """
    Custom permission to only allow students approved by the admin 
    OR superusers to access the Antigravity app data.
    """
    
    def has_permission(self, request, view):
        # Step 1: Check if the user is even logged in
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Step 2: Admins (superusers) always have permission
        if request.user.is_superuser:
            return True

        # Step 3: Check if the student has an approved profile
        try:
            return request.user.profile.is_approved
        except AttributeError:
            # If the user has no profile, they are definitely not approved
            return False

    def has_object_permission(self, request, view, obj):
        # Superusers can access any object
        if request.user.is_superuser:
            return True
        # Students can only access their own objects (where applicable)
        return hasattr(obj, 'user') and obj.user == request.user

class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers to perform management tasks.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)