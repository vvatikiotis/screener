#
#  Using this TA lib. Depends on TA-Lib (brew it)
# https://github.com/twopirllc/pandas-ta
#

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
from datetime import datetime

# our own
import helpers
import supertrend
import bftb
import from_bar_diffs
import prices_diff
import tr_atr
import inside_bar
import engulfing_pattern
import historical_vol

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
def run_indicators(tf_df_dict, type, timeframe=None, parameter=None):
    indicator_results = {}
    indicator2 = None

    if timeframe == None:
        if (
            type == "supertrend"
            or type == "from_diff"
            or type == "price_diff"
            or type == "tr_atr"
            or type == "bear_engulf"
            or type == "bull_engulf"
            or type == "hist_vol"
        ):
            indicator1 = bftb.run_btfd(tf_df_dict)
        # Inside bar has no meaning in timeframes other that 1w and 3d
        if type == "supertrend":
            indicator2 = supertrend.run_supertrend(tf_df_dict)
        # all the other analysis need a tf spec
        if type == "from_diff":
            indicator2 = from_bar_diffs.run_from_bar_diffs(
                tf_df_dict, from_bar=parameter
            )
        if type == "price_diff":
            indicator2 = prices_diff.run_prices_diff(tf_df_dict, last_nth=parameter)
        if type == "tr_atr":
            indicator2 = tr_atr.run_tr_atr(tf_df_dict, from_bar=parameter)
        if type == "bear_engulf":
            indicator2 = engulfing_pattern.run_engulfing_pattern(
                tf_df_dict, type="bear"
            )
        if type == "bull_engulf":
            indicator2 = engulfing_pattern.run_engulfing_pattern(
                tf_df_dict, type="bull"
            )
        if type == "hist_vol":
            indicator2 = historical_vol.run_historical_vol(
                tf_df_dict, from_bar=parameter
            )

    else:
        tf = timeframe[0]
        if tf == "1d":
            indicator1 = bftb.run_btfd(tf_df_dict)
            if type == "supertrend":
                indicator2 = supertrend.run_supertrend(tf_df_dict)
            if type == "bear_engulf":
                indicator2 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bear"
                )
            if type == "bull_engulf":
                indicator2 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bull"
                )
            # all the other analysis need a tf spec
            if type == "from_diff":
                indicator2 = from_bar_diffs.run_from_bar_diffs(
                    tf_df_dict, from_bar=parameter
                )
            if type == "price_diff":
                indicator2 = prices_diff.run_prices_diff(tf_df_dict, last_nth=parameter)
            if type == "tr_atr":
                indicator2 = tr_atr.run_tr_atr(tf_df_dict, from_bar=parameter)
            if type == "hist_vol":
                indicator2 = historical_vol.run_historical_vol(
                    tf_df_dict, from_bar=parameter
                )
        else:
            if type == "supertrend":
                indicator1 = supertrend.run_supertrend(tf_df_dict)
            if type == "bear_engulf":
                indicator1 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bear"
                )
            if type == "bull_engulf":
                indicator1 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bull"
                )
            # all the other analysis need a tf spec
            if type == "from_diff":
                indicator1 = from_bar_diffs.run_from_bar_diffs(
                    tf_df_dict, tf, from_bar=parameter
                )
            if type == "price_diff":
                indicator1 = prices_diff.run_prices_diff(
                    tf_df_dict, tf, last_nth=parameter
                )
            if type == "tr_atr":
                indicator1 = tr_atr.run_tr_atr(tf_df_dict, tf, from_bar=parameter)

    indicator_results = {"indicator1": indicator1}
    if indicator2 != None:
        indicator_results["indicator2"] = indicator2

    return indicator_results


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
            data = list(
                helpers.dict_filter(
                    csv_dict_reader,
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "close_time",
                )
            )

        df = prepare_dataframe(data)
        tf_df_dict[timeframe] = df

    # use_analysis, use_timeframe, use_paramter  global vars per process
    results = run_indicators(tf_df_dict, use_analysis, use_timeframe, use_parameter)

    return {"symbol": {"name": symbol}, **results}


def pool_initializer(analysis, timeframe, parameter):
    global use_analysis
    global use_timeframe
    global use_parameter

    use_analysis = analysis
    use_timeframe = timeframe
    use_parameter = parameter


def main():
    set_options()

    CSV_DIR = "../symbols/csv"
    filenames = [f for f in os.listdir(CSV_DIR) if f.endswith(".csv")]
    filenames.sort()  # sort works in-place
    symbol_tfs_dict = helpers.group(filenames)
    for k, v in symbol_tfs_dict.items():
        v.sort(key=helpers.sort_lambda)
        symbol_tfs_dict[k] = v
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]

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
    PARSER.add_argument(
        "-sort",
        "--sort-series",
        choices=["asc", "desc"],
        help="WIP Sort last column",
    )
    PARSER.add_argument(
        "-u",
        "--use-analysis",
        default="supertrend",
        choices=[
            "supertrend",
            "from_diff",
            "price_diff",
            "tr_atr",
            "bear_engulf",
            "bull_engulf",
            "hist_vol",
        ],
        help="Type of analysis",
    )
    PARSER.add_argument(
        "-p",
        "--parameter",
        help="Specify lookback window size (integer) for from_diff, price_diff, tr_atr and hist_vol analysis",
    )

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

    if (
        parsed_arguments.timeframe != None
        and len(parsed_arguments.timeframe) > 1
        and parsed_arguments.use_analysis != "supertrend"
        and parsed_arguments.use_analysis != "bear_engulf"
        and parsed_arguments.use_analysis != "bull_engulf"
    ):
        print(
            f"This analysis supports only 1 timeframe. Will use only {parsed_arguments.timeframe[0]}, the rest are ignored"
        )

    parameter = 10
    if parsed_arguments.parameter != None:
        if (
            parsed_arguments.use_analysis != "from_diff"
            and parsed_arguments.use_analysis != "price_diff"
            and parsed_arguments.use_analysis != "tr_atr"
            and parsed_arguments.use_analysis != "hist_vol"
        ):
            print(
                f"Only from_diff, price_diff, tr_atr, hist_vol support -p. Will run {parsed_arguments.use_analysis} with default arguments"
            )
        else:
            parameter = int(parsed_arguments.parameter)

    # Enable it for many
    pool = Pool(
        processes=8,
        initializer=pool_initializer,
        initargs=(
            parsed_arguments.use_analysis,
            parsed_arguments.timeframe,
            parameter,
        ),
    )
    results = pool.map(run, symbol_tfs_arr)
    pool.close()
    pool.join()
    output(results, parsed_arguments)


# NOTE: to add an indicator, we MUST spacify an OUTPUT_ID and a tabulate function
# inside the indicator module. The tabulate function MUST return:
# [headers_dict, results_dict]
def get_tabulate_func(module_id):
    if module_id == supertrend.OUTPUT_ID:
        return supertrend.tabulate
    elif module_id == bftb.OUTPUT_ID:
        return bftb.tabulate
    elif module_id == from_bar_diffs.OUTPUT_ID:
        return from_bar_diffs.tabulate
    elif module_id == tr_atr.OUTPUT_ID:
        return tr_atr.tabulate
    elif module_id == prices_diff.OUTPUT_ID:
        return prices_diff.tabulate
    elif module_id == inside_bar.OUTPUT_ID:
        return inside_bar.tabulate
    elif module_id == engulfing_pattern.OUTPUT_ID:
        return engulfing_pattern.tabulate
    elif module_id == historical_vol.OUTPUT_ID:
        return historical_vol.tabulate


#
def output(results, args):
    last_rows_count = args.time_series
    sort = args.sort_series
    analysis = args.use_analysis

    if last_rows_count == None:
        print_tabular(results, sort, analysis=analysis)
    elif last_rows_count != None:
        print_series(results, last_rows_count, sort)


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_tabular(results, sort=None, analysis=None):
    headers = []
    table = []
    titles = []
    descs = []

    for i, symbol_dict in enumerate(results):
        symbol = symbol_dict["symbol"]["name"]
        headers.append({"symbol": "Symbol"})
        table.append({"symbol": symbol})
        titles.append([])
        descs.append([])

        for key, value in symbol_dict.items():
            if key.startswith("indicator") == True:
                if i == 0:
                    titles[i].append(f"--------- {value['name']} ---------")
                    descs[i].append(f"----- {value['desc']} -----")
                tabulate_func = get_tabulate_func(value["output_id"])
                [header, dict_] = tabulate_func(
                    symbol_dict[key]["series"], symbol_dict[key]["screened"], analysis
                )
                headers[i] |= header  # |= Update headers[i] dict, in place
                table[i] |= dict_

    today = datetime.now()
    print(f"--------- {colored(today, 'yellow')} ---------\n")
    print(*titles[0])
    print(tabulate(table, headers=headers[0], tablefmt="fancy_grid"))
    print("\n")
    print(*[f"{x}\n" for x in descs[0]])


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_series(results, last, sort=None):
    today = datetime.now()
    print(f"--------- {colored(today, 'yellow')} ---------\n")

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
