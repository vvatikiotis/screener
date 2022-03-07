#!/bin/bash

shopt -s extglob nullglob

DIR=$HOME/devel/trading/screener

for f in $DIR/symbols/*.json
do
    if [ "$f" != $DIR/symbols/checkpoints.json ]
    then
        # bash expansion magic
        filenameWext=${f##*/}
        filename=${filenameWext%%.*}
        echo "Will convert: $f  ->  $DIR/symbols/csv/$filename.csv"
        cat $f | jq -r '["open_time","open","high","low","close","volume","close_time","quote_asset_volume","number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"], .[]|@csv' > $DIR/symbols/csv/${filename}.csv
    fi
done

