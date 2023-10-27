import unittest
from unittest.mock import patch
from django.test import TestCase
from requests.exceptions import RequestException

from scripts.bart_large_mnli_compare import api_call, HuggingFaceZeroShotAPIError

class TestLogging(TestCase):
    @patch('scripts.bart_large_mnli_compare.logger')
    def test_api_call_logs_info(self, mock_logger):

        with patch('scripts.bart_large_mnli_compare.requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200 
            mock_response.text = 'OK'

            api_call('url', 'headers', 'data')

            mock_post.assert_called_with('url', headers='headers', json='data', timeout=10)

        mock_logger.info.assert_called_with("API response: 200, OK")


    @patch('scripts.bart_large_mnli_compare.logger')
    def test_api_call_logs_error(self, mock_logger):
        with patch('scripts.bart_large_mnli_compare.requests.post') as mock_post:
            mock_post.side_effect = RequestException("Some error")

            with self.assertRaises(HuggingFaceZeroShotAPIError):
                api_call('url', 'headers', 'data')
        
            mock_post.assert_called_with('url', headers='headers', json='data', timeout=10)

        mock_logger.error.assert_called_with(f"Request exception: Some error")

if __name__ == '__main__':
    unittest.main()
