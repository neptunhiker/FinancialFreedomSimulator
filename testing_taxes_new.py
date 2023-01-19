import unittest
from dataclasses import dataclass

import taxes


class TestTaxBase(unittest.TestCase):
    def setUp(self):
        self.tax_base = taxes.TaxBase()

    def test_adjust_tax_exemption_valid(self):
        self.tax_base.adjust_tax_exemption(100)
        self.assertEqual(self.tax_base.tax_exemption, 1100)

    def test_adjust_tax_exemption_invalid_not_number(self):
        with self.assertRaises(ValueError) as context:
            self.tax_base.adjust_tax_exemption("100")
        self.assertEqual(str(context.exception), "Adjustment must be a number.")

    def test_adjust_tax_exemption_invalid_negative(self):
        with self.assertRaises(ValueError) as context:
            self.tax_base.adjust_tax_exemption(-1100)
        self.assertEqual(str(context.exception), "The adjustment may not lead to a negative tax exemption amount.")


class TestShares(unittest.TestCase):

    def setUp(self) -> None:
        self.tax_base = taxes.TaxBase()
        self.tax_base_02 = taxes.TaxBase(tax_exemption=1000, loss_pot=200, withheld_taxes=0, tax_rate=0.26375)

    def test_nr_shares_for_net_proceeds_1(self):
        target_net_proceeds = 1000
        sale_price = 10
        historical_price = 5
        expected_output = 100
        self.assertEqual(self.tax_base.nr_shares_for_net_proceeds(target_net_proceeds, sale_price, historical_price),
                         expected_output)

    def test_nr_shares_for_net_proceeds_2(self):
        target_net_proceeds = 2000
        sale_price = 20
        historical_price = 10
        expected_output = 100
        self.assertEqual(self.tax_base.nr_shares_for_net_proceeds(target_net_proceeds, sale_price, historical_price),
                         expected_output)

    def test_nr_shares_for_net_proceeds_4(self):
        target_net_proceeds = -200
        sale_price = 20
        historical_price = 10
        self.assertRaises(ValueError, self.tax_base.nr_shares_for_net_proceeds, target_net_proceeds, sale_price,
                          historical_price)

    def test_required_nr_shares_high_net_proceeds(self):
        exp_nr_shares = 70.77935130196437
        calc_nr_shares = self.tax_base_02.nr_shares_for_net_proceeds(target_net_proceeds=10000,
                                                                     sale_price=150, historical_price=100)
        self.assertEqual(exp_nr_shares, calc_nr_shares)

    def test_required_nr_shares_medium_net_proceeds(self):
        exp_nr_shares = 50
        calc_nr_shares = self.tax_base_02.nr_shares_for_net_proceeds(target_net_proceeds=7157.125,
                                                                     sale_price=150, historical_price=100)
        self.assertEqual(exp_nr_shares, calc_nr_shares)

    def test_required_nr_shares_low_net_proceeds(self):
        exp_nr_shares = 13.333333333333334
        calc_nr_shares = self.tax_base_02.nr_shares_for_net_proceeds(target_net_proceeds=2000,
                                                                     sale_price=150, historical_price=100)
        self.assertEqual(exp_nr_shares, calc_nr_shares)
