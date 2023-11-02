from django.test import TestCase
from scripts.my_custom_helper_functions import it_is_best_to_merge_and_then_sort

class InsertVsMergeAlgorithmChoiceTest(TestCase):
    def test_algorithm_choice_for_large_k_small_n(self):
        k, n = 100, 0
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 1000, 100
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))
        
    def test_algorithm_choice_for_large_k_medium_n(self):
        k, n = 100, 40
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 1000, 500
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_large_k_large_n(self):
        k, n = 100, 80
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 1000, 1000
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_medium_k_small_n(self):
        k, n = 50, 0
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 400, 100
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_medium_k_medium_n(self):
        k, n = 50, 45
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 450, 500
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_medium_k_large_n(self):
        # merge = 140*log(140) =~ 1000
        # insert = 40*100 = 4000
        k, n = 40, 100
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

        #merge ~16000
        #insert ~500000
        k, n = 500, 1000
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_small_k_small_n(self):
        k, n = 0, 20
        self.assertFalse(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 5, 25
        self.assertFalse(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_small_k_medium_n(self):
        k, n = 1, 50
        self.assertFalse(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 35, 100
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))

    def test_algorithm_choice_for_small_k_large_n(self):
        k, n = 1, 1000
        self.assertFalse(it_is_best_to_merge_and_then_sort(k, n))

        k, n = 200, 10000
        self.assertTrue(it_is_best_to_merge_and_then_sort(k, n))