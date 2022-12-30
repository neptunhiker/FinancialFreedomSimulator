from dataclasses import dataclass
import datetime

import numpy as np
import pandas as pd

import cashflows


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


def determine_investment(cash_inflow: float, living_expenses: float, target_investment: float) -> float:
    """
    Determine an investment amount

    cash_inflow: float - the net cash inflow from income, retirement, private pension etc. for that month
    living_expenses: float - the living expenses for that month
    target_investment: float - the amount which is intended to be saved as a maximum for that month
    """

    return float(max(min(cash_inflow - living_expenses, target_investment), 0))


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
    tax_rate: float = 0.05


@dataclass
class Portfolio:
    df: pd.DataFrame
    pf_value_initial: float


class Simulation:

    def __init__(self, starting_date: datetime.date, ending_date: datetime.date, investor: Investor,
                 inflation: float = 0.02):
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.gross_cash_flows = pd.DataFrame(columns=["Date", "Investor age", "CF direction", "Amount", "Type"])
        self.investor = investor
        self.inflation = inflation

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

    def _create_net_cashflows(self) -> pd.DataFrame:
        """Create a dataframe of net cash flows out of gross cash flows"""

        gross_df = self.gross_cash_flows.copy()
        gross_df.drop(["Investor age"], axis=1, inplace=True)
        gross_df.set_index("Date", inplace=True)
        gross_df.index = pd.to_datetime(gross_df.index)
        grouped = gross_df.groupby(pd.Grouper(freq="M")).sum()
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
                              (1 + self.inflation) ** ((x["Date"].date() - self.starting_date).days / 365.25)
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

        return df_complete


if __name__ == '__main__':
    investor = Investor("John", "Doe", datetime.date(1990, 12, 23),
                        living_expenses=3000,
                        target_investment_amount=4000.0)
    simulation = Simulation(starting_date=datetime.date(2022, 1, 22),
                            ending_date=datetime.date(2080, 5, 28),
                            investor=investor)
    simulation.create_df_of_investments_and_disinvestments()
