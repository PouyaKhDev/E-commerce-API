from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffOrReadOnly(BasePermission):
    """
    Staff: full access
    Others: read-only
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrStaff(BasePermission):
    """
    Object-level permission.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        # Order or Cart: both have 'user'
        user_field = getattr(obj, "user", None)
        return user_field == request.user
