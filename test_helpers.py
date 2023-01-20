import math
import unittest
import helpers
from datetime import date


class TestDetermineAge(unittest.TestCase):

    def test_determine_age_valid(self):
        age = helpers.determine_age(date(2022, 1, 1), date(1999, 1, 1))
        self.assertEqual(age, 23.0)

    def test_determine_age_valid_2(self):
        age = helpers.determine_age(date(2022, 12, 1), date(2000, 1, 1))
        self.assertEqual(age, 22.9)

    def test_determine_age_invalid(self):
        with self.assertRaises(ValueError) as context:
            helpers.determine_age(date(1999, 1, 1), date(2000, 1, 1))
        self.assertEqual("The date has to be larger than the birthdate", str(context.exception))

    def test_determine_age_invalid_2(self):
        with self.assertRaises(ValueError) as context:
            helpers.determine_age(date(1999, 1, 1), date(2022, 1, 1))
        self.assertEqual("The date has to be larger than the birthdate", str(context.exception))


class TestDetermineDisinvestment(unittest.TestCase):

    def test_determine_disinvestment_high_income(self):
        cash_inflow = 10000
        living_expenses = 3600
        tax_rate = 0.1
        expected_disinvestment = 0
        calculated_disinvestment = helpers.determine_disinvestment(cash_inflow, living_expenses, tax_rate)
        self.assertEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_low_income(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = 0.1
        expected_disinvestment = 1111.1111111111
        calculated_disinvestment = helpers.determine_disinvestment(cash_inflow, living_expenses, tax_rate)
        self.assertAlmostEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_invalid_tax_rate_too_high(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = 1.0
        self.assertRaises(ValueError, helpers.determine_disinvestment, cash_inflow, living_expenses, tax_rate)

    def test_determine_disinvestment_invalid_tax_rate_too_low(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = -0.3
        self.assertRaises(ValueError, helpers.determine_disinvestment, cash_inflow, living_expenses, tax_rate)

    def test_determine_disinvestment_medium_living_expenses_with_linear_buffer(self):
        cash_inflow = 3000
        living_expenses = 5000
        tax_rate = 0.1
        expected_disinvestment = 2222.222222222222
        calculated_disinvestment = helpers.determine_disinvestment(cash_inflow, living_expenses, tax_rate,
                                                                   safety_buffer=True, months_to_simulate=20,
                                                                   pf_value=200000)
        self.assertAlmostEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_high_living_expenses_with_linear_buffer(self):
        cash_inflow = 3000
        living_expenses = 9999999
        tax_rate = 0.1
        expected_disinvestment = 10000
        calculated_disinvestment = helpers.determine_disinvestment(cash_inflow, living_expenses, tax_rate,
                                                                   safety_buffer=True, months_to_simulate=20,
                                                                   pf_value=200000)
        self.assertAlmostEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_high_income_with_linear_buffer(self):
        cash_inflow = 8000
        living_expenses = 1000
        tax_rate = 0.1
        expected_disinvestment = 0
        calculated_disinvestment = helpers.determine_disinvestment(cash_inflow, living_expenses, tax_rate,
                                                                   safety_buffer=True, months_to_simulate=20,
                                                                   pf_value=200000)
        self.assertAlmostEqual(expected_disinvestment, calculated_disinvestment)


class TestDetermineInvestment(unittest.TestCase):

    def test_determine_investment_high_income(self):
        cash_inflow = 10000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 4000
        calculated_investment = helpers.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_high_income_and_no_cap(self):
        cash_inflow = 10000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 6400
        calculated_investment = helpers.determine_investment(cash_inflow, living_expenses, target_investment_amount,
                                                             investment_cap=False)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_low_income(self):
        cash_inflow = 5000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 1400
        calculated_investment = helpers.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_no_income(self):
        cash_inflow = 0
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 0
        calculated_investment = helpers.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_negative_income(self):
        cash_inflow = -5000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 0
        calculated_investment = helpers.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)


class TestDetermineLivingExpenses(unittest.TestCase):

    def test_living_expenses_in_the_future_valid_input(self):
        date_of_origin = date(2020, 3, 23)
        living_expenses = 3600
        future_date = date(2030, 3, 23)
        inflation = 0.02
        expected_future_living_expenses = 4388.38
        calculated_future_living_expenses = helpers.determine_living_expenses(date_of_origin, living_expenses,
                                                                              future_date, inflation)
        lower_tolerance = expected_future_living_expenses * 0.999
        upper_tolerance = expected_future_living_expenses * 1.001
        self.assertGreaterEqual(calculated_future_living_expenses, lower_tolerance)
        self.assertLessEqual(calculated_future_living_expenses, upper_tolerance)

    def test_living_expenses_in_the_future_date_in_the_past(self):
        date_of_origin = date(2020, 3, 23)
        living_expenses = 3600
        future_date = date(2010, 3, 23)
        inflation = 0.02
        self.assertRaises(ValueError, helpers.determine_living_expenses, date_of_origin, living_expenses, future_date,
                          inflation)


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
        positive_numbers = [3, 4, math.nan, 8]
        self.assertRaises(ValueError, helpers.validate_positive_numbers, positive_numbers)

    def test_validate_positive_numbers_with_invalid_input_3(self):
        positive_numbers = []
        with self.assertRaises(ValueError) as context:
            helpers.validate_positive_numbers(positive_numbers)
        self.assertEqual("The given list to validate has to contain entries. It is currently an empty list.",
                         str(context.exception))


class TestValidateTaxRate(unittest.TestCase):

    def test_validate_tax_rate_valid(self):
        helpers.validate_tax_rate(0.1)
        helpers.validate_tax_rate(0.0)

    def test_validate_tax_rate_invalid(self):
        with self.assertRaises(ValueError):
            helpers.validate_tax_rate(1.0)
        with self.assertRaises(ValueError):
            helpers.validate_tax_rate(-0.1)


if __name__ == '__main__':
    unittest.main()
