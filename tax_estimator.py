from collections import OrderedDict
from dataclasses import dataclass, field
import numpy as np
from pprint import pprint
from typing import Tuple

import taxes





@dataclass
class Portfolio:
    fifo: OrderedDict = field(init=False)
    running_id: int = field(init=False)
    tax_base: taxes.TaxBase = taxes.TaxBase()
    initial_portfolio_value: float = 0
    initial_perc_gain: float = 0

    def __post_init__(self):
        self.fifo = OrderedDict()
        self.running_id = 0
        if self.initial_portfolio_value > 0:
            self.set_up()
        elif self.initial_portfolio_value < 0:
            raise ValueError("Initial portfolio value must be positive.")
        if self.initial_perc_gain <= -1:
            raise ValueError("The initial percentage gain for the portfolio may not be less or equal to -1.")

    def buy_shares(self, nr_shares: float, historical_price: float):
        self.fifo[self.running_id + 1] = [nr_shares, historical_price]
        self.running_id += 1

    def determine_available_shares(self) -> int:
        """Determine the number of available shares in the portfolio"""

        items = []
        for value in (zip(*list(self.fifo.values()))):
            items.append(sum(value))
        if bool(self.fifo):  # empty dictionaries evaluate to False in Python
            return items[0]
        else:
            return 0

    def determine_next_available_net_proceeds(self, sale_price: float):
        """
        Determine the next available net proceeds, i.e. the net proceeds of the first position in the FIFO stack
        :param sale_price: the price at which available securities could be sold
        :return: the amount of available net proceeds achievable by selling the first FIFO position entirely
        """
        if sale_price < 0:
            raise ValueError("The sale price must be larger than zero.")

        next_transaction_id = next(iter(self.fifo))
        next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
        historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
        taxable = self.tax_base.determine_taxable(sale_price, historical_price, next_available_nr_shares)
        taxes_abs = self.tax_base.calculate_taxes(taxable, sale_price, next_available_nr_shares)["Taxes absolute"]
        available_gross_proceeds = next_available_nr_shares * sale_price
        available_net_proceeds = available_gross_proceeds - taxes_abs

        return available_net_proceeds

    def determine_portfolio_value(self, share_price: float) -> float:
        """
        Determine the value of the portfolio based on a given share price
        :param share_price - the share price at which the portfolio value is to be determined
        :return the portfolio valuation
        """
        if share_price < 0:
            raise ValueError("To determine the value of the portfolio a positive share price value has to be given.")

        available_shares = self.determine_available_shares()
        return available_shares * share_price

    def sell_net_volume(self, target_net_proceeds: float, sale_price: float, partial_sale: bool = False) -> OrderedDict:
        """
        Sell a certain volume of the portfolio such that the net proceeds are equal to the target net proceeds
        :param target_net_proceeds: the target proceeds after taxes
        :param sale_price: the price at which shares are to be sold
        :param partial_sale: if False then the sales are reversed if the available volume is not sufficient to satisfy
            the target net
        :return: Ordered dict of shares to be sold (key) and their respective historical price and sale price (value)
        """
        # Check if the sale of the first element in the portfolios FIFO stack would be sufficient to satisfy the
        # target net proceeds by calculating the theoretical net proceeds
        fifo_copy = self.fifo.copy()  # used to restore the portfolio if net proceeds are insufficient to make the sale
        sale_transactions = OrderedDict()
        net_proceeds = 0
        while round(net_proceeds, 2) < round(target_net_proceeds, 2):
            try:
                available_net_proceeds = self.determine_next_available_net_proceeds(sale_price=sale_price)
                next_transaction_id = next(iter(self.fifo))
                next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
                historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
                if net_proceeds + available_net_proceeds >= target_net_proceeds:

                    shares_to_sell = self.tax_base.nr_shares_for_net_proceeds(target_net_proceeds, sale_price,
                                                                              historical_price)
                    net_proceeds += self.tax_base.determine_net_proceeds(shares_to_sell, sale_price, historical_price)
                    self.sell_shares(shares_to_sell, sale_price)
                else:
                    shares_to_sell = next_available_nr_shares
                    net_proceeds += self.tax_base.determine_net_proceeds(shares_to_sell, sale_price, historical_price)
                    self.sell_shares(nr_shares=shares_to_sell, sale_price=sale_price)

                sale_transactions[shares_to_sell] = [historical_price, sale_price]

            except StopIteration as err:
                print(err)
                if partial_sale:
                    break  # break out of the While loop
                else:
                    self.fifo = fifo_copy  # restore original portfolio
                    sale_transactions = OrderedDict()
                    break  # break out of the While loop

        return sale_transactions
        #
        # sale_transactions = OrderedDict()
        # tax_exemption = self.tax_base.tax_exemption
        # loss_pot = self.tax_base.loss_pot
        # withheld_taxes = self.tax_base.withheld_taxes
        # net_proceeds = 0
        # fifo_copy = self.fifo.copy()  # used to restore the portfolio if net proceeds are insufficient to make the sale
        # while round(net_proceeds, 2) < round(target_net_proceeds, 2):
        #     try:
        #         next_transaction_id = next(iter(self.fifo))
        #         next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
        #         historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
        #         available_gross_proceeds = next_available_nr_shares * sale_price
        #         taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, next_available_nr_shares)
        #         taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
        #         available_net_proceeds = available_gross_proceeds - taxes_dict["Taxes absolute"]
        #         if net_proceeds + available_net_proceeds >= target_net_proceeds:
        #             required_gross_sale = determine_gross_sale(target_net_proceeds=target_net_proceeds - net_proceeds,
        #                                                        sale_price=sale_price, historical_price=historical_price,
        #                                                        tax_rate=self.tax_base.tax_rate,
        #                                                        tax_exemption=tax_exemption)[1]
        #             transactions = self.sell_gross_volume(gross_proceeds=required_gross_sale, sale_price=sale_price)
        #             shares_to_be_sold, (historical_price, sale_price) = next(iter(transactions.items()))
        #             taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, shares_to_be_sold)
        #             taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, shares_to_be_sold)
        #             gross_proceeds = shares_to_be_sold * sale_price
        #             net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
        #             sale_transactions[shares_to_be_sold] = [historical_price, sale_price]
        #             self.tax_base.adjust_taxbase_via_sale(sale_price, historical_price, shares_to_be_sold)
        #             tax_exemption, loss_pot, withheld_taxes = self.tax_base.determine_tax_exemption_and_loss_pot(
        #                 sale_price, historical_price, shares_to_be_sold)
        #         else:
        #             self.sell_shares(nr_shares=next_available_nr_shares, sale_price=sale_price)
        #             taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price,
        #                                                              next_available_nr_shares)
        #             taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
        #             gross_proceeds = next_available_nr_shares * sale_price
        #             net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
        #             sale_transactions[next_available_nr_shares] = [historical_price, sale_price]
        #             self.tax_base.adjust_taxbase_via_sale(sale_price, historical_price, next_available_nr_shares)
        #             tax_exemption, loss_pot, withheld_taxes = self.tax_base.determine_tax_exemption_and_loss_pot(
        #                 sale_price, historical_price, next_available_nr_shares)
        #     except StopIteration as err:
        #         print(err)
        #         if partial_sale:
        #             break  # break out of the While loop
        #         else:
        #             self.fifo = fifo_copy  # restore original portfolio
        #             sale_transactions = OrderedDict()
        #             break  # break out of the While loop
        #
        # return sale_transactions

    # def sell_net_volume(self, target_net_proceeds: float, sale_price: float, partial_sale: bool = False) -> OrderedDict:
    #     """
    #     Sell a certain volume of the portfolio such that the net proceeds are equal to the target net proceeds
    #     :param target_net_proceeds: the target proceeds after taxes
    #     :param sale_price: the price at which shares are to be sold
    #     :param partial_sale: if False then the sales are reversed if the available volume is not sufficient to satisfy
    #         the target net
    #     :return: Ordered dict of shares to be sold (key) and their respective historical price and sale price (value)
    #     """
    #     sale_transactions = OrderedDict()
    #     tax_exemption = self.tax_base.tax_exemption
    #     loss_pot = self.tax_base.loss_pot
    #     withheld_taxes = self.tax_base.withheld_taxes
    #     net_proceeds = 0
    #     fifo_copy = self.fifo.copy()  # used to restore the portfolio if net proceeds are insufficient to make the sale
    #     while round(net_proceeds, 2) < round(target_net_proceeds, 2):
    #         try:
    #             next_transaction_id = next(iter(self.fifo))
    #             next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
    #             historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
    #             available_gross_proceeds = next_available_nr_shares * sale_price
    #             taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, next_available_nr_shares)
    #             taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
    #             available_net_proceeds = available_gross_proceeds - taxes_dict["Taxes absolute"]
    #             if net_proceeds + available_net_proceeds >= target_net_proceeds:
    #                 required_gross_sale = determine_gross_sale(target_net_proceeds=target_net_proceeds - net_proceeds,
    #                                                            sale_price=sale_price, historical_price=historical_price,
    #                                                            tax_rate=self.tax_base.tax_rate,
    #                                                            tax_exemption=tax_exemption)[1]
    #                 transactions = self.sell_gross_volume(gross_proceeds=required_gross_sale, sale_price=sale_price)
    #                 shares_to_be_sold, (historical_price, sale_price) = next(iter(transactions.items()))
    #                 taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, shares_to_be_sold)
    #                 taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, shares_to_be_sold)
    #                 gross_proceeds = shares_to_be_sold * sale_price
    #                 net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
    #                 sale_transactions[shares_to_be_sold] = [historical_price, sale_price]
    #                 self.tax_base.adjust_taxbase_via_sale(sale_price, historical_price, shares_to_be_sold)
    #                 tax_exemption, loss_pot, withheld_taxes = self.tax_base.determine_tax_exemption_and_loss_pot(
    #                     sale_price, historical_price, shares_to_be_sold)
    #             else:
    #                 self.sell_shares(nr_shares=next_available_nr_shares, sale_price=sale_price)
    #                 taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price,
    #                                                                  next_available_nr_shares)
    #                 taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
    #                 gross_proceeds = next_available_nr_shares * sale_price
    #                 net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
    #                 sale_transactions[next_available_nr_shares] = [historical_price, sale_price]
    #                 self.tax_base.adjust_taxbase_via_sale(sale_price, historical_price, next_available_nr_shares)
    #                 tax_exemption, loss_pot, withheld_taxes = self.tax_base.determine_tax_exemption_and_loss_pot(
    #                     sale_price, historical_price, next_available_nr_shares)
    #         except StopIteration as err:
    #             print(err)
    #             if partial_sale:
    #                 break  # break out of the While loop
    #             else:
    #                 self.fifo = fifo_copy  # restore original portfolio
    #                 sale_transactions = OrderedDict()
    #                 break  # break out of the While loop
    #
    #     return sale_transactions


    # def sell_net_volume(self, target_net_proceeds: float, sale_price: float, tax_rate: float = 0.26375,
    #                     tax_exemption: float = 0,
    #                     partial_sale: bool = False) -> OrderedDict:
    #     """
    #     Sell a certain volume of the portfolio such that the net proceeds are equal to the target net proceeds
    #     :param target_net_proceeds: the target proceeds after taxes
    #     :param sale_price: the price at which shares are to be sold
    #     :param tax_rate: the tax rate at which gains are taxed
    #     :param tax_exemption: the tax exemption amount that will not be taxed
    #     :param partial_sale: if False then the sales are reversed if the available volume is not sufficient to satisfy
    #         the target net
    #     :return: Ordered dict of shares to be sold (key) and their respective historical price and sale price (value)
    #     """
    #     sale_transactions = OrderedDict()
    #     net_proceeds = 0
    #     fifo_copy = self.fifo.copy()  # used to restore the portfolio if net proceeds are insufficient to make the sale
    #     while round(net_proceeds, 2) < round(target_net_proceeds, 2):
    #         try:
    #             next_transaction_id = next(iter(self.fifo))
    #             next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
    #             historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
    #             available_gross_proceeds = next_available_nr_shares * sale_price
    #             taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, next_available_nr_shares)
    #             taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
    #             available_net_proceeds = available_gross_proceeds - taxes_dict["Taxes absolute"]
    #             if net_proceeds + available_net_proceeds >= target_net_proceeds:
    #                 required_gross_sale = determine_gross_sale(target_net_proceeds=target_net_proceeds - net_proceeds,
    #                                                            sale_price=sale_price, historical_price=historical_price,
    #                                                            tax_rate=self.tax_base.tax_rate,
    #                                                            tax_exemption=self.tax_base.tax_exemption)[1]
    #                 transactions = self.sell_gross_volume(gross_proceeds=required_gross_sale, sale_price=sale_price)
    #                 shares_to_be_sold, (historical_price, sale_price) = next(iter(transactions.items()))
    #                 taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price, shares_to_be_sold)
    #                 taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, shares_to_be_sold)
    #                 gross_proceeds = shares_to_be_sold * sale_price
    #                 net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
    #                 sale_transactions[shares_to_be_sold] = [historical_price, sale_price]
    #             else:
    #                 self.sell_shares(nr_shares=next_available_nr_shares, sale_price=sale_price)
    #                 taxable_amount = self.tax_base.determine_taxable(sale_price, historical_price,
    #                                                                  next_available_nr_shares)
    #                 taxes_dict = self.tax_base.calculate_taxes(taxable_amount, sale_price, next_available_nr_shares)
    #                 gross_proceeds = next_available_nr_shares * sale_price
    #                 net_proceeds += gross_proceeds - taxes_dict["Taxes absolute"]
    #                 sale_transactions[next_available_nr_shares] = [historical_price, sale_price]
    #         except StopIteration as err:
    #             print(err)
    #             if partial_sale:
    #                 break  # break out of the While loop
    #             else:
    #                 self.fifo = fifo_copy  # restore original portfolio
    #                 sale_transactions = OrderedDict()
    #                 break  # break out of the While loop
    #
    #     return sale_transactions

    # def sell_net_volume(self, target_net_proceeds: float, sale_price: float, tax_rate: float = 0.26375,
    #                     tax_exemption: float = 0,
    #                     partial_sale: bool = False) -> OrderedDict:
    #     """
    #     Sell a certain volume of the portfolio such that the net proceeds are equal to the target net proceeds
    #     :param target_net_proceeds: the target proceeds after taxes
    #     :param sale_price: the price at which shares are to be sold
    #     :param tax_rate: the tax rate at which gains are taxed
    #     :param tax_exemption: the tax exemption amount that will not be taxed
    #     :param partial_sale: if False then the sales are reversed if the available volume is not sufficient to satisfy
    #         the target net
    #     :return: Ordered dict of shares to be sold (key) and their respective historical price and sale price (value)
    #     """
    #     sale_transactions = OrderedDict()
    #     net_proceeds = 0
    #     fifo_copy = self.fifo.copy()  # used to restore the portfolio if net proceeds are insufficient to make the sale
    #     while round(net_proceeds, 2) < round(target_net_proceeds, 2):
    #         try:
    #             next_transaction_id = next(iter(self.fifo))
    #             next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
    #             historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
    #             available_gross_proceeds = next_available_nr_shares * sale_price
    #             taxes = calculate_taxes(sale_price=sale_price, historical_price=historical_price,
    #                                     number_of_shares=next_available_nr_shares, tax_rate=tax_rate,
    #                                     tax_exemption=tax_exemption)[0]
    #             available_net_proceeds = available_gross_proceeds - taxes
    #             if net_proceeds + available_net_proceeds >= target_net_proceeds:
    #                 required_gross_sale = determine_gross_sale(target_net_proceeds=target_net_proceeds - net_proceeds,
    #                                                            sale_price=sale_price, historical_price=historical_price,
    #                                                            tax_rate=tax_rate, tax_exemption=tax_exemption)[1]
    #                 transactions = self.sell_gross_volume(gross_proceeds=required_gross_sale, sale_price=sale_price)
    #                 shares_to_be_sold, (historical_price, sale_price) = next(iter(transactions.items()))
    #                 taxes = calculate_taxes(sale_price=sale_price, historical_price=historical_price,
    #                                         number_of_shares=shares_to_be_sold, tax_rate=tax_rate,
    #                                         tax_exemption=tax_exemption)[0]
    #                 gross_proceeds = shares_to_be_sold * sale_price
    #                 net_proceeds += gross_proceeds - taxes
    #                 sale_transactions[shares_to_be_sold] = [historical_price, sale_price]
    #
    #             else:
    #                 self.sell_shares(nr_shares=next_available_nr_shares, sale_price=sale_price)
    #                 taxes = calculate_taxes(sale_price=sale_price, historical_price=historical_price,
    #                                         number_of_shares=next_available_nr_shares, tax_rate=tax_rate,
    #                                         tax_exemption=tax_exemption)[0]
    #                 gross_proceeds = next_available_nr_shares * sale_price
    #                 net_proceeds += gross_proceeds - taxes
    #                 sale_transactions[next_available_nr_shares] = [historical_price, sale_price]
    #         except StopIteration as err:
    #             print(err)
    #             if partial_sale:
    #                 break  # break out of the While loop
    #             else:
    #                 self.fifo = fifo_copy  # restore original portfolio
    #                 sale_transactions = OrderedDict()
    #                 break  # break out of the While loop
    #
    #     return sale_transactions


    def sell_gross_volume(self, gross_proceeds: float, sale_price: float) -> OrderedDict:
        """
        Sell a certain volume of the portfolio

        param gross_proceeds: the volume to be sold
        param sale_price: the price at which the shares are sold
        return: Ordered dictionary of shares to be sold (key) and their respective historical price (value)
        """
        shares_to_be_sold = gross_proceeds / sale_price
        return self.sell_shares(nr_shares=shares_to_be_sold, sale_price=sale_price)

    def sell_shares(self, nr_shares: float, sale_price: float) -> OrderedDict:
        """
        Sell a certain number of shares from the portfolio (FIFO procedure)
        :param nr_shares: the number of shares to be sold
        :param sale_price: the price at which the shares are sold
        :return: Ordered dictionary of shares to be sold (key) and their respective historical and sale price (value)
        """
        shares_sold = 0
        transactions = OrderedDict()
        while shares_sold < nr_shares:
            next_transaction_id = next(iter(self.fifo))
            next_available_nr_shares = self.fifo[next_transaction_id][0]  # next "nr of shares" in portfolio
            historical_price = self.fifo[next_transaction_id][1]  # next "historical price" in portfolio
            if shares_sold + next_available_nr_shares > nr_shares:
                shares_to_be_sold = nr_shares - shares_sold
                self.fifo[next_transaction_id] = [next_available_nr_shares - shares_to_be_sold, historical_price]
                shares_sold += shares_to_be_sold
            else:
                shares_to_be_sold, historical_price = self.fifo.popitem(last=False)[1]
                shares_sold += shares_to_be_sold
            transactions[shares_to_be_sold] = [historical_price, sale_price]

        for key, value in transactions.items():
            shares = key
            historical_price = value[0]
            self.tax_base.adjust_taxbase_via_sale(sale_price, historical_price, shares)

        return transactions

    def set_up(self) -> None:
        """
        Set up the portfolio with a given gain based on assumed arbitrary share price of 100
        :return: None
        """
        arbitrary_share_price = 100
        nr_shares = self.initial_portfolio_value / arbitrary_share_price
        historical_price = arbitrary_share_price / (1 + self.initial_perc_gain)
        self.buy_shares(nr_shares=nr_shares, historical_price=historical_price)
        return None

    def show_positions(self):
        pprint(self.fifo)





