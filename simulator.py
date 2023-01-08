import calendar
import math
from dataclasses import dataclass
import datetime

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pandas as pd
from pprint import pprint
from typing import List, Union, Tuple

import cashflows
import returngens


def analyze_survival_probability(list_of_pf_valuations: List[pd.Series]) -> float:
    """Analyze how many portfolios of the simulation would have survived with a value greater than zero throughout time"""

    survivals = []
    for series in list_of_pf_valuations:
        survivals.append(determine_survival(series))

    return sum(survivals) / len(survivals)


def determine_portfolio_death(series: pd.Series) -> Union[int, float]:
    """
    Determine the point in time of a portfolio having a negative valuation

    series: pd.Series - a series of (portfolio) values
    """

    if determine_survival(series):
        return np.nan
    else:
        return int(np.argmax(series.lt(0).to_numpy(), axis=0))


def determine_survival(series: pd.Series) -> bool:
    """
    Determine whether a portfolio has always been positive in value over time

    series: pd.Series - a series of (portflio) values
    """
    return (series >= 0).all()


def determine_disinvestment(cash_inflow: float, living_expenses: float, tax_rate: float) -> float:
    """
    Determine a disinvestment amount

    cash_inflow: float - the net cash inflow from income, retirement, private pension etc. for that month
    living_expenses: float - the living expenses for that month
    tax_rate: float - the rate at which the disinvestment is assumed to be taxed
    """
    if tax_rate >= 1:
        raise ValueError("The tax rate is too high (i.e. greater or equal to 100%.")
    elif tax_rate < 0:
        raise ValueError("The tax rate is too low (i.e. lower than 0%).")

    return max((living_expenses - cash_inflow) / (1 - tax_rate), 0)


def determine_investment(cash_inflow: float, living_expenses: float, target_investment: float,
                         investment_cap: bool = True) -> float:
    """
    Determine an investment amount

    cash_inflow: float - the net cash inflow from income, retirement, private pension etc. for that month
    living_expenses: float - the living expenses for that month
    target_investment: float - the amount which is intended to be saved as a maximum for that month
    """

    if investment_cap:
        return float(max(min(cash_inflow - living_expenses, target_investment), 0))
    else:
        return float(max(cash_inflow - living_expenses, 0))


def determine_investor_age(date: datetime.date, investor_birthdate: datetime.date) -> float:
    """Determine the age of an investor given a specific date"""
    if date < investor_birthdate:
        raise ValueError("The date has to be larger than the investor's birthdate")

    delta_in_years = (date - investor_birthdate).days / 365.25
    return round(delta_in_years, 1)


def determine_living_expenses(date_of_origin: datetime.date, living_expenses_at_date_of_origin: float,
                              future_date: datetime.date, inflation: float) -> float:
    """
    Determine living expenses at a future date

    date_of_origin: datetime.date - date at which living expenses are known
    living_expenses_at_date_of_origin: float - living expenses at date_of_origin
    future_date: datetime.date - date at which living expenses are to be determined
    inflation: float - expected increase of living expenses per year
    """
    if future_date < date_of_origin:
        raise ValueError

    delta_in_years = (future_date - date_of_origin).days / 365.25
    increase_due_to_inflation = (1 + inflation) ** delta_in_years
    return living_expenses_at_date_of_origin * increase_due_to_inflation


@dataclass
class Investor:
    first_name: str
    last_name: str
    birthdate: datetime.date
    living_expenses: float = 4000.0
    target_investment_amount: float = 4000.0
    investment_cap: bool = True
    tax_rate: float = 0.05
    current_portfolio_value: float = 200000

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass
class Portfolio:
    df: pd.DataFrame
    pf_value_initial: float


