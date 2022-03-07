#!/bin/bash

shopt -s extglob nullglob

# find current path
DIR=`pwd`
#echo "==> $DIR"

# add path in Array
IFS='\/' read -ra THE_PATH <<< "$DIR"

# validate that the last folder , that we are in, is screener project
ArrLength=${#THE_PATH[@]}
LastDir=${THE_PATH[$ArrLength-1]}

if [ "$LastDir" != "screener" ]
  then 
    echo " Please run script from screener dir "
    exit 1
  fi


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

