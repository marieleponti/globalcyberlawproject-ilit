from django.conf import settings
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse


class LoginRequiredMiddleware:
    """Gate the whole site behind login.

    Enabled via the REQUIRE_LOGIN environment variable (see settings.py), so the
    site can be made public on launch day without a code change or redeploy of a
    different image.

    Health checks and the ACME challenge path stay open: the container probe and
    Certbot are unauthenticated by nature.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = self._build_exempt_urls()

    @staticmethod
    def _build_exempt_urls():
        exempt = [
            settings.STATIC_URL,
            '/healthz',
            '/readyz',
            '/.well-known/',
        ]
        for name in ('login', 'logout'):
            try:
                exempt.append(reverse(name))
            except NoReverseMatch:
                pass
        try:
            exempt.append(reverse('admin:login'))
        except NoReverseMatch:
            exempt.append('/admin/login/')
        return tuple(url for url in exempt if url)

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not request.path.startswith(self.exempt_urls):
                return redirect('login')

        return self.get_response(request)
