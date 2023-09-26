import unittest
from unittest.mock import Mock, patch
from scripts.bart_large_mnli_compare import compute_zero_shot_comparison, HuggingFaceZeroShotAPITimeoutError, HuggingFaceZeroShotAPIError

class TestComputeZeroShotComparison(unittest.TestCase):
    def setUp(self):
        self.item_statement = "Test item"
        self.criteria_1 = "Criteria 1"
        self.criteria_2 = "Criteria 2"
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"labels": [self.criteria_1, self.criteria_2]}

    @patch('scripts.bart_large_mnli_compare.api_call')
    @patch('scripts.bart_large_mnli_compare.parse_response')
    def test_successful_api_call(self, mock_parser, mock_api_call):
        mock_api_call.return_value = self.mock_response
        mock_parser.return_value = (self.mock_response.json(), True)
        result = compute_zero_shot_comparison(
            self.item_statement, self.criteria_1, self.criteria_2,
            post_function=mock_api_call, parser_function=mock_parser
            )
        self.assertTrue(result[1])

    @patch('scripts.bart_large_mnli_compare.api_call')
    @patch('scripts.bart_large_mnli_compare.parse_response')
    def test_api_timeout_retry(self, mock_api_call, mock_parser):
        mock_api_call.side_effect = [HuggingFaceZeroShotAPITimeoutError] * 4 + [self.mock_response]
        mock_parser.return_value = (self.mock_response.json(), True)
        result = compute_zero_shot_comparison(
            self.item_statement, self.criteria_1, self.criteria_2,
            post_function=mock_api_call, parser_function=mock_parser
            )
        self.assertTrue(result[1])

    @patch('scripts.bart_large_mnli_compare.api_call')
    @patch('scripts.bart_large_mnli_compare.parse_response')
    def test_api_error_retry(self, mock_api_call, mock_parser):
        mock_api_call.side_effect = [HuggingFaceZeroShotAPIError, self.mock_response]
        mock_parser.return_value = (self.mock_response.json(), True)
        result = compute_zero_shot_comparison(
            self.item_statement, self.criteria_1, self.criteria_2,
            post_function=mock_api_call, parser_function=mock_parser
            )
        self.assertTrue(result[1])

    @patch('scripts.bart_large_mnli_compare.api_call', side_effect=HuggingFaceZeroShotAPIError)
    def test_max_retries_reached(self, mock_api_call):
        with self.assertRaises(HuggingFaceZeroShotAPIError):
            compute_zero_shot_comparison(
                self.item_statement, self.criteria_1, self.criteria_2,
                post_function=mock_api_call
                )

if __name__ == '__main__':
    unittest.main()
