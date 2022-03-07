#!/bin/bash

shopt -s extglob nullglob

#DIR=$HOME/devel/trading/screener
# find current path
DIR=`pwd`
#echo "==> $DIR"

# add path in Array
IFS='\/' read -ra THE_PATH <<< "$DIR"
for i in "${THE_PATH[@]}"; do
  echo "$i"
done

# validate that the last folder , that we are in, is screener project
ArrLength=${#THE_PATH[@]}
LastDir=${THE_PATH[$ArrLength-1]}
#echo "===> ${LastDir}"

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