def determine_gross_transaction_volume(transactions: OrderedDict) -> float:
    """
    Determine the gross volume based on an Ordered dict of sale transactions
    :param transactions: Ordered dict of shares to be sold (key) and respective historical price and sale price (value)
    :return: gross volume
    """
    gross_volume = 0
    for key, value in transactions.items():
        gross_volume += key * value[1]
    return gross_volume


def determine_gross_sale(target_net_proceeds: float, sale_price: float, historical_price: float,
                         tax_rate: float = 0.26375, tax_exemption: float = 0) -> Tuple[float, float]:
    """
    Determine the necessary gross sale to achieve the desired net proceeds
    :param target_net_proceeds: the cash amount that is intended to be achieved after taxes
    :param sale_price: the price at which the funds are sold
    :param historical_price: the price at which the funds were bought originally
    :param tax_rate: the tax rate at which gains are assumed to be taxed
    :param tax_exemption: the amount of the gains that are exempt from being taxed
    :return: (number_of_shares_to_be_sold, gross_sale_volume)
    """
    if sale_price < historical_price:
        number_of_shares_to_be_sold = target_net_proceeds / sale_price
    else:
        nr_shares_without_tax_exemption = target_net_proceeds / (
                    sale_price - (sale_price - historical_price) * tax_rate)
        gain_without_tax_exemption = nr_shares_without_tax_exemption * (sale_price - historical_price)
        if tax_exemption >= gain_without_tax_exemption:
            number_of_shares_to_be_sold = target_net_proceeds / sale_price
        else:
            number_of_shares_to_be_sold = (target_net_proceeds - tax_exemption * tax_rate) / \
                                          (sale_price - (sale_price - historical_price) * tax_rate)

    gross_sale_volume = number_of_shares_to_be_sold * sale_price

    # return 1, 2
    return number_of_shares_to_be_sold, gross_sale_volume


