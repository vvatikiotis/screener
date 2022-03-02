import numpy as np
import pandas as pd
import csv
import pandas_ta as ta
import matplotlib.pyplot as plt
import os
from multiprocessing import Pool
from termcolor import colored
from tabulate import tabulate


def bang_for_buck(df, symbol, timeframe):
    amount = 10000
    days_in_year = 365
    l = len(df)
    lookback = 200 if l >= 200 else l
    bang_4_buck = (
        (amount / df["close"])
        * ta.sma(
            ta.true_range(high=df["high"], low=df["low"], close=df["close"]),
            length=lookback,
        )
        / 100
    )

    highB4B = bang_4_buck.tail(days_in_year).max()
    lowB4B = bang_4_buck.tail(days_in_year).min()

    result = {
        "symbol": symbol,
        "results": {
            "BtfB": bang_4_buck.tail(1).to_string(index=False),
            "BtfB_High": highB4B,
            "BtfB_Low": lowB4B,
        },
    }

    return result


def SuperTrend(df_dict, length=10, multiplier=2):
    def screen_supertrend(tf_df_dict, symbol):
        # several predicates can be defined
        def predicate1(df):
            last = -1
            one_b4_last = -2
            two_b4_last = -3
            three_b4_last = -4
            direction = lambda pos: df.iloc[pos][
                1
            ]  # 1 = position of direction in the series

            #
            if direction(one_b4_last) == -1 and direction(last) == 1:
                return "Buy (0)"

            if (
                direction(two_b4_last) == -1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-1)"

            if (
                direction(three_b4_last) == -1
                and direction(two_b4_last) == 1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-2)"

            if direction(one_b4_last) == 1 and direction(last) == -1:
                return "Sell (0)"
            if (
                direction(two_b4_last) == 1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-1)"
            if (
                direction(three_b4_last) == 1
                and direction(two_b4_last) == -1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-2)"

            return False

        results = {}
        results["symbol"] = symbol
        for tf in tf_df_dict:
            p = predicate1(tf_df_dict[tf])
            results[tf] = p
            # if symbol == "BTCUSDT" and tf == "4h":
            #     print(tf_df_dict[tf].tail(10))

        return results

    symbol_tfs_dict = {}
    for tf in df_dict:
        df = df_dict[tf]
        symbol_tfs_dict[tf] = ta.supertrend(
            df["high"], df["low"], df["close"], length, multiplier
        )

    return [symbol_tfs_dict, screen_supertrend]

    #  TODO: Pine supertrend is optimised! Do it!
    #
    # def _supertrend(df):
    #     src = (df["open"] + df["close"]) / 2
    #     atr = ta.atr(df["high"], df["low"], df["close"], length=atr_period, talib=True)

    #     bot = src - multiplier * atr
    #     print(bot)
    #     bot1 = bot.shift(1) if (not bot.shift(1).isnull()) else bot
    #     # bot = max(bot, bot1) if df["close"].shift(1) > bot1 else bot
    #     # //up1 = nz(up[1], up)
    #     # up := close[1] > up1 ? math.max(up, up1) : up

    # return _supertrend


def prepare_dataframe(data):
    df = pd.DataFrame(data)
    df["open_time"] = pd.to_datetime(arg=df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(arg=df["close_time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["quote_asset_volume"] = df["quote_asset_volume"].astype(float)
    df["taker_buy_base_asset_volume"] = df["taker_buy_base_asset_volume"].astype(float)
    df["taker_buy_quote_asset_volume"] = df["taker_buy_quote_asset_volume"].astype(
        float
    )
    df["number_of_trades"] = df["number_of_trades"].astype(int)

    return df


#
#
# results = array of dicts
def color_and_print(results):
    def color(t):
        red = "\033[31m"
        green = "\033[32m"
        blue = "\033[34m"
        reset = "\033[39m"
        utterances = t.split()

        if "Sell" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x.startswith("Sell")]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = red + utterances[i] + reset

        if "Buy" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x.startswith("Buy")]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = green + utterances[i] + reset

        # join the list back into a string and print
        return " ".join(utterances)

    headers = dict([(x, x) for x in list(results[0].keys())])
    for i, entry in enumerate(results):
        for k, v in list(entry.items()):
            if v == False:
                results[i][k] = ""
            elif v.startswith("Buy") or v.startswith("Sell"):
                results[i][k] = color(v)

    print(tabulate(results, headers=headers, tablefmt="fancy_grid"))


#
# tf_dfs_dict: { '12h': supertrend_df, '4h': supertrend_df}
#
def parse(tf_df_dict, symbol, parseFn=None, filter=True):
    p = parseFn(tf_df_dict, symbol)
    # print(p)
    return p


#
# symbol_timeframes_arr: ['BTCUSDT, ['12h', '4h', ...]]
# processes one symbol in all its timeframes
#
def run(symbol_timeframes_arr):
    [symbol, TFs] = symbol_timeframes_arr
    process_dict = {}
    for timeframe in TFs:
        path = f"../symbols/csv/{symbol}_{timeframe}.csv"
        with open(path, "r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
            data = list(csv_dict_reader)

        df = prepare_dataframe(data)
        process_dict[timeframe] = df

    btfb = bang_for_buck(process_dict["1d"], symbol, "1d")
    # print(btfb)
    [symbol_tfs_dict, screen_supertrend] = SuperTrend(process_dict)
    supertrend_output_10_2 = parse(symbol_tfs_dict, symbol, parseFn=screen_supertrend)

    return supertrend_output_10_2


def main():
    set_options()

    ###################################
    # helpers
    def group(strings):
        groups = {}
        for s in map(lambda s: s.split(".")[0], strings):
            prefix, remainder = s.split("_")
            groups.setdefault(prefix, []).append(remainder)
        return groups

    def sort_lambda(v):
        SORT_ORDER = {"1w": 0, "3d": 1, "1d": 2, "12h": 3, "6h": 4, "4h": 5, "1h": 6}
        return SORT_ORDER[v]

    # END helpers
    ###################################

    dir = "../symbols/csv"
    filenames = [f for f in os.listdir(dir) if f.endswith(".csv")]
    filenames.sort()  # sort works in-place
    symbol_tfs_dict = group(filenames)
    for k, v in symbol_tfs_dict.items():
        v.sort(key=sort_lambda)
        symbol_tfs_dict[k] = v
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]

    # Enable it for many
    pool = Pool(8)
    res = pool.map(run, symbol_tfs_arr)
    pool.close()
    pool.join()
    color_and_print(res)


def set_options():
    pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    main()
