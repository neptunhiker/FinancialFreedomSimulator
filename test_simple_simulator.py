import matplotlib
import pandas as pd
import unittest

import simple_simulator
import unittest


class TestSimulatePortfolio(unittest.TestCase):

    def test_simulate_portfolio(self):
        # test the function with default input
        df, nominal_final_value, real_final_value = simple_simulator.simulate_portfolio()

        # check if the output is the expected
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIsInstance(nominal_final_value, int)
        self.assertIsInstance(real_final_value, int)

if __name__ == '__main__':
    unittest.main()
