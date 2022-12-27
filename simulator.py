from dataclasses import dataclass
import datetime

import pandas as pd

import cashflows


def determine_investor_age(*, date: datetime.date, investor_birthdate: datetime.date) -> float:
    """Determine the age of an investor given a specific date"""
    # todo: implement function
    pass

class Simulation:

    def __init__(self, starting_date: datetime.date, ending_date: datetime.date, investor: Investor):
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.gross_cash_flows = pd.DataFrame(columns=["Date", "Investor age", "CF direction", "Amount", "Type"])
        self.investor = investor

    def add_cash_inflow(self, cash_inflow: cashflows.Inflow):
        """Add a cash inflow to the gross cashflows"""
        age = determine_investor_age(date=cash_inflow.date, investor_birthdate=self.investor.birthdate)


@dataclass
class Investor:

    first_name: str
    last_name: str
    birthdate: datetime.date


@dataclass
class Portfolio:

    df: pd.DataFrame
    pf_value_initial: float
