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
        cat $f | jq -r '["Open_time","Open","High","Low","Close","Volume","Close_time","Quote_asset_volume","Number_of_trades","Taker_buy_base_asset_volume","Taker_buy_quote_asset_volume","Ignore"], .[]|@csv' > ../symbols/csv/${filename}.csv
    fi
done