class Simulation:

    def __init__(self, starting_date: datetime.date, ending_date: datetime.date, investor: Investor,
                 inflation: float = 0.02, return_generator: returngens.ReturnGenerator = returngens.GBM(0.07, 0.2)):
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.gross_cash_flows = pd.DataFrame(columns=["Date", "Investor age", "CF direction", "Amount", "Type"])
        self.investments_disinvestments = pd.DataFrame()
        self.investor = investor
        self.inflation = inflation
        self.return_generator = return_generator
        self.results = dict()

    def add_cashflow(self, cashflow: cashflows.Cashflow):
        """Add a cash inflow to the gross cashflows"""
        investor_age = determine_investor_age(date=cashflow.date, investor_birthdate=self.investor.birthdate)
        if cashflow.direction == "Cash inflow":
            amount = float(cashflow.amount)
        elif cashflow.direction == "Cash outflow":
            amount = float(-cashflow.amount)
        else:
            raise ValueError("Unknown cashflow direction.")
        new_df = pd.DataFrame(columns=self.gross_cash_flows.columns, data=[[cashflow.date, investor_age,
                                                                            cashflow.direction,
                                                                            float(amount),
                                                                            cashflow.description]])
        self.gross_cash_flows = pd.concat([self.gross_cash_flows, new_df], ignore_index=True)

    def add_recurring_cashflows(self, cashflow: cashflows.Cashflow, ending_date: datetime.date,
                                perc_increase_per_year: float = 0) -> None:
        """Add recurring cashflows to the simulation"""

        _, days_in_month = calendar.monthrange(ending_date.year, ending_date.month)
        ending_date = datetime.date(year=ending_date.year, month=ending_date.month, day=days_in_month)
        date_range = pd.date_range(cashflow.date, ending_date, freq="M")
        for date in date_range:
            t = (date.date() - cashflow.date).days / 365.25
            amount = cashflow.amount * (1 + perc_increase_per_year) ** t
            new_cf = cashflows.Cashflow(amount=amount, description=cashflow.description, date=date.date(),
                                        direction=cashflow.direction)
            self.add_cashflow(new_cf)

    def _create_net_cashflows(self) -> pd.DataFrame:
        """Create a dataframe of net cash flows out of gross cash flows"""

        gross_df = self.gross_cash_flows.copy()
        gross_df.drop(["Investor age"], axis=1, inplace=True)
        gross_df.set_index("Date", inplace=True)
        gross_df.index = pd.to_datetime(gross_df.index)
        grouped = gross_df.groupby(pd.Grouper(freq="M")).sum(numeric_only=True)
        grouped.rename(columns={"Amount": "Cashflow"}, inplace=True)

        # reindex dataframe so that the index date covers the entire simulation time period
        idx = pd.date_range(self.starting_date, self.ending_date, freq="M")
        grouped = grouped.reindex(idx)
        grouped.reset_index(inplace=True)
        grouped.rename(columns={"index": "Date"}, inplace=True)
        grouped["Date"].apply(lambda x: x.date())
        grouped.set_index(["Date"], inplace=True)
        grouped.index.freq = "M"

        # fill dataframe with zeroes if dataframe is otherwise empty
        if grouped.empty:
            grouped["Cashflow"] = np.zeros(len(grouped))

        # fill NaN values with zeroes
        grouped["Cashflow"] = grouped["Cashflow"].fillna(0)

        return grouped

    def _create_living_expenses(self) -> pd.DataFrame:
        """Create dataframe with future living expenses scaled by inflation"""

        df = pd.DataFrame(columns=["Date", "Living expenses"])
        df["Date"] = pd.date_range(self.starting_date, self.ending_date, freq="M")
        df["Date"] = df["Date"].apply(lambda x: x.date())
        df["Living expenses"] = df.apply(lambda x: determine_living_expenses(
            self.starting_date, self.investor.living_expenses, x["Date"], self.inflation), axis=1)
        df.set_index("Date", inplace=True)
        return df

    def _create_investments(self, df_cash_inflows: pd.DataFrame, df_living_expenses: pd.DataFrame) -> pd.DataFrame:
        """
        Create dataframe that includes cash inflows, living expenses and corresponding investment amounts.

        df_cash_inflows: pd.DataFrame - a dataframe that contains net cash inflows over time
        df_living_expenses: pd.DataFrame - a dataframe that contains future living expenses
        """

        # check consistency of data frames
        if not df_cash_inflows.index.equals(df_living_expenses.index):
            raise ValueError("Indices of data frames are not the same!")

        joined_df = pd.concat([df_cash_inflows, df_living_expenses], axis=1)
        joined_df.reset_index(inplace=True)
        joined_df.rename(columns={"index": "Date"}, inplace=True)
        joined_df["Date"] = pd.to_datetime(joined_df["Date"])
        joined_df["Investments"] = joined_df.apply(lambda x: determine_investment(
            cash_inflow=x["Cashflow"],
            living_expenses=x["Living expenses"],
            target_investment=self.investor.target_investment_amount *
                              (1 + self.inflation) ** ((x["Date"].date() - self.starting_date).days / 365.25),
            investment_cap=self.investor.investment_cap
        ), axis=1)

        joined_df.set_index(["Date"], inplace=True)
        joined_df.index.freq = "M"

        return joined_df

    def _create_disinvestments(self, df_cash_inflows: pd.DataFrame, df_living_expenses: pd.DataFrame) -> pd.DataFrame:
        """
        Create dataframe that includes cash inflows, living expenses and corresponding disinvestment amounts.

        df_cash_inflows: pd.DataFrame - a dataframe that contains net cash inflows over time
        df_living_expenses: pd.DataFrame - a dataframe that contains future living expenses
        """
        # check consistency of data frames
        if not df_cash_inflows.index.equals(df_living_expenses.index):
            raise ValueError("Indices of data frames are not the same!")

        joined_df = pd.concat([df_cash_inflows, df_living_expenses], axis=1)
        joined_df.reset_index(inplace=True)
        joined_df.rename(columns={"index": "Date"}, inplace=True)
        joined_df["Date"] = pd.to_datetime(joined_df["Date"])
        joined_df["Disinvestments"] = joined_df.apply(lambda x: determine_disinvestment(
            cash_inflow=x["Cashflow"],
            living_expenses=x["Living expenses"],
            tax_rate=self.investor.tax_rate
        ), axis=1)

        joined_df.set_index(["Date"], inplace=True)
        joined_df.index.freq = "M"

        return joined_df

    def create_df_of_investments_and_disinvestments(self):
        """Create a dataframe that contains net cash inflows, living expenses, investment and disinvestments"""

        df_net_cashflows = self._create_net_cashflows()
        df_living_expenses = self._create_living_expenses()
        df_investments = self._create_investments(df_net_cashflows, df_living_expenses)
        df_disinvestments = self._create_disinvestments(df_net_cashflows, df_living_expenses)

        # check that net cash flows and living expenses are the same
        if not df_investments["Cashflow"].equals(df_disinvestments["Cashflow"]):
            raise ValueError("Series for net cash inflows are not the same!")
        if not df_investments["Living expenses"].equals(df_disinvestments["Living expenses"]):
            raise ValueError("Series for living expenses are not the same!")

        df_complete = pd.concat([df_investments, df_disinvestments], axis=1)

        # remove duplicate columns (living expenses and cash inflows should be in twice)
        df_complete = df_complete.loc[:, ~df_complete.columns.duplicated()].copy()

        self.investments_disinvestments = df_complete

        return df_complete

    def create_portfolio_valuations(self) -> pd.DataFrame:
        """
        Create a dataframe that simulates the portfolio valuation
        """

        # check that a dataframe for investments and disinvestments has already been generated
        if "Investments" not in self.investments_disinvestments.columns and \
                "Disinvestments" not in self.investments_disinvestments.columns:
            raise ValueError("Before being able to create portfolio valuations a dataframe needs to be created "
                             "that contains investments and disinvestments")

        df = self.investments_disinvestments.copy()

        # add a column for the return data (needs to be simulated)
        df["Log return"] = self.return_generator.generate_monthly_returns(n=len(self.investments_disinvestments)).values

        # add additional columns for PF valuation at the beginning and end of period
        df["PF Beg"] = np.zeros(len(df))
        df["PF End"] = np.zeros(len(df))

        # loop through dataframe and update portfolio values
        counter = 0
        for index, row in df.iterrows():
            if counter == 0:
                row["PF Beg"] = self.investor.current_portfolio_value
            else:
                row["PF Beg"] = df.loc[previous_index, "PF End"]

            if row["PF Beg"] < 0:
                row["PF End"] = row["PF Beg"] + row["Investments"] - row["Disinvestments"]
            else:
                row["PF End"] = math.exp(row["Log return"]) * row["PF Beg"] + row["Investments"] - row["Disinvestments"]

            previous_index = index
            counter += 1

        return df

    def run_simulation(self, n: int = 10) -> None:
        """
        Run the simulation

        n: int - number of simulations
        """

        self.create_df_of_investments_and_disinvestments()

        for i in range(n):
            self.results[i] = self.create_portfolio_valuations()

    def plot_results(self) -> None:
        """Plot the simulation results"""

        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 6))
        fig.suptitle(f'Financial Freedom Simulator for {self.investor.name}', fontsize=20)

        # ax1
        for sim_run, df in self.results.items():
            ax1.plot(df.index, df["PF End"])
        ax1.axhline(0, linestyle='dotted', color='grey')  # horizontal lines
        ax1.axvline(datetime.date(2051, 1, 31), linestyle="--", color="black")
        ax1.set_ylim(-3000000, 30000000)
        ax1.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        # todo: put the calculations outside of the method for plotting
        pf_valuations_lower_percentile = dict()
        pf_valuations_median = dict()
        pf_valuations_upper_percentile = dict()
        lower_percentile = 10
        upper_percentile = 90
        for date in self.investments_disinvestments.index:
            valuations = []
            for df in self.results.values():
                valuations.append(int(df.loc[date, "PF End"]))
            pf_valuations_lower_percentile[date] = np.percentile(valuations, lower_percentile)
            pf_valuations_median[date] = np.percentile(valuations, 50)
            pf_valuations_upper_percentile[date] = np.percentile(valuations, upper_percentile)
        ax2.plot(pf_valuations_upper_percentile.keys(), pf_valuations_upper_percentile.values(),
                 label=f"{upper_percentile} % percentile")
        ax2.plot(pf_valuations_median.keys(), pf_valuations_median.values(),
                 label=f"{50} % percentile")
        ax2.plot(pf_valuations_lower_percentile.keys(), pf_valuations_lower_percentile.values(),
                 label=f"{lower_percentile} % percentile")
        ax2.axhline(0, linestyle='dotted', color='grey')  # horizontal lines
        ax2.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.legend()

        plt.show()

    def analyze_results(self) -> dict:
        """Analyze the portfolio results"""

        results = dict()

        # survival probability
        pf_valuations = []
        for df in self.results.values():
            pf_valuations.append(df["PF End"])
        results["Survival probability"] = analyze_survival_probability(pf_valuations)

        # earliest portfolio death, i.e. valuation < 0
        if results["Survival probability"] == 1.0:
            results["Earliest portfolio death"] = "All portfolios survived"
        else:
            pf_valuation_dates = self.results[0].index
            pf_deaths = []
            for pf_valuation in pf_valuations:
                pf_deaths.append(determine_portfolio_death(pf_valuation))
            results["Earliest portfolio death"] = pf_valuation_dates[int(np.nanmin(pf_deaths))].date()

        return results


