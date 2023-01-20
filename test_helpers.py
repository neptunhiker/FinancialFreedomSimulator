from datetime import date
import math
import pandas as pd
import unittest

import helpers


class TestAnalyzeSurvivalProbability(unittest.TestCase):

    def test_survival_probability(self):
        series_01 = pd.Series(data=[23, 20, 2, -5])
        series_02 = pd.Series(data=[23, 34, 2, 12])
        series_03 = pd.Series(data=[23, 34, 2, 16])
        series_04 = pd.Series(data=[23, 34, 2, 99])
        expected_result = 0.75
        calculated_result = helpers.analyze_survival_probability([series_01, series_02, series_03, series_04])
        self.assertEqual(expected_result, calculated_result)

    def test_survival_probability_empty_list(self):
        """
        Test that passing an empty list results in an error
        """
        with self.assertRaises(ValueError):
            helpers.analyze_survival_probability([])

    def test_survival_probability_all_positive(self):
        """
        Test that passing a list of all positive series results in a probability of 1
        """
        series_01 = pd.Series(data=[23, 34, 45, 56])
        series_02 = pd.Series(data=[100, 200, 300, 400])
        series_03 = pd.Series(data=[1, 2, 3, 4])
        expected_result = 1
        calculated_result = helpers.analyze_survival_probability([series_01, series_02, series_03])
        self.assertEqual(expected_result, calculated_result)


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


class TestDetermineCashNeed(unittest.TestCase):

    def test_determine_cash_need_high_income(self):
        cash_inflow = 10000
        living_expenses = 3000
        exp_cash_need = 0
        calc_cash_need = helpers.determine_cash_need(cash_inflow, living_expenses)
        self.assertEqual(exp_cash_need, calc_cash_need)

    def test_determine_cash_need_high_living_expenses(self):
        cash_inflow = 1000
        living_expenses = 3000
        exp_cash_need = 2000
        calc_cash_need = helpers.determine_cash_need(cash_inflow, living_expenses)
        self.assertEqual(exp_cash_need, calc_cash_need)

    def test_determine_cash_need_equal_income_and_expenses(self):
        cash_inflow = 1000
        living_expenses = 1000
        exp_cash_need = 0
        calc_cash_need = helpers.determine_cash_need(cash_inflow, living_expenses)
        self.assertEqual(exp_cash_need, calc_cash_need)

    def test_determine_cash_need_negative_income(self):
        cash_inflow = -100
        living_expenses = 1000
        with self.assertRaises(ValueError):
            helpers.determine_cash_need(cash_inflow, living_expenses)

    def test_determine_cash_need_negative_living_expenses(self):
        cash_inflow = 1000
        living_expenses = -100
        with self.assertRaises(ValueError):
            helpers.determine_cash_need(cash_inflow, living_expenses)


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


class TestDeterminePortfolioDeath(unittest.TestCase):

    def test_timing_of_portfolio_death(self):
        self.assertEqual(3, helpers.determine_portfolio_death(pd.Series(data=[23, 0, 2, -5])))
        self.assertEqual(0, helpers.determine_portfolio_death(pd.Series(data=[-2, 0, 2, -5])))
        self.assertEqual(1, helpers.determine_portfolio_death(pd.Series(data=[23, -3, 2, -5])))
        self.assertTrue(math.isnan(helpers.determine_portfolio_death(pd.Series(data=[23, 3, 2, 232]))))


class TestDetermineSurvival(unittest.TestCase):

    def test_survival_of_portfolio_true(self):
        series = pd.Series(data=[23, 10, 12, 45])
        self.assertTrue(helpers.determine_survival(series))

    def test_survival_of_portfolio_false(self):
        series = pd.Series(data=[23, 0, -2, 45])
        self.assertFalse(helpers.determine_survival(series))

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
