import datetime
import unittest

from dateutil.relativedelta import relativedelta
import pandas as pd

import cashflows
import simulator


class TestHelperFunctions(unittest.TestCase):

    def test_age_of_investor_regular_01(self):
        date = datetime.date(2050, 1, 29)
        birthday = datetime.date(1984, 1, 22)
        expected_age = 66.0
        calculated_age = simulator.determine_investor_age(date=date, investor_birthdate=birthday)
        self.assertEqual(expected_age, calculated_age)

    def test_age_of_investor_regular_02(self):
        date = datetime.date(2030, 9, 25)
        birthday = datetime.date(1984, 1, 22)
        expected_age = 46.7
        calculated_age = simulator.determine_investor_age(date=date, investor_birthdate=birthday)
        self.assertEqual(expected_age, calculated_age)

    def test_age_of_investor_value_error(self):
        date = datetime.date(1982, 1, 29)
        birthday = datetime.date(1984, 1, 22)
        self.assertRaises(ValueError, simulator.determine_investor_age, date=date, investor_birthdate=birthday)

    def test_determine_disinvestment_high_income(self):
        cash_inflow = 10000
        living_expenses = 3600
        tax_rate = 0.1
        expected_disinvestment = 0
        calculated_disinvestment = simulator.determine_disinvestment(cash_inflow, living_expenses, tax_rate)
        self.assertEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_low_income(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = 0.1
        expected_disinvestment = 1100
        calculated_disinvestment = simulator.determine_disinvestment(cash_inflow, living_expenses, tax_rate)
        self.assertEqual(expected_disinvestment, calculated_disinvestment)

    def test_determine_disinvestment_invalid_tax_rate_too_high(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = 1.0
        self.assertRaises(ValueError, simulator.determine_disinvestment, cash_inflow, living_expenses, tax_rate)

    def test_determine_disinvestment_invalid_tax_rate_too_low(self):
        cash_inflow = 2600
        living_expenses = 3600
        tax_rate = -0.3
        self.assertRaises(ValueError, simulator.determine_disinvestment, cash_inflow, living_expenses, tax_rate)

    def test_determine_investment_high_income(self):
        cash_inflow = 10000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 4000
        calculated_investment = simulator.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_low_income(self):
        cash_inflow = 5000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 1400
        calculated_investment = simulator.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_no_income(self):
        cash_inflow = 0
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 0
        calculated_investment = simulator.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)

    def test_determine_investment_negative_income(self):
        cash_inflow = -5000
        living_expenses = 3600
        target_investment_amount = 4000
        expected_investment = 0
        calculated_investment = simulator.determine_investment(cash_inflow, living_expenses, target_investment_amount)
        self.assertEqual(expected_investment, calculated_investment)


class TestSimulationAddingCashflows(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23))
        self.simulation = simulator.Simulation(starting_date=datetime.date(2023, 12, 2),
                                               ending_date=datetime.date(2080, 12, 30), investor=self.investor)

    def test_adding_cash_inflow(self):
        cash_inflow = cashflows.Income(2000, datetime.date(2030, 12, 12))
        self.simulation.add_cashflow(cash_inflow)
        expected_df = pd.DataFrame(columns=["Date", "Investor age", "CF direction", "Amount", "Type"],
                                   data=[[datetime.date(2030, 12, 12), 40.0, "Cash inflow", float(2000), "Income"]])
        pd.testing.assert_frame_equal(expected_df, self.simulation.gross_cash_flows)

        cash_inflow_02 = cashflows.Income(8000, datetime.date(2040, 12, 12))
        self.simulation.add_cashflow(cash_inflow_02)
        expected_df_02 = pd.DataFrame(columns=["Date", "Investor age", "CF direction", "Amount", "Type"],
                                      data=[
                                          [datetime.date(2030, 12, 12), 40.0, "Cash inflow", float(2000), "Income"],
                                          [datetime.date(2040, 12, 12), 50.0, "Cash inflow", float(8000), "Income"]])
        pd.testing.assert_frame_equal(expected_df_02, self.simulation.gross_cash_flows)


