from collections import OrderedDict
import datetime
import math
import numpy as np
import pandas as pd
from typing import List, Tuple, Union


def analyze_survival_probability(list_of_pf_valuations: List[pd.Series]) -> float:
    """
    Analyze the survival probability of a list of portfolio valuations over time.
    :param list_of_pf_valuations: List[pd.Series] - a list of pandas Series representing portfolio valuations over time
    :return: float - the probability that a portfolio has always been positive in value over time
    """
    if not list_of_pf_valuations:
        raise ValueError("The list of portfolio valuations is empty.")

    # use list comprehension to create a list of booleans representing survival
    survivals = [determine_survival(series) for series in list_of_pf_valuations]

    return sum(survivals) / len(survivals)


def determine_age(date: datetime.date, birthdate: datetime.date) -> float:
    """Determine the age of a person given a specific date"""
    if date < birthdate:
        raise ValueError("The date has to be larger than the birthdate")

    delta_in_years = (date - birthdate).days / 365.25
    return round(delta_in_years, 1)


def determine_cash_need(cash_inflow: float, living_expenses: float) -> float:
    """
    Determine the cash need based on cash inflow and living expenses

    :param cash_inflow: cash inflow
    :param living_expenses: living expenses
    :return: the amount of living expenses that cannot be covered by the cash inflow
    """
    if cash_inflow < 0:
        raise ValueError("Cash inflow cannot be negative")
    if living_expenses < 0:
        raise ValueError("Living expenses cannot be negative")
    return max(0, living_expenses - cash_inflow)



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

    :param series: pd.Series - a series of (portfolio) values
    :return: bool - True if the portfolio has always been positive in value over time, False otherwise
    """
    return (series.values > 0).all()


def determine_taxes(sale_price: float, historical_price: float, number_of_shares: float,
                    tax_rate: float = 0.26375, tax_exemption: float = 0, loss_pot: float = 0) -> Tuple[float, float]:
    """
    Calculate taxes on a sale of shares
    :param sale_price: price at which the shares are sold
    :param historical_price: price at which the shares were bought
    :param number_of_shares: nr of shares to be sold
    :param tax_rate: tax rate at which the gain will be taxed
    :param tax_exemption: only gains beyond the tax exemption amount are taxed
    :param loss_pot: the loss carryforward (loss pot)
    :return: list of absolute taxes and taxes in relation to the transaction volume
    """
    if tax_exemption < 0:
        raise ValueError("A tax exemption amount may not be negative.")

    if loss_pot < 0:
        raise ValueError("A loss pot may not be negative.")

    gain = (sale_price - historical_price) * number_of_shares
    if gain < 0 or gain <= tax_exemption + loss_pot:
        return 0, 0
    else:
        taxes_abs = (gain - tax_exemption - loss_pot) * tax_rate
        taxes_rel = taxes_abs / (sale_price * number_of_shares)
        return taxes_abs, taxes_rel


def determine_taxes_for_transactions(transactions: OrderedDict, share_price: float, tax_rate: float = 0.26375,
                                     tax_exemption: float = 0) -> Tuple[float, float]:
    """
    Calculate taxes for a list of transactions
    :param transactions: Ordered dictionary of transactions containing shares to be sold (key) and their
        historical prices and sale prices (values)
    :param share_price: the price at which the shares were sold
    :param tax_rate: the rate at which net gains are taxed
    :param tax_exemption: the amount of gains that will not be taxed
    :return: tuple of absolute taxes and relative taxes in relation to the transaction volume
    """
    transaction_volume = 0
    taxes_abs = 0
    for key, value in transactions.items():
        nr_shares = key
        historical_price = value[0]
        transaction_volume += nr_shares * share_price
        taxes_abs += determine_taxes(sale_price=share_price, historical_price=historical_price,
                                     number_of_shares=key, tax_rate=tax_rate, tax_exemption=tax_exemption)[0]
        gain_loss = key * (share_price - historical_price)
        tax_exemption = max(0, tax_exemption - max(0, gain_loss))

    try:
        taxes_rel = taxes_abs / transaction_volume
    except ZeroDivisionError as err:
        taxes_rel = 0

    return taxes_abs, taxes_rel

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

