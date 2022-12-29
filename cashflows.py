from abc import ABC
import datetime
from dataclasses import dataclass, field



@dataclass
class Cashflow(ABC):

    amount: float
    description: str
    date: datetime.date
    direction: str = field(init=False, default="Cash inflow")


@dataclass
class Income(Cashflow):

    description: str = field(init=False, default="Income")


@dataclass
class OtherCashInflow(Cashflow):

    direction: str = field(init=False, default="Cash inflow")


@dataclass
class PrivatePension(Cashflow):

    description: str = field(init=False, default="Private Pension")


@dataclass
class Retirement(Cashflow):

    description: str = field(init=False, default="Retirement")




if __name__ == '__main__':

    ret = Retirement(2000, datetime.date(2023,1,23))
    pp = PrivatePension(4900, datetime.date(2072, 2, 23))
    inc = Income(4900, datetime.date(2072, 2, 23))
    other = OtherCashInflow(4900, "Inheritance", datetime.date(2045, 2, 1))

    print(ret)
    print(pp)
    print(inc)
    print(other)