from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            settings.STATIC_URL,
            '/admin/login/',
        ]

        if not request.user.is_authenticated:
            if not any(request.path.startswith(url) for url in exempt_urls):
                return redirect('login')

        return self.get_response(request)
