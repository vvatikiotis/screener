import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import os
import sys
import argparse
from multiprocessing import Pool
from termcolor import colored
from tabulate import tabulate

# our own
import helpers
import supertrend
import bftb


#
#
#
def prepare_dataframe(data):
    df = pd.DataFrame(data)
    df["open_time"] = pd.to_datetime(arg=df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(arg=df["close_time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    # df["volume"] = df["volume"].astype(float)
    # df["quote_asset_volume"] = df["quote_asset_volume"].astype(float)
    # df["taker_buy_base_asset_volume"] = df["taker_buy_base_asset_volume"].astype(float)
    # df["taker_buy_quote_asset_volume"] = df["taker_buy_quote_asset_volume"].astype(
    #     float
    # )
    # df["number_of_trades"] = df["number_of_trades"].astype(int)

    return df


#
# tf_df_dict: {'1d': df1, '12h': df2,...}
#
def run_indicators(tf_df_dict):
    # print(tf_df_dict)
    st_dict = supertrend.run_supertrend(tf_df_dict)
    if "1d" in tf_df_dict:
        bftb_dict = bftb.run_btfd(tf_df_dict)
        inds = {"indicator1": bftb_dict, "indicator2": st_dict}
    else:
        inds = {"indicator1": st_dict}

    return inds


#
# symbol_timeframes_arr: ['BTCUSDT, ['12h', '4h', ...]]
# processes one symbol in all its timeframes
#
def run(symbol_timeframes_arr):
    [symbol, TFs] = symbol_timeframes_arr
    tf_df_dict = {}
    for timeframe in TFs:
        path = f"../symbols/csv/{symbol}_{timeframe}.csv"
        with open(path, "r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
            data = list(csv_dict_reader)

        df = prepare_dataframe(data)
        tf_df_dict[timeframe] = df

    results = run_indicators(tf_df_dict)

    return {"symbol": {"name": symbol}, **results}


def main():
    set_options()

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-s", "--symbol", nargs="+", help="Run for symbol or list of symbols"
    )
    PARSER.add_argument(
        "-t", "--timeframe", nargs="+", help="Run for timeframe or list of timeframes"
    )
    PARSER.add_argument(
        "-ts",
        "--time-series",
        help="Show last ts rows from timeseries instead of TA results",
    )

    dir = "../symbols/csv"
    filenames = [f for f in os.listdir(dir) if f.endswith(".csv")]
    filenames.sort()  # sort works in-place
    symbol_tfs_dict = helpers.group(filenames)
    for k, v in symbol_tfs_dict.items():
        v.sort(key=helpers.sort_lambda)
        symbol_tfs_dict[k] = v
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]

    parsed_arguments = PARSER.parse_args(sys.argv[1:])
    if parsed_arguments.symbol != None:
        symbol_tfs_arr = list(
            filter(lambda s: s[0] in parsed_arguments.symbol, symbol_tfs_arr)
        )
    if parsed_arguments.timeframe != None:
        tfs = parsed_arguments.timeframe
        symbol_tfs_arr = list(
            map(
                lambda s: [s[0], tfs],
                symbol_tfs_arr,
            )
        )

    # Enable it for many
    pool = Pool(8)
    results = pool.map(run, symbol_tfs_arr)
    pool.close()
    pool.join()
    output(results, parsed_arguments.time_series)


#
def output(results, last=10):
    if last == None:
        color_and_print(results)
    else:
        print_series(results, last)


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def color_and_print(results):

    # NOTE: to add an indicator, we MUST spacify an OUTPUT_ID and a tabulate function
    # inside the indicator module. The tabulate function MUST return:
    # [headers_dict, results_dict]
    def get_tabulate_func(id):
        if id == supertrend.OUTPUT_ID:
            return supertrend.tabulate
        elif id == bftb.OUTPUT_ID:
            return bftb.tabulate

    headers = []
    table = []

    for i, symbol_dict in enumerate(results):
        symbol = symbol_dict["symbol"]["name"]
        headers.append({"symbol": "Symbol"})
        table.append({"symbol": symbol})

        for key, value in symbol_dict.items():
            if key.startswith("indicator") == True:
                tabulate_func = get_tabulate_func(value["output_id"])
                [header, dict_] = tabulate_func(
                    symbol_dict[key]["series"],
                    symbol_dict[key]["screened"],
                    helpers.color,
                )
                headers[i] |= header  # |= Update headers[i] dict, in place
                table[i] |= dict_

    print(tabulate(table, headers=headers[0], tablefmt="fancy_grid"))


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_series(results, last):
    for i, symbol_dict in enumerate(results):  # iterate per symbol
        symbol = symbol_dict["symbol"]["name"]
        print(f"\n\n----------------- ", colored(symbol, "green"), " -----------------")

        for k, indicator in symbol_dict.items():  # iterate per indicator
            if k.startswith("indicator") == True:
                indicator_name = indicator["name"]
                indicator_series = indicator["series"]
                print(f"\n------------ {indicator_name} ------------")
                for tf, series in indicator_series.items():
                    print(f"Timeframe: {tf}")
                    print(series.tail(int(last)))


def set_options():
    pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    main()
