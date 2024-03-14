from rest_framework import permissions
from apps.medical.models import Doctor, Family
class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.role=='doctor':
            return True
        if Doctor.objects.filter(user=request.user).exists():
            return True
        return False
    
class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return Family.objects.filter(creator = request.user).exists()
    