import investpy
import pandas as pd
import pprint


def main():

    isins_symbols = [['DE0005493092', 'na'], ['DE000ETFL441', 'ELF1'], ['IE00B52VJ196', 'IUSK'], ['IE00BFMXXD54', 'VUA1'],
     ['IE00BMVB5R75', 'V80A'], ['LU0274211480', 'XDAX'], ['IE00BZ02LR44', 'XZWO']]
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


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)

    main()