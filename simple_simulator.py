"""
This module simulates the return path of a monthly investment with a given expected rate of return. It has the ability to
plot the portfolio value over time, and also adjust for inflation. It contains three main functions:

simulate_portfolio(monthly_investment, yearly_increase_of_monthly_investment, months_to_simulate,
expected_rate_of_return, initial_pf_value, inflation)

plot_portfolio(df, title)

return_simulator(monthly_investment, yearly_increase_of_monthly_investment, months_to_simulate, expected_rate_of_return,
initial_pf_value, plot, inflation)

"""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from typing import Tuple


def simulate_portfolio(monthly_investment: int = 4000, yearly_increase_of_monthly_investment: float = 0.02,
                       months_to_simulate: int = 120, expected_rate_of_return: float = 0.08,
                       initial_pf_value: int = 200000, inflation: float = 0.03) -> Tuple[pd.DataFrame, int, int]:
    """
    Simulate the return path of a monthly investment with a given expected rate of return.

    Parameters: monthly_investment (int): The initial monthly investment amount in EUR. Default is 4000.
    yearly_increase_of_monthly_investment (float): The annual percentage increase of the monthly investment. Default
    is 0.02. months_to_simulate (int): The number of months to simulate the investment over. Default is 120.
    expected_rate_of_return (float): The expected annual rate of return. Default is 0.08. initial_pf_value (int): The
    initial value of the portfolio in EUR. Default is 200000. inflation (float): The annual inflation rate. Default
    is 0.03.

    Returns: Tuple[pd.DataFrame, int, int]: A tuple containing the dataframe of the portfolio values, the final
    nominal value of the portfolio, and the final real value of the portfolio (adjusted for inflation).
    """
    df = pd.DataFrame(index=range(0, months_to_simulate + 1))
    for i in range(0, months_to_simulate + 1):
        if i == 0:
            df.loc[i, "PF value nominal"] = initial_pf_value
            df.loc[i, "PF value real"] = initial_pf_value
        else:
            df.loc[i, "PF value nominal"] = int(df.loc[i - 1, "PF value nominal"] * (1 + expected_rate_of_return / 12) + \
                                                monthly_investment * (
                                                        1 + yearly_increase_of_monthly_investment / 12) ** (
                                                        i - 1))
            df.loc[i, "PF value real"] = df.loc[i, "PF value nominal"] / (1 + inflation / 12) ** (i - 1)

    nominal_final_value = int(df.iloc[-1]["PF value nominal"])
    real_final_value = int(nominal_final_value / (1 + inflation) ** (months_to_simulate / 12))

    return df, nominal_final_value, real_final_value


def plot_portfolio(df: pd.DataFrame, title: str) -> None:
    """
    Plot the portfolio values.

    Parameters:
    df (pd.DataFrame): The dataframe containing the portfolio values.
    title (str): The title of the plot.

    Returns:
    None
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["PF value nominal"], label="PF value nominal")
    ax.plot(df["PF value real"], label="PF value real")
    fig.suptitle(title)
    plt.xlabel("Months")
    plt.ylabel("PF value")
    ax.grid()
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.legend()
    fig.tight_layout()
    plt.show()


def return_simulator(monthly_investment: int = 4000, yearly_increase_of_monthly_investment: float = 0.02,
                     months_to_simulate: int = 120, expected_rate_of_return: float = 0.08,
                     initial_pf_value: int = 200000, plot: bool = False, inflation: float = 0.03):
    df, nominal_final_value, real_final_value = simulate_portfolio(monthly_investment,
                                                                   yearly_increase_of_monthly_investment,
                                                                   months_to_simulate, expected_rate_of_return,
                                                                   initial_pf_value, inflation)

    if plot:
        title = f"Portfolio simulator based on monthly investments of {monthly_investment} EUR increasing " \
                f"by {yearly_increase_of_monthly_investment * 100} % per year\nsimulated over " \
                f"{months_to_simulate} months " \
                f"({round(months_to_simulate / 12, 1)} years) with an inflation of {round(inflation * 100, 1)} %\n" \
                f"and an expected rate of return of {round(expected_rate_of_return * 100, 1)} % per year. Initial " \
                f"PF value: {format(initial_pf_value, ',')} EUR."
        plot_portfolio(df, title)

    return nominal_final_value, real_final_value


if __name__ == '__main__':
    return_simulator(plot=True)
