import numpy as np
import pandas as pd
import csv
import pandas_ta as ta
import matplotlib.pyplot as plt
import os
from multiprocessing import Pool
from termcolor import colored


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
    log = "%s %s: " % (symbol, timeframe)
    log += (
        "Bang for the Back: "
        + colored(bang_4_buck.tail(1).to_string(index=False), "cyan")
        + ", "
    )

    highB4B = bang_4_buck.tail(days_in_year).max()
    lowB4B = bang_4_buck.tail(days_in_year).min()
    log += "BtfB high: %s, " % (highB4B)
    log += "BtfB low: %s" % (lowB4B)
    print(log)

    return [bang_4_buck, highB4B, lowB4B]


def SuperTrend(df_dict, length=10, multiplier=2):
    def filter_supertrend(tf_df_dict, symbol):
        # several predicates can be defined
        def predicate1(df):
            last = -1
            one_b4_last = -2
            two_b4_last = -3
            three_b4_last = -4
            direction = lambda pos: df.iloc[pos][
                1
            ]  # 1 = position of direction in the series

            if (
                direction(one_b4_last) == -1
                and direction(last) == 1
                or direction(two_b4_last) == -1
                and direction(one_b4_last) == 1
                and direction(last) == 1
                or direction(three_b4_last) == -1
                and direction(two_b4_last) == 1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "buy"
            if (
                direction(one_b4_last) == 1
                and direction(last) == -1
                or direction(two_b4_last) == 1
                and direction(one_b4_last) == -1
                and direction(last) == -1
                or direction(three_b4_last) == 1
                and direction(two_b4_last) == -1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "sell"

            return False

        results = ""
        for tf in tf_df_dict:
            if p := predicate1(tf_df_dict[tf]):
                # print(f'{symbol} {tf} {p}')
                if results == "":
                    results += f"{symbol}: {tf} {p}, "
                else:
                    results += f"{tf} {p}, "

        return results

    symbol_tfs_dict = {}
    for tf in df_dict:
        df = df_dict[tf]
        symbol_tfs_dict[tf] = ta.supertrend(
            df["high"], df["low"], df["close"], length, multiplier
        )

    return [symbol_tfs_dict, filter_supertrend]

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


def color_and_print(text):
    def color(t):
        red = "\033[31m"
        green = "\033[32m"
        blue = "\033[34m"
        reset = "\033[39m"
        utterances = t.split()

        if "sell" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x == "sell"]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = red + utterances[i] + reset

        if "buy" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x == "buy"]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = green + utterances[i] + reset

        # join the list back into a string and print
        return " ".join(utterances)

    if text != "":
        print(color(text[:-2]))


#
# tf_dfs_dict: { '12h': supertrend_df, '4h': supertrend_df}
#
def output(tf_df_dict, symbol, filterFn=None, filter=True):
    results = filterFn(tf_df_dict, symbol)
    color_and_print(results)
    return results


#
# symbol_timeframes_arr: ['BTCUSDT, ['12h', '4h', ...]]
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

    # bang_for_buck(df, symbol, timeframe)
    [symbol_tfs_dict, filter_supertrend] = SuperTrend(process_dict)
    output(symbol_tfs_dict, symbol, filterFn=filter_supertrend)


def main():
    set_options()

    dir = "../symbols/csv"
    filenames = [f for f in sorted(os.listdir(dir)) if f.endswith(".csv")]
    symbol_tfs_dict = group(filenames)
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]
    # print(symbol_tfs_arr)

    # Enable it for many
    pool = Pool(8)
    pool.map(run, symbol_tfs_arr)
    pool.close()
    # res = pool.join()
    # color_and_print(res)


def set_options():
    pd.set_option("display.max_rows", None)


def group(strings):
    groups = {}
    for s in map(lambda s: s.split(".")[0], strings):
        prefix, remainder = s.split("_")
        groups.setdefault(prefix, []).append(remainder)
    return groups


if __name__ == "__main__":
    main()
