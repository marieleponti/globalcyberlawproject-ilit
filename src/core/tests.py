from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings

# Production uses a manifest storage that refuses {% static %} lookups until
# collectstatic has run; these tests only care about the analytics tag.
PLAIN_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=PLAIN_STORAGES)
class UmamiTagTests(TestCase):
    def render_base(self):
        request = RequestFactory().get("/")
        return render_to_string("core/base.html", request=request)

    @override_settings(UMAMI_SCRIPT_URL="", UMAMI_WEBSITE_ID="")
    def test_no_tag_when_unconfigured(self):
        self.assertNotIn("data-website-id", self.render_base())

    @override_settings(
        UMAMI_SCRIPT_URL="https://stats.example.org/script.js",
        UMAMI_WEBSITE_ID="",
    )
    def test_no_tag_without_website_id(self):
        self.assertNotIn("data-website-id", self.render_base())

    @override_settings(
        UMAMI_SCRIPT_URL="https://stats.example.org/script.js",
        UMAMI_WEBSITE_ID="abc-123",
    )
    def test_tag_rendered_when_configured(self):
        html = self.render_base()
        self.assertIn('src="https://stats.example.org/script.js"', html)
        self.assertIn('data-website-id="abc-123"', html)