def return_simulator(monthly_investment: int = 4000, yearly_increase_of_monthly_investment: float = 0.02,
                     months_to_simulate: int = 120, expected_rate_of_return: float = 0.08,
                     initial_pf_value: int = 200000, plot: bool = False, inflation: float = 0.03) -> Tuple[int, int]:
    """
    Simulate the return path of a monthly investment with a given expected rate of return
    """

    df = pd.DataFrame(index=range(0, months_to_simulate + 1))
    for i in range(0, months_to_simulate + 1):
        if i == 0:
            df.loc[i, "PF value nominal"] = initial_pf_value
            df.loc[i, "PF value real"] = initial_pf_value
        else:
            df.loc[i, "PF value nominal"] = int(df.loc[i - 1, "PF value nominal"] * (1 + expected_rate_of_return / 12) + \
                                        monthly_investment * (1 + yearly_increase_of_monthly_investment / 12) ** (
                                                    i - 1))
            df.loc[i, "PF value real"] = df.loc[i, "PF value nominal"] / (1 + inflation / 12) ** (i - 1)

    if plot:
        fig, ax = plt.subplots(figsize=(10,6))
        ax.plot(df["PF value nominal"], label="PF value nominal")
        ax.plot(df["PF value real"], label="PF value real")
        fig.suptitle(f"Portfolio simulator based on monthly investments of {monthly_investment} EUR increasing "
                     f"by {yearly_increase_of_monthly_investment*100} % per year\nsimulated over "
                     f"{months_to_simulate} months "
                     f"({round(months_to_simulate/12, 1)} years) with an inflation of {round(inflation * 100, 1)} %\n"
                     f"and an expected rate of return of {round(expected_rate_of_return*100, 1)} % per year. Initial "
                     f"PF value: {format(initial_pf_value, ',')} EUR.")
        plt.xlabel("Months")
        plt.ylabel("PF value")
        ax.grid()
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.legend()
        fig.tight_layout()
        plt.show()

    nominal_final_value = int(df.iloc[-1]["PF value nominal"])
    real_final_value = int(nominal_final_value / (1 + inflation) ** (months_to_simulate / 12))

    return nominal_final_value, real_final_value


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.expand_frame_repr', False)

    print(return_simulator(monthly_investment=4500,
                           expected_rate_of_return=0.07,
                           yearly_increase_of_monthly_investment=0.05,
                           months_to_simulate=120,
                           initial_pf_value=200000,
                           inflation=0.03,
                           plot=True))

    print(return_simulator(monthly_investment=20,
                           expected_rate_of_return=0.0849,
                           yearly_increase_of_monthly_investment=0.0,
                           months_to_simulate=600,
                           initial_pf_value=0,
                           inflation=0.03,
                           plot=True))
    #
    # print(return_simulator(monthly_investment=20,
    #                        expected_rate_of_return=0.08,
    #                        yearly_increase_of_monthly_investment=0.0,
    #                        months_to_simulate=144,
    #                        initial_pf_value=1440,
    #                        inflation=0.03,
    #                        plot=True))
    #
    # print(return_simulator(monthly_investment=2500,
    #                        expected_rate_of_return=0.08,
    #                        yearly_increase_of_monthly_investment=0.04,
    #                        months_to_simulate=120,
    #                        initial_pf_value=200000,
    #                        inflation=0.03,
    #                        plot=True))
    #
    # yearly_return = 0.08
    # yearly_vola = 0.18
    # number_of_simulations = 200
    #
    # investor = Investor("Me", "Lord", datetime.date(1984, 1, 22),
    #                     living_expenses=3000,
    #                     target_investment_amount=4500.0,
    #                     investment_cap=True,
    #                     tax_rate=0.05,
    #                     current_portfolio_value=200000)
    #
    # simulation = Simulation(starting_date=datetime.date(2023, 1, 22),
    #                         ending_date=datetime.date(2074, 1, 22),
    #                         investor=investor,
    #                         inflation=0.03,
    #                         return_generator=returngens.GBM(
    #                             yearly_return=yearly_return,
    #                             yearly_vola=yearly_vola))
    #
    # simulation.add_recurring_cashflows(cashflow=cashflows.Income(8000, datetime.date(2023, 1, 29)),
    #                                    ending_date=datetime.date(2033, 1, 23), perc_increase_per_year=0.04)
    # simulation.add_recurring_cashflows(cashflow=cashflows.Income(3000, datetime.date(2035, 1, 29)),
    #                                    ending_date=datetime.date(2040, 1, 23), perc_increase_per_year=0.01)
    # simulation.add_recurring_cashflows(cashflow=cashflows.Income(2500, datetime.date(2042, 1, 29)),
    #                                    ending_date=datetime.date(2048, 1, 23), perc_increase_per_year=0.01)
    # simulation.add_recurring_cashflows(cashflow=cashflows.Retirement(2500, datetime.date(2051, 1, 29)),
    #                                    ending_date=simulation.ending_date, perc_increase_per_year=0.02)
    # simulation.add_recurring_cashflows(cashflow=cashflows.PrivatePension(1200, datetime.date(2051, 1, 29)),
    #                                    ending_date=simulation.ending_date, perc_increase_per_year=0.02)
    # simulation.add_cashflow(cashflow=cashflows.Inheritance(50000, datetime.date(2040, 3, 2)))
    #
    # simulation.run_simulation(n=number_of_simulations)
    # pprint(simulation.analyze_results())
    # simulation.plot_results()

    # todo: inheritance is still capped by investment cap which shouldn't be the case