class TestSimulationCreatingNetCashflows(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23))
        self.simulation = simulator.Simulation(starting_date=datetime.date(2023, 12, 2),
                                               ending_date=datetime.date(2080, 12, 30),
                                               investor=self.investor)
        self.simulation.add_cashflow(cashflows.Income(2000, datetime.date(2030, 1, 13)))
        self.simulation.add_cashflow(cashflows.PrivatePension(3000, datetime.date(2030, 1, 23)))
        self.simulation.add_cashflow(cashflows.Retirement(4000, datetime.date(2030, 4, 13)))
        self.simulation.add_cashflow(cashflows.OtherCashInflow(6000, "Inheritance", datetime.date(2031, 1, 3)))

    def test_net_cashflow(self):

        expected_df = pd.DataFrame(
            columns=["Date", "Cash inflow"],
            data=[
                [datetime.date(2030, 1, 31), 5000.0],
                [datetime.date(2030, 2, 28), 0.0],
                [datetime.date(2030, 3, 31), 0.0],
                [datetime.date(2030, 4, 30), 4000.0],
                [datetime.date(2030, 5, 31), 0.0],
                [datetime.date(2030, 6, 30), 0.0],
                [datetime.date(2030, 7, 31), 0.0],
                [datetime.date(2030, 8, 31), 0.0],
                [datetime.date(2030, 9, 30), 0.0],
                [datetime.date(2030, 10, 31), 0.0],
                [datetime.date(2030, 11, 30), 0.0],
                [datetime.date(2030, 12, 31), 0.0],
                [datetime.date(2031, 1, 31), 6000.0]
            ]
        )
        expected_df.set_index("Date", inplace=True)
        expected_df.index = pd.to_datetime(expected_df.index)
        expected_df.index.freq = "M"
        calculated_df = self.simulation.create_net_cashflows()
        pd.testing.assert_frame_equal(expected_df, calculated_df)


class TestSimulationLivingExpenses(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23), living_expenses=10000)
        self.simulation = simulator.Simulation(starting_date=datetime.date(2023, 12, 2),
                                               ending_date=datetime.date(2080, 12, 30),
                                               investor=self.investor)

    def test_living_expenses_in_the_future_valid_input(self):
        date_of_origin = datetime.date(2020, 3, 23)
        living_expenses = 3600
        future_date = datetime.date(2030, 3, 23)
        inflation = 0.02
        expected_future_living_expenses = 4388.38
        calculated_future_living_expenses = simulator.determine_living_expenses(date_of_origin,
                                                                                living_expenses,
                                                                                future_date,
                                                                                inflation)
        lower_tolerance = expected_future_living_expenses * 0.999
        upper_tolerance = expected_future_living_expenses * 1.001
        self.assertGreaterEqual(calculated_future_living_expenses, lower_tolerance)
        self.assertLessEqual(calculated_future_living_expenses, upper_tolerance)

    def test_living_expenses_in_the_future_date_in_the_past(self):
        date_of_origin = datetime.date(2020, 3, 23)
        living_expenses = 3600
        future_date = datetime.date(2010, 3, 23)
        inflation = 0.02
        self.assertRaises(ValueError, simulator.determine_living_expenses, date_of_origin, living_expenses, future_date,
                          inflation)

    def test_df_of_future_living_expenses(self):
        future_date = datetime.date(2026, 3, 31)
        years_until_future_date = (future_date - self.simulation.starting_date).days / 365.25
        expected_living_expenses = self.investor.living_expenses * \
                                   (1 + self.simulation.inflation)**years_until_future_date
        calculated_df = self.simulation.create_living_expenses()
        print(calculated_df)
        calculated_living_expenses = calculated_df.loc[future_date, "Living expenses"]
        self.assertEqual(expected_living_expenses, calculated_living_expenses)