def determine_disinvestment_gain_or_loss(transactions: OrderedDict) -> float:
    """
    Determine the gain or loss made based on given transactions
    :param transactions: Ordered dict of shares to be sold (key) and respective historical price and sale price (value)
    :return: the absolute gain (positive) or loss of the transactions
    """

    gain = 0
    for key, value in transactions.items():
        gain += key * (value[1] - value[0])

    return gain


def main():
    months_to_simulate = 600
    months_of_contributions = 120
    expected_return = 0.08
    monthly_contributions = 4000
    living_expenses = 1000
    current_share_price = 100
    pf = Portfolio()

    for i in range(months_of_contributions):
        pf.buy_shares(nr_shares=monthly_contributions / current_share_price, historical_price=current_share_price)
        current_share_price *= (1 + expected_return / 12)

    pf.show_positions()

    total_taxes = 0
    transaction_volume = 0
    for i in range(months_of_contributions + 1, months_to_simulate + 1):
        shares_to_sell = living_expenses / current_share_price
        transactions = pf.sell_shares(nr_shares=shares_to_sell)
        total_taxes += taxes_for_transactions(transactions=transactions, share_price=current_share_price)[0]
        transaction_volume += shares_to_sell * current_share_price
        current_share_price *= (1 + expected_return / 12)

    print(total_taxes, transaction_volume, round(total_taxes / transaction_volume, 2))
    pf.show_positions()


if __name__ == '__main__':
    main()
