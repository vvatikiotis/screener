#!/bin/bash

shopt -s extglob nullglob

for f in ../symbols/*.json
do
    if [ "$f" != "../symbols/checkpoints.json" ]
    then
        echo $f

        # bash expansion magic
        filenameWext=${f##*/}
        filename=${filenameWext%%.*}
        echo $filename
        cat $f | jq -r '["open_time","open","high","low","close","volume","close_time","quote_asset_volume","number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"], .[]|@csv' > ../symbols/csv/${filename}.csv
    fi
done

