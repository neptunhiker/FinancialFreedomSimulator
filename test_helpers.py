import unittest
import helpers


class TestValidatePositiveNumbers(unittest.TestCase):

    def test_validate_positive_numbers_with_valid_input(self):
        positive_numbers = [1, 2, 3.5]
        helpers.validate_positive_numbers(positive_numbers)

    def test_validate_positive_numbers_with_valid_input_2(self):
        positive_numbers = [5, 7.5, 3]
        helpers.validate_positive_numbers(positive_numbers)

    def test_validate_positive_numbers_with_invalid_input(self):
        positive_numbers = [-3, 0, -1.5]
        with self.assertRaises(ValueError) as context:
            helpers.validate_positive_numbers(positive_numbers)
        self.assertEqual("The given argument must be a positive number.", str(context.exception))

    def test_validate_positive_numbers_with_invalid_input_2(self):
        positive_numbers = []
        with self.assertRaises(ValueError) as context:
            helpers.validate_positive_numbers(positive_numbers)
        self.assertEqual("The given list to validate has to contain entries. It is currently an empty list.",
                         str(context.exception))


if __name__ == '__main__':
    unittest.main()
