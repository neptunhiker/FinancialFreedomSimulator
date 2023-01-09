from collections import OrderedDict
import unittest

import tax_estimator


class TestSelling(unittest.TestCase):

    def setUp(self) -> None:
        self.pf = tax_estimator.Portfolio()
        self.pf.buy_shares(nr_shares=50, historical_price=100)
        self.pf.buy_shares(nr_shares=30, historical_price=120)
        self.pf.buy_shares(nr_shares=10, historical_price=100)

    def test_selling_shares(self):
        sale_price = 100
        exp_transactions = OrderedDict()
        exp_transactions[50] = [100, sale_price]
        exp_transactions[20] = [120, sale_price]
        calc_transactions = self.pf.sell_shares(nr_shares=70, sale_price=sale_price)
        self.assertEqual(exp_transactions, calc_transactions)

    def test_selling_gross_volume(self):
        sale_price = 150
        exp_transactions = OrderedDict()
        exp_transactions[50] = [100, sale_price]
        exp_transactions[20] = [120, sale_price]
        calc_transactions = self.pf.sell_gross_volume(gross_proceeds=10500, sale_price=sale_price)
        self.assertEqual(exp_transactions, calc_transactions)

    def test_selling_net_volume(self):
        sale_price = 150
        exp_transactions = OrderedDict()
        exp_transactions[50] = [100, sale_price]
        exp_transactions[18.707482993197278] = [120, sale_price]
        calc_transactions = self.pf.sell_net_volume(target_net_proceeds=10000, sale_price=sale_price, tax_rate=0.1)
        self.assertEqual(exp_transactions, calc_transactions)

    def test_selling_net_volume_insufficient_without_partial_sale(self):
        pf_before = self.pf.fifo.copy()
        self.pf.sell_net_volume(target_net_proceeds=999999, sale_price=150, tax_rate=0.1, partial_sale=False)
        self.assertEqual(pf_before, self.pf.fifo)

    def test_selling_net_volume_insufficient_with_partial_sale(self):
        sale_price = 150
        exp_transactions = OrderedDict()
        exp_transactions[50] = [100, sale_price]
        exp_transactions[30] = [120, sale_price]
        exp_transactions[10] = [100, sale_price]
        calc_transactions = self.pf.sell_net_volume(target_net_proceeds=999999, sale_price=sale_price, tax_rate=0.1,
                                                    partial_sale=True)
        self.assertEqual(exp_transactions, calc_transactions)


class TestCapitalGainsTaxes(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_positive_taxes(self):
        taxes_abs = 10.549999999999999
        taxes_rel = 0.04395833333333333
        expected_taxes = (taxes_abs, taxes_rel)
        calculated_taxes = tax_estimator.calculate_taxes(sale_price=120, historical_price=100, number_of_shares=2)
        self.assertEqual(expected_taxes, calculated_taxes)

    def test_positive_taxes_with_low_tax_exemption(self):
        taxes_abs = 1  # (gain - tax_exemption) * tax_rate = (40 - 30) * 0.1
        taxes_rel = 0.004166666666666667
        expected_taxes = (taxes_abs, taxes_rel)
        calculated_taxes = tax_estimator.calculate_taxes(sale_price=120, historical_price=100, number_of_shares=2,
                                                         tax_rate=0.1, tax_exemption=30)
        self.assertEqual(expected_taxes, calculated_taxes)

    def test_positive_taxes_with_high_tax_exemption(self):
        taxes_abs = 0
        taxes_rel = 0
        expected_taxes = (taxes_abs, taxes_rel)
        calculated_taxes = tax_estimator.calculate_taxes(sale_price=120, historical_price=100, number_of_shares=2,
                                                         tax_rate=0.1, tax_exemption=801)
        self.assertEqual(expected_taxes, calculated_taxes)

    def test_positive_taxes_with_negative_tax_exemption(self):
        self.assertRaises(ValueError, tax_estimator.calculate_taxes, sale_price=120, historical_price=100,
                          number_of_shares=2, tax_exemption=-100)

    def test_negative_taxes(self):
        taxes_abs = 0
        taxes_rel = 0
        expected_taxes = (taxes_abs, taxes_rel)
        calculated_taxes = tax_estimator.calculate_taxes(sale_price=80, historical_price=100, number_of_shares=2)
        self.assertEqual(expected_taxes, calculated_taxes)


class TestTaxesForTransactions(unittest.TestCase):

    def setUp(self) -> None:
        self.transactions = OrderedDict()
        self.transactions = OrderedDict()
        self.transactions[30] = 100
        self.transactions[50] = 120
        self.transactions[4] = 100

    def test_transactions_high_sale_price(self) -> None:
        sale_price = 150
        transaction_volume = 12600  # 4500 + 7500 + 600
        exp_taxes_abs = 844  # 395.625 + 395.625 + 52.75
        exp_taxes_rel = 0.06698412698412698  # 844 / 12600
        calc_taxes_abs, calc_taxes_rel = tax_estimator.taxes_for_transactions(transactions=self.transactions,
                                                                              share_price=sale_price)
        self.assertEqual((exp_taxes_abs, exp_taxes_rel), (calc_taxes_abs, calc_taxes_rel))

    def test_transactions_medium_sale_price(self) -> None:
        sale_price = 120
        transaction_volume = 10080  # 3600 + 6000 + 480
        exp_taxes_abs = 179.35  # 158.25 + 0 + 21.099999999999998
        exp_taxes_rel = 0.017792658730158728  # 179.35 / 10080
        calc_taxes_abs, calc_taxes_rel = tax_estimator.taxes_for_transactions(transactions=self.transactions,
                                                                              share_price=sale_price)
        self.assertEqual((exp_taxes_abs, exp_taxes_rel), (calc_taxes_abs, calc_taxes_rel))

    def test_transactions_low_sale_price(self) -> None:
        sale_price = 80
        exp_taxes_abs = 0
        exp_taxes_rel = 0
        calc_taxes_abs, calc_taxes_rel = tax_estimator.taxes_for_transactions(transactions=self.transactions,
                                                                              share_price=sale_price)
        self.assertEqual((exp_taxes_abs, exp_taxes_rel), (calc_taxes_abs, calc_taxes_rel))


class TestDetermineGrossSale(unittest.TestCase):

    def test_determine_gross_sale_with_taxes(self):
        target_net_proceeds = 3000
        exp_nr_shares = 25.423728813559322
        exp_transaction_volume = 3050.8474576271187
        calc_nr_shares, calc_gross_sale_volume = tax_estimator.determine_gross_sale(
            target_net_proceeds=target_net_proceeds, sale_price=120, historical_price=100, tax_rate=0.1)
        self.assertEqual((exp_nr_shares, exp_transaction_volume), (calc_nr_shares, calc_gross_sale_volume))

    def test_determine_gross_sale_no_taxes(self):
        target_net_proceeds = 3000
        exp_nr_shares = 60
        exp_transaction_volume = 3000
        calc_nr_shares, calc_gross_sale_volume = tax_estimator.determine_gross_sale(
            target_net_proceeds=target_net_proceeds, sale_price=50, historical_price=100, tax_rate=0.1)
        self.assertEqual((exp_nr_shares, exp_transaction_volume), (calc_nr_shares, calc_gross_sale_volume))


