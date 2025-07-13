from rest_framework import permissions

class IsEmployerOrAdmin(permissions.BasePermission):
    """
    Allow access only to employers and admins.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'EMPLOYER' or 
            request.user.role == 'ADMIN' or
            request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        # Allow employers to edit only their own job postings
        if request.user.role == 'EMPLOYER':
            return obj.posted_by == request.user
        # Admins can edit any job posting
        return request.user.role == 'ADMIN' or request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to the owner of the object or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow job seekers to view/edit only their own applications
        if hasattr(obj, 'applicant'):
            return obj.applicant == request.user or request.user.role == 'ADMIN' or request.user.is_staff
        # For job listings, allow only the poster or admin to edit
        if hasattr(obj, 'posted_by'):
            return obj.posted_by == request.user or request.user.role == 'ADMIN' or request.user.is_staff
        return False