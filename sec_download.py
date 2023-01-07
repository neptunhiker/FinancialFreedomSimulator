import math

import investpy
import pandas as pd
import pprint
import datetime
import matplotlib.pyplot as plt


def main():
    df_dev_world = vanguard_from_excel(file_name="FTSE Developed World UCITS ETF - (USD) Accumulating.xlsx")
    df_em = vanguard_from_excel(file_name="FTSE Emerging Markets UCITS ETF - (USD) Accumulating.xlsx")

    for df in [df_em, df_dev_world]:
        df.sort_index(inplace=True)
        df["pct ch"] = df["Marktpreis (EUR)"].pct_change()
        df["cum diff"] = df["Marktpreis (EUR)"].diff().cumsum()
        df["ytd"] = df["cum diff"] / df["Marktpreis (EUR)"].iloc[0]

    total = pd.concat([df_em, df_dev_world], axis=1)
    print(total)
    print(df_em["pct ch"].std() * math.sqrt(252))
    print(df_dev_world["pct ch"].std() * math.sqrt(252))
    print(df_em["pct ch"].corr(df_dev_world["pct ch"]))


def etf_download():
    isins_symbols = [['DE0005493092', 'na'], ['DE000ETFL441', 'ELF1'], ['IE00B52VJ196', 'IUSK'],
                     ['IE00BFMXXD54', 'VUA1'],
                     ['IE00BMVB5R75', 'V80A'], ['LU0274211480', 'XDAX'], ['IE00BZ02LR44', 'XZWO'],
                     ["IE00BK5BQV03", "VGVF"]]
    securities = dict()
    for item in isins_symbols:
        isin = item[0]
        symbol = item[1]
        if symbol != "na":
            try:
                df = investpy.etfs.get_etfs(country="Germany")
                temp_df = df[df["isin"] == isin]
                temp_df = temp_df[temp_df["stock_exchange"] == "Xetra"]
                full_name = temp_df["full_name"].item()
                securities[isin] = full_name
            except ValueError as err:
                try:
                    etf = investpy.etfs.search_etfs(by="symbol", value=symbol)
                    full_name = etf[etf["country"] == "germany"]["name"].item()
                    securities[isin] = full_name
                except RuntimeError as err:
                    securities[isin] = "unknown"
        else:
            securities[isin] = "unknown"

    pprint.pprint(securities)

    # df = investpy.etfs.get_etfs(country="Germany")
    # df = df[df["full_name"].str.startswith("iShares MSCI World")]


def vanguard_from_excel(file_name: str) -> pd.DataFrame:
    """
    Read securities data downloaded from Vanguard website

    file_name: str - name of the excel file
    """
    df = pd.read_excel(file_name)
    df["Daten"] = df["Daten"].apply(lambda x: convert_to_date(x))
    df["NAV (USD)"] = df["NAV (USD)"].apply(lambda x: convert_to_price(x, currency="USD"))
    df["Marktpreis (EUR)"] = df["Marktpreis (EUR)"].apply(lambda x: convert_to_price(x, currency="EUR"))
    df.rename(columns={"Daten": "Datum"}, inplace=True)
    df.set_index("Datum", inplace=True)

    return df


def convert_to_price(string: str, currency: str):
    if currency.lower() == "usd":
        old_text = " $"
    elif currency.lower() == "eur":
        old_text = " €"
    try:
        string = string.replace(",", ".")
        string = string.replace(old_text, "")
    except AttributeError as err:
        return string

    return float(string)


def convert_to_date(string):
    if "März" in string:
        string = string.replace("März", "Mar.")
    if "Mai" in string:
        string = string.replace("Mai", "May.")
    if "Juni" in string:
        string = string.replace("Juni", "Jun.")
    if "Juli" in string:
        string = string.replace("Juli", "Jul.")
    if "Sept" in string:
        string = string.replace("Sept", "Sep")
    if "Okt" in string:
        string = string.replace("Okt", "Oct")
    if "Dez" in string:
        string = string.replace("Dez", "Dec")

    return datetime.datetime.strptime(string, "%d. %b. %Y")


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.expand_frame_repr', False)

    # main()
    # etf_download()
