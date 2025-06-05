from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/bookmarks/') and not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        response = self.get_response(request)
        return response
