import datetime
import math
import unittest
from collections import OrderedDict

import numpy as np
import pandas as pd

import cashflows
import simulator
import tax_estimator


class TestHelperFunctions(unittest.TestCase):





    def test_determine_cash_need_high_income(self):
        cash_inflow = 10000
        living_expenses = 3000
        exp_cash_need = 0
        calc_cash_need = simulator.determine_cash_need(cash_inflow, living_expenses)
        self.assertEqual(exp_cash_need, calc_cash_need)

    def test_determine_cash_need_high_living_expenses(self):
        cash_inflow = 1000
        living_expenses = 3000
        exp_cash_need = 2000
        calc_cash_need = simulator.determine_cash_need(cash_inflow, living_expenses)
        self.assertEqual(exp_cash_need, calc_cash_need)


class TestSimulationAddingCashflows(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23))
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2023, 12, 2),
                                               ending_date=datetime.date(2080, 12, 30),
                                               investor=self.investor,
                                               portfolio=pf)

    def test_adding_cashflows(self):
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
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2029, 12, 2),
                                               ending_date=datetime.date(2031, 3, 27),
                                               investor=self.investor,
                                               portfolio=pf)
        self.simulation.add_cashflow(cashflows.Income(2000, datetime.date(2030, 1, 13)))
        self.simulation.add_cashflow(cashflows.PrivatePension(3000, datetime.date(2030, 1, 23)))
        self.simulation.add_cashflow(cashflows.Retirement(4000, datetime.date(2030, 4, 13)))
        self.simulation.add_cashflow(cashflows.OtherCashInflow(6000, "Inheritance", datetime.date(2031, 1, 3)))

    def test_net_cashflow(self):
        expected_df = pd.DataFrame(
            columns=["Date", "Cashflow"],
            data=[
                [datetime.date(2029, 12, 31), 0.0],
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
                [datetime.date(2031, 1, 31), 6000.0],
                [datetime.date(2031, 2, 28), 0.0]
            ]
        )
        expected_df.set_index("Date", inplace=True)
        expected_df.index = pd.to_datetime(expected_df.index)
        expected_df.index.freq = "M"
        calculated_df = self.simulation._create_net_cashflows()
        pd.testing.assert_frame_equal(expected_df, calculated_df)




class TestInvestmentDataframe(unittest.TestCase):

    def setUp(self) -> None:
        self.df = pd.DataFrame(columns=["Cashflow", "Living expenses"],
                               index=pd.date_range(datetime.date(2022, 1, 22), datetime.date(2022, 5, 28), freq="M"),
                               data=[[8000, 3000], [6000, 3200], [0, 3400], [1200, 3800]])
        self.cash_inflows = self.df["Cashflow"].to_frame()
        self.living_expenses = self.df["Living expenses"].to_frame()
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23),
                                           living_expenses=3000,
                                           target_investment_amount=4000.0)
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2022, 1, 22),
                                               ending_date=datetime.date(2080, 5, 28),
                                               investor=self.investor, portfolio=pf)


class TestInvestmentsAndDisinvestments(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23),
                                           living_expenses=3000,
                                           target_investment_amount=4000.0,
                                           )
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2022, 1, 22),
                                               ending_date=datetime.date(2022, 5, 28),
                                               investor=self.investor,
                                               portfolio=pf,
                                               inflation=0.0)
        self.simulation.add_cashflow(cashflows.Income(8000, datetime.date(2022, 1, 12)))
        self.simulation.add_cashflow(cashflows.Income(6000, datetime.date(2022, 2, 19)))
        self.simulation.add_cashflow(cashflows.Income(1200, datetime.date(2022, 4, 29)))
        data = [[8000, 3000, 4000, 0], [6000, 3000, 3000, 0], [0, 3000, 0, 5000], [1200, 3000, 0, 3000]]
        data = [list(map(float, sublist)) for sublist in data]
        self.df = pd.DataFrame(columns=["Cashflow", "Living expenses", "Investments", "Disinvestments"],
                               index=pd.date_range(datetime.date(2022, 1, 22), datetime.date(2022, 5, 28), freq="M"),
                               data=data)
        self.cash_inflows = self.df["Cashflow"].to_frame()
        self.living_expenses = self.df["Living expenses"].to_frame()
        self.investments = self.df[["Living expenses", "Investments"]].copy()
        self.disinvestments = self.df[["Living expenses", "Disinvestments"]].copy()


class TestAdditionalLivingExpenses(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23),
                                           living_expenses=1000,
                                           target_investment_amount=4000.0,
                                           )
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2022, 1, 22),
                                               ending_date=datetime.date(2022, 5, 28),
                                               investor=self.investor,
                                               portfolio=pf,
                                               inflation=0.0)
        self.simulation.add_cashflow(cashflows.Income(8000, datetime.date(2022, 1, 12)))
        self.simulation.add_cashflow(cashflows.Income(6000, datetime.date(2022, 2, 19)))
        self.simulation.add_cashflow(cashflows.AdditionalLivingExpenses(6000, datetime.date(2022, 4, 23)))


class TestAddingRecurringCashflows(unittest.TestCase):

    def setUp(self) -> None:
        self.investor = simulator.Investor("John", "Doe", datetime.date(1990, 12, 23),
                                           living_expenses=1000,
                                           target_investment_amount=4000.0,
                                           )
        pf = tax_estimator.Portfolio()
        self.simulation = simulator.Simulation(starting_date=datetime.date(2022, 1, 22),
                                               ending_date=datetime.date(2022, 7, 28),
                                               investor=self.investor,
                                               portfolio=pf,
                                               inflation=0.0)
        self.simulation.add_recurring_cashflows(cashflow=cashflows.Income(4000, datetime.date(2022, 1, 28)),
                                                ending_date=datetime.date(2022, 4, 28),
                                                perc_increase_per_year=0.0)


class TestAnalysisOfSimulationResults(unittest.TestCase):

    def test_survival_of_portfolio_true(self):
        series = pd.Series(data=[23, 0, 12, 45])
        self.assertTrue(simulator.determine_survival(series))

    def test_survival_of_portfolio_false(self):
        series = pd.Series(data=[23, 0, -2, 45])
        self.assertFalse(simulator.determine_survival(series))

    def test_timing_of_portfolio_death(self):
        self.assertEqual(3, simulator.determine_portfolio_death(pd.Series(data=[23, 0, 2, -5])))
        self.assertEqual(0, simulator.determine_portfolio_death(pd.Series(data=[-2, 0, 2, -5])))
        self.assertEqual(1, simulator.determine_portfolio_death(pd.Series(data=[23, -3, 2, -5])))
        self.assertTrue(math.isnan(simulator.determine_portfolio_death(pd.Series(data=[23, 3, 2, 232]))))

    def test_survival_probability(self):
        series_01 = pd.Series(data=[23, 0, 2, -5])
        series_02 = pd.Series(data=[23, 0, 2, 12])
        series_03 = pd.Series(data=[23, 0, 2, 16])
        series_04 = pd.Series(data=[23, 0, 2, 99])
        expected_result = 0.75
        calculated_result = simulator.analyze_survival_probability([series_01, series_02, series_03, series_04])

        self.assertEqual(expected_result, calculated_result)
