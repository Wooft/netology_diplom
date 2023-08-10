from rest_framework.permissions import BasePermission


class BasketOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.order.user