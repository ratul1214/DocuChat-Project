from rest_framework.permissions import IsAuthenticated

class IsAuthenticatedOrOptions(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == "OPTIONS":
            return True
        return super().has_permission(request, view)
