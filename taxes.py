from dataclasses import dataclass
import math
from typing import Tuple

import helpers



@dataclass
class TaxBase:
    tax_exemption: float = 1000
    loss_pot: float = 0
    withheld_taxes: float = 0
    tax_rate: float = 0.26375

    def adjust_tax_exemption(self, adjustment: float) -> None:
        """
        Adjust the tax exemption by the given adjustment amount
        :param adjustment: amount by which the tax exemption is to be adjusted
        :return: None
        """
        if not isinstance(adjustment, (int, float)):
            raise ValueError("Adjustment must be a number.")
        if adjustment < -self.tax_exemption:
            raise ValueError("The adjustment may not lead to a negative tax exemption amount.")

        self.tax_exemption += adjustment

    def nr_shares_for_net_proceeds(self, target_net_proceeds: float,
                                   sale_price: float, historical_price: float) -> float:
        """
        Determine the number of shares that would have to be sold to satisfy the target net proceeds
        :param target_net_proceeds: the proceeds of the sale after taxes that is to be achieved
        :param sale_price: the price at which shares would be sold
        :param historical_price: the price at which the existing shares are assumed to have been bought
        :return: the number of shares that would have to be bought to satisfy the net proceeds
        """
        helpers.validate_positive_numbers([target_net_proceeds, sale_price, historical_price])

        if sale_price < historical_price:
            req_shares = target_net_proceeds / sale_price
        else:
            req_shares_without_taxation = target_net_proceeds / sale_price
            resulting_gain = req_shares_without_taxation * (sale_price - historical_price)
            if resulting_gain <= self.tax_exemption + self.loss_pot:
                req_shares = req_shares_without_taxation
            else:
                req_shares = (self.tax_exemption + self.loss_pot) / (sale_price - historical_price)
                net_proceeds = req_shares * sale_price
                remaining_net_proceeds = target_net_proceeds - net_proceeds
                additional_req_shares = remaining_net_proceeds / (sale_price - (sale_price - historical_price) * self.tax_rate)
                req_shares += additional_req_shares
                net_proceeds = req_shares * sale_price - max(0.0, (req_shares * (sale_price - historical_price) -
                                                                   self.loss_pot - self.tax_exemption) * self.tax_rate)
        taxable = self.determine_taxable(sale_price, historical_price, req_shares)
        taxes_abs = self.calculate_taxes(taxable, sale_price, req_shares)["Taxes absolute"]
        net_proceeds = req_shares * sale_price - taxes_abs

        if not math.isclose(net_proceeds, target_net_proceeds, rel_tol=1e-4):
            raise ValueError(f"net_proceeds: {net_proceeds} does not match target_net_proceeds: {target_net_proceeds}")

        if req_shares < 0 or not math.isfinite(req_shares):
            raise ValueError(f"invalid number of shares: {req_shares}")

        #
        # assert round(net_proceeds, 4) == round(target_net_proceeds, 4)

        return req_shares


    def determine_tax_exemption_and_loss_pot(self, sale_price: float, historical_price: float,
                                             nr_shares: float) -> Tuple[float, float, float]:
        """
        Determine the size of a tax exemption and a loss pot after a sale of securities
        :param sale_price: the price at which the securities are sold
        :param historical_price: the price at which the securities were originally bought
        :param nr_shares: the number of shares to be sold
        :return: tax_exemption, loss_pot after adjustment through the sale
        """
        # adjust taxes withheld
        taxable = self.determine_taxable(sale_price=sale_price, historical_price=historical_price, nr_shares=nr_shares)
        taxes = self.calculate_taxes(taxable=taxable, sale_price=sale_price, nr_shares=nr_shares)
        withheld_taxes = self.withheld_taxes + taxes["Taxes absolute"]

        gain_loss = nr_shares * (sale_price - historical_price)
        residual_gain_loss = max(0.0, gain_loss - self.loss_pot)

        # adjust loss pot
        loss_pot = max(0.0, self.loss_pot - gain_loss)

        # adjust tax exemption
        tax_exemption = max(0.0, self.tax_exemption - residual_gain_loss)

        return tax_exemption, loss_pot, withheld_taxes

    def determine_taxable(self, sale_price: float, historical_price: float, nr_shares: float) -> float:
        """
        Determine the amount that would be taxable given a hypothetical security sale
        :param sale_price: price at which the securities are sold
        :param historical_price: price at which the securities were bought
        :param nr_shares: number of shares being sold
        :return: the taxable amount
        """
        gain_loss = nr_shares * (sale_price - historical_price)
        residual_gain_loss = max(0.0, gain_loss - self.loss_pot)

        if residual_gain_loss > 0:
            taxable = max(0.0, residual_gain_loss - self.tax_exemption)
        else:
            taxable = 0

        return taxable

    def determine_net_proceeds(self, nr_shares: float, sale_price: float, historical_price: float) -> float:
        """
        Determine the net proceeds that would follow from selling securities
        :param nr_shares: the number of shares that would be sold
        :param sale_price: the price at which the securities would be sold
        :param historical_price: the price at which the securities are assumed to having been bought
        :return: the net proceeds that would result from the sale
        """

        taxable = self.determine_taxable(sale_price, historical_price, nr_shares)
        taxes_abs = self.calculate_taxes(taxable, sale_price, nr_shares)["Taxes absolute"]
        gross_proceeds = nr_shares * sale_price
        return gross_proceeds - taxes_abs

    def adjust_taxbase_via_sale(self, sale_price: float, historical_price: float, nr_shares: float) -> dict:
        """
        Adjust the tax exemption amount and/or loss pot based on a sale of securities and the respective gain/loss
        :param sale_price: price at which the securities are sold
        :param historical_price: price at which the securities were bought
        :param nr_shares: number of shares being sold
        :return: return dict of taxable amount, absolute and relative taxes
        """
        # adjust taxes withheld
        taxable = self.determine_taxable(sale_price=sale_price, historical_price=historical_price, nr_shares=nr_shares)
        taxes = self.calculate_taxes(taxable=taxable, sale_price=sale_price, nr_shares=nr_shares)
        self.withheld_taxes += taxes["Taxes absolute"]

        gain_loss = nr_shares * (sale_price - historical_price)
        residual_gain_loss = max(0.0, gain_loss - self.loss_pot)

        # adjust loss pot
        self.loss_pot = max(0.0, self.loss_pot - gain_loss)

        # adjust tax exemption
        self.tax_exemption = max(0.0, self.tax_exemption - residual_gain_loss)

        result = {"Taxes absolute": taxes["Taxes absolute"],
                  "Taxes relative": taxes["Taxes relative"],
                  "Taxable": taxable}

        return result

    def calculate_taxes(self, taxable: float, sale_price: float, nr_shares: float) -> dict:
        """
        Calculate the absolute and relative taxes for a securities' sale
        :param taxable: the amount that is to be taxed
        :param sale_price: price at which the securities are sold
        :param nr_shares: number of shares being sold
        :return: dictionary of absolute and relative taxes
        """
        taxes_abs = taxable * self.tax_rate
        try:
            taxes_rel = taxes_abs / (sale_price * nr_shares)
        except ZeroDivisionError:
            taxes_rel = 0

        return {"Taxes absolute": taxes_abs, "Taxes relative": taxes_rel}