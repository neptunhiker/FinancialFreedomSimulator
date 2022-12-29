from dataclasses import dataclass
import datetime

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

    return max((living_expenses - cash_inflow) * (1 + tax_rate), 0)


def determine_investment(cash_inflow: float, living_expenses: float, target_investment: float) -> float:
    """
    Determine an investment amount

    cash_inflow: float - the net cash inflow from income, retirement, private pension etc. for that month
    living_expenses: float - the living expenses for that month
    target_investment: float - the amount which is intended to be saved as a maximum for that month
    """

    return max(min(cash_inflow - living_expenses, target_investment), 0)


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

    def add_cashflow(self, cash_inflow: cashflows.Cashflow):
        """Add a cash inflow to the gross cashflows"""
        investor_age = determine_investor_age(date=cash_inflow.date, investor_birthdate=self.investor.birthdate)
        new_df = pd.DataFrame(columns=self.gross_cash_flows.columns, data=[[cash_inflow.date, investor_age,
                                                                            cash_inflow.direction,
                                                                            float(cash_inflow.amount),
                                                                            cash_inflow.description]])
        self.gross_cash_flows = pd.concat([self.gross_cash_flows, new_df], ignore_index=True)

    def create_net_cashflows(self) -> pd.DataFrame:
        """Create a dataframe of net cash flows out of gross cash flows"""

        gross_df = self.gross_cash_flows.copy()
        gross_df.drop(["Investor age"], axis=1, inplace=True)
        gross_df.set_index("Date", inplace=True)
        gross_df.index = pd.to_datetime(gross_df.index)
        grouped = gross_df.groupby(pd.Grouper(freq="M")).sum()
        grouped.rename(columns={"Amount": "Cash inflow"}, inplace=True)
        return grouped

    def create_living_expenses(self) -> pd.DataFrame:
        """Create dataframe with future living expenses scaled by inflation"""

        df = pd.DataFrame(columns=["Date", "Living expenses"])
        df["Date"] = pd.date_range(self.starting_date, self.ending_date, freq="M")
        df["Date"] = df["Date"].apply(lambda x: x.date())
        df["Living expenses"] = df.apply(lambda x: determine_living_expenses(
            self.starting_date, self.investor.living_expenses, x["Date"], self.inflation), axis=1)
        df.set_index("Date", inplace=True)
        return df
