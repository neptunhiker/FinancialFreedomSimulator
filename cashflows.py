from dataclasses import dataclass


@dataclass
class Inflow:

    amount: float
    description: str

    
@dataclass
class Outflow:

    amount: float
    description: str
