import datetime
import math
from typing import List, Union


def determine_age(date: datetime.date, birthdate: datetime.date) -> float:
    """Determine the age of a person given a specific date"""
    if date < birthdate:
        raise ValueError("The date has to be larger than the birthdate")

    delta_in_years = (date - birthdate).days / 365.25
    return round(delta_in_years, 1)


def determine_disinvestment(cash_inflow: float, living_expenses: float, tax_rate: float, safety_buffer: bool = False,
                            months_to_simulate: int = None, pf_value: float = None) -> float:
    """
    Determine a disinvestment amount
    :param cash_inflow: the net cash inflow from income, retirement, private pension etc. for that month
    :param living_expenses: the living expenses for that month
    :param tax_rate: the rate at which the disinvestment is assumed to be taxed
    :param safety_buffer: if true then the disinvestment is capped linearly based on pf value and months to simulate
    :param months_to_simulate: number of months left to simulate, ignored if safety_buffer is False
    :param pf_value: value of the portfolio, ignored if safety_buffer is False
    :return float of disinvestment amount
    """
    validate_tax_rate(tax_rate)

    unconstrained_disinvestment = max((living_expenses - cash_inflow) / (1 - tax_rate), 0)
    if safety_buffer:
        linear_threshold = pf_value / months_to_simulate
        return min(linear_threshold, unconstrained_disinvestment)
    else:
        return unconstrained_disinvestment


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


def validate_positive_numbers(positive_numbers: List[Union[float, int]]) -> None:
    """
    Validate whether the given argument is a positive number
    :param positive_numbers: A list of numbers to be validated
    :return: None
    """
    if not positive_numbers:
        raise ValueError("The given list to validate has to contain entries. It is currently an empty list.")
    for positive_number in positive_numbers:
        if math.isnan(positive_number):
            raise ValueError("The given argument must be a valid number.")
        if positive_number <= 0:
            raise ValueError("The given argument must be a positive number.")


def validate_tax_rate(tax_rate: float) -> None:
    """
    Validate a tax rate
    :param tax_rate: float to be validated
    :return: None
    """
    if tax_rate >= 1:
        raise ValueError("The tax rate is too high (i.e. greater or equal to 100%.")
    elif tax_rate < 0:
        raise ValueError("The tax rate is too low (i.e. lower than 0%).")

