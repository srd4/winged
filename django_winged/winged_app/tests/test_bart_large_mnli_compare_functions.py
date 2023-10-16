from django.test import TestCase
from unittest.mock import Mock, patch
from scripts.bart_large_mnli_compare import compute_zero_shot_comparison, HuggingFaceZeroShotAPITimeoutError, HuggingFaceZeroShotAPIError

from django.contrib.auth.models import User
from winged_app.models import Item, CriteriaStatementVersion, Criteria


class TestComputeZeroShotComparison(TestCase):
    def setUp(self):
        self.first_user = User.objects.create_user('first_user', 'first_user@example.com', 'testpass')
        self.item = Item.objects.create(statement="Test statement", user=self.first_user)
        self.item_current_statement_version = self.item.current_statement_version
        self.criteria_1 = Criteria.objects.create(statement="Criteria 1", user=self.first_user)
        self.criteria_2 = Criteria.objects.create(statement="Criteria 2", user=self.first_user)
        self.mock_response = Mock()
        self.mock_response.json.return_value = {"labels": [self.criteria_1.current_criteria_statement_version.computed_statement, self.criteria_2.current_criteria_statement_version.computed_statement]}

    @patch('scripts.bart_large_mnli_compare.api_call')
    def test_successful_api_call(self, mock_api_call):
        mock_response2 = Mock()
        mock_response2.json.return_value = {"labels": [self.criteria_2.current_criteria_statement_version.computed_statement, self.criteria_1.current_criteria_statement_version.computed_statement]}

        # Response for function on first and second call.
        mock_api_call.side_effect = [self.mock_response, mock_response2]

        # Patch sleep so tests don't wait.
        with patch('time.sleep', return_value=None):
            # First api_call fucntion call
            result = compute_zero_shot_comparison(
                self.item_current_statement_version.statement,
                self.criteria_1.current_criteria_statement_version.computed_statement,
                self.criteria_2.current_criteria_statement_version.computed_statement,
                post_function=mock_api_call
                )
            # Assert parser returns True
            self.assertTrue(result[1])

            # Second api_call fucntion call
            result = compute_zero_shot_comparison(
                self.item_current_statement_version.statement,
                self.criteria_1.current_criteria_statement_version.computed_statement,
                self.criteria_2.current_criteria_statement_version.computed_statement,
                post_function=mock_api_call
                )
            # Assert parser returns False
            self.assertFalse(result[1])


    @patch('scripts.bart_large_mnli_compare.api_call')
    @patch('scripts.bart_large_mnli_compare.parse_response')
    def test_api_timeout_retry(self, mock_api_call, mock_parser):
        mock_api_call.side_effect = [HuggingFaceZeroShotAPITimeoutError] * 2 + [self.mock_response]
        mock_parser.return_value = (self.mock_response.json(), True)

        with patch('time.sleep', return_value=None):
            result = compute_zero_shot_comparison(
                self.item_current_statement_version.statement,
                self.criteria_1.current_criteria_statement_version.computed_statement,
                self.criteria_2.current_criteria_statement_version.computed_statement,
                post_function=mock_api_call,
                parser_function=mock_parser
                )
            self.assertTrue(result[1])

    @patch('scripts.bart_large_mnli_compare.api_call')
    @patch('scripts.bart_large_mnli_compare.parse_response')
    def test_api_error_retry(self, mock_api_call, mock_parser):
        mock_api_call.side_effect = [HuggingFaceZeroShotAPIError, self.mock_response]
        mock_parser.return_value = (self.mock_response.json(), True)

        with patch('time.sleep', return_value=None):
            result = compute_zero_shot_comparison(
                self.item_current_statement_version.statement,
                self.criteria_1.current_criteria_statement_version.computed_statement,
                self.criteria_2.current_criteria_statement_version.computed_statement,
                post_function=mock_api_call,
                parser_function=mock_parser
                )
            self.assertTrue(result[1])

    @patch('scripts.bart_large_mnli_compare.api_call', side_effect=HuggingFaceZeroShotAPIError)
    def test_max_retries_reached(self, mock_api_call):
        
        with self.assertRaises(HuggingFaceZeroShotAPIError):
            with patch('time.sleep', return_value=None):
                compute_zero_shot_comparison(
                    self.item_current_statement_version.statement,
                    self.criteria_1.current_criteria_statement_version.computed_statement,
                    self.criteria_2.current_criteria_statement_version.computed_statement,
                    post_function=mock_api_call                
                )
