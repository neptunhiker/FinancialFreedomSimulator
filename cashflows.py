import datetime
from dataclasses import dataclass



@dataclass
class Inflow:

    amount: float
    description: str
    date: datetime.date

    
@dataclass
class Outflow:

    amount: float
    description: str
    date: datetime.date
