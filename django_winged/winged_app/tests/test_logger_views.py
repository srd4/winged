from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from winged_app.models import Container, SpectrumType

class RunScriptAPIViewTest(TestCase):
    def setUp(self):
        # Create a test user and set up the client for authentication
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test Container and SpectrumType objects
        self.container = Container.objects.create(name="first_user_container", user=self.user)
        self.spectrumtype = SpectrumType.objects.create(name="Test SpectrumType", description="Test Description", user=self.user)

    @patch('winged_app.views.logger')  # Replace with your actual import
    def test_run_script_api_view(self, mock_logger):
        with patch('winged_app.views.threading.Thread') as mock_thread:
            response = self.client.get(f"/containers/{self.container.pk}/run-script/spectrumtypes/{self.spectrumtype.pk}/some_mode/")

            sentences_to_log = [
                f"container: {self.container}",
                f"spectrumtype: {self.spectrumtype}",
                f"actionables{self.container.is_on_actionables_tab}",
                f"done: {self.container.is_on_done_tab}",
            ]

            # Verify logging
            mock_logger.info.assert_called_with("\n".join(sentence for sentence in sentences_to_log))

            self.assertEqual(response.status_code, 202)