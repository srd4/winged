from django.urls import reverse, resolve
from django.test import SimpleTestCase
from ..views import RunScriptAPIView

class URLPatternTest(SimpleTestCase):

    def test_url_resolves(self):
        # Test that the URL resolves to the correct view
        url = '/containers/1/criterion-vs-items-sort/criterion/2/user_input/'
        resolver = resolve(url)
        container_id = resolver.kwargs['container_id']
        spectrumtype_id = resolver.kwargs['criterion_id']
        comparison_mode = resolver.kwargs['ai_model']

        self.assertEqual(resolver.func.view_class, RunScriptAPIView)
        self.assertEqual(container_id, 1)
        self.assertEqual(spectrumtype_id, 2)
        self.assertEqual(comparison_mode, "user_input")

        # Test that reverse() returns the expected URL
        url_name = 'criterion-vs-items-sort'  # Update with the actual URL name
        url = reverse(url_name, args=[1, 2, "user_input"])
        self.assertEqual(url, '/containers/1/criterion-vs-items-sort/criterion/2/user_input/')