from django.urls import reverse, resolve
from django.test import SimpleTestCase
from ..views import RunScriptAPIView

class URLPatternTest(SimpleTestCase):

    def test_url_resolves(self):
        # Test that the URL resolves to the correct view
        url = '/containers/1/run-script/spectrumtypes/2/openai/'
        resolver = resolve(url)
        container_id = resolver.kwargs['container_id']
        spectrumtype_id = resolver.kwargs['spectrumtype_id']
        comparison_mode = resolver.kwargs['comparison_mode']

        self.assertEqual(resolver.func.view_class, RunScriptAPIView)
        self.assertEqual(container_id, 1)
        self.assertEqual(spectrumtype_id, 2)
        self.assertEqual(comparison_mode, "openai")

    def test_url_reverse(self):
        # Test that reverse() returns the expected URL
        url_name = 'run-script'  # Update with the actual URL name
        url = reverse(url_name, args=[1, 2, "user_input"])
        self.assertEqual(url, '/containers/1/run-script/spectrumtypes/2/user_input/')