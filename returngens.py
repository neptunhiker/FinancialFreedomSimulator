import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


class ReturnGenerator(ABC):
    """Represents a Return Generator class."""

    @abstractmethod
    def generate_monthly_returns(self, n: int) -> pd.Series:
        """Generate n number of returns"""
        pass


@dataclass
class GBM(ReturnGenerator):
    """A return generator that generates returns based on the Geometric Brownian Motion."""

    yearly_return: float
    yearly_vola: float
    _monthly_vola: float = field(init=False)
    _yearly_vola: float = field(init=False)

    def __post_init__(self):
        self._monthly_vola = self.yearly_vola / math.sqrt(12)
        self._monthly_drift = self.yearly_return / 12 - 0.5 * self._monthly_vola**2

    def generate_monthly_returns(self, n: int) -> pd.Series:
        returns = []
        for i in range(n):
            returns.append(self._monthly_drift + random.normalvariate(mu=0, sigma=self._monthly_vola))

        return pd.Series(data=returns, index=range(n), name="Monthly returns")


@dataclass
class StudenT(ReturnGenerator):
    """A return generator that generates returns based on the Student T distribution."""

    yearly_return: float
    yearly_vola: float
    degrees_of_freedom: int
    _monthly_vola: float = field(init=False)
    _yearly_vola: float = field(init=False)

    def __post_init__(self):
        self._monthly_vola = self.yearly_vola / math.sqrt(12)
        self._monthly_drift = self.yearly_return / 12 - 0.5 * self._monthly_vola**2

    def generate_monthly_returns(self, n: int) -> pd.Series:
        returns = []
        for i in range(n):
            returns.append(self._monthly_drift + np.random.standard_t(self.degrees_of_freedom, 1)[0] * self._monthly_vola)

        return pd.Series(data=returns, index=range(n), name="Monthly returns")


class TestAlgo:

    def run(self, n: int, return_generator: ReturnGenerator):
        returns = return_generator.generate_monthly_returns(n)
        print(returns.describe())


if __name__ == '__main__':
    gbm = GBM(0.07, 0.2)
    student_t = StudenT(0.07, 0.2, 20)

    app = TestAlgo()
    print("-" * 50)
    app.run(n=10000, return_generator=gbm)
    print("-" * 50)
    app.run(n=10000, return_generator=student_t)

