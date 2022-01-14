import fs, { constants } from 'fs';
import { readFile, writeFile, access } from 'fs/promises';
import fetch from 'node-fetch';
import { Command } from 'commander/esm.mjs';
import chalk from 'chalk';
import Indicators from 'technicalindicators';

const SYMBOLS = [
  'BTCUSDT',
  // 'ETHUSDT',
  // 'SOLUSDT',
  // 'AVAXUSDT',
  // 'LUNAUSDT',
  // 'DOTUSDT',
  // 'MATICUSDT',
  // 'ADAUSDT',
  // 'ATOMUSDT',
  // 'ONEUSDT',
  // 'EGLDUSDT',
  // 'LINKUSDT',
  // 'FTMUSDT',
  // 'ONEUSDT',
  // 'NEARUSDT',
];
const RESOLUTIONS = [
  { interval: '1d', seedPeriod: 120 },
  { interval: '12h', seedPeriod: 240 },
  { interval: '6h', seedPeriod: 480 },
  { interval: '4h', seedPeriod: 720 },
];

const program = new Command();
async function fetchData(symbol, interval, limit) {
  const response = await fetch(
    'https://api.binance.com/api/v3/klines?' +
      new URLSearchParams({
        symbol,
        interval,
        limit,
      })
  );

  return await response.json();
}

//
//
//
async function writeJsonFile(data, flag, filename) {
  try {
    await writeFile(`./symbols/${filename}`, JSON.stringify(data), { flag });
  } catch (err) {
    console.error(`writeJsonFile() :: Error writing ./symbols/${filename}`);
    throw err;
  }
}

async function readJsonFile(filename) {
  try {
    const data = await readFile(`./symbols/${filename}`);
    return data;
  } catch (err) {
    console.error(`readJsonFile() :: Error reading ./symbols/${filename}`);
    throw err;
  }
}

//
// check integrity. All  symbol files have to be present in the checkpoint file
//
async function checkIntegrity() {}

//
// rebuilds checkpoints.json for defined SYMBOLS
//
const DATA_PATH = './symbols';
async function rebuildCheckpointsForSymbols(symbols, resolutions) {
  const checkpoints = [];
  // https://advancedweb.hu/how-to-use-async-functions-with-array-foreach-in-javascript/
  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;
        const { interval } = resol;

        let data;
        try {
          data = await readJsonFile(`${DATA_PATH}/${symbol}_${interval}.json`);
        } catch (err) {
          console.log(
            `rebuildCheckpoints() :: cannot find ${DATA_PATH}/${symbol}_${interval}.json`,
            err
          );
          throw err;
        }

        const checkpoint = Object.values(JSON.parse(data)).at(-1)[6];
        checkpoints.push({
          symbol,
          interval,
          checkpoint,
        });
      }, undefined);
    })
  );

  // write ticker close datetime
  console.log(
    'rebuildCheckpointsForSymbols() :: Found following checkpoints\n',
    checkpoints
  );
  writeJsonFile(checkpoints, 'w', 'checkpoints.json');

  return checkpoints;
}

//
// fetch all symbols
//
async function fetchSymbols(symbols, resolutions) {
  const i2secs = {
    '4h': 14400,
    '6h': 21600,
    '12h': 43200,
    '1d': 86400,
  };

  let checkpoints = [];
  try {
    const checkpointsJson = await readJsonFile(`checkpoints.json`);
    checkpoints = JSON.parse(checkpointsJson);
  } catch (err) {
    console.log('fetchSymbols() :: Cannot find checkpoints file', err);
  }
  let nextCheckpoints = [];

  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;

        const { interval, seedPeriod } = resol;
        let { checkpoint } = checkpoints.find((o) => {
          return o.symbol === symbol && interval === interval
            ? o.checkpoint
            : 0;
        }) || { checkpoint: -1 };

        const symbolFname = `${symbol}_${interval}.json`;
        let fetchedData;
        if (checkpoint === -1) {
          try {
            await access(`${DATA_PATH}/${symbolFname}`, constants.F_OK);
            const json = await readJsonFile(symbolFname);
            checkpoint = Object.values(JSON.parse(json)).at(-1)[6];
            console.log(
              `fetchSymbols() :: ${symbolFname} exists, getting last checkpoint from there.\n*** Please rerun to fetch latest data. ***\n`
            );
          } catch (err) {
            console.log(`fetchSymbols() :: Seeding ${symbol}, ${interval} ...`);
            fetchedData = await fetchData(symbol, interval, seedPeriod);
            checkpoint = `${Object.values(fetchedData).at(-1)[6]}`;
          }
        } else {
          const nowUTC = Date.parse(new Date());
          let diff;

          // checkpoint is close datetime. Binance API sets current bar's
          // close datetime in the future. So, nowUTC - checkpoint is negative
          const needUpdate = (diff = (nowUTC - checkpoint) / 1000) > 0;

          needUpdate &&
            console.log(`fetchSymbols() :: Updating ${symbol} ${interval} ...`);
          fetchedData = needUpdate
            ? await fetchData(
                symbol,
                interval,
                diff === nowUTC / 1000
                  ? seedPeriod
                  : Math.floor(diff / i2secs[interval]) + 1
              )
            : undefined;
        }

        if (fetchedData) {
          writeJsonFile(fetchedData, 'a', symbolFname);
        }

        nextCheckpoints.push({
          symbol,
          interval,
          checkpoint,
        });
      }, undefined);
    })
  );

  if (nextCheckpoints.length !== 0) {
    console.log(
      `fetchSymbols() :: Writing next checkpoints, ${nextCheckpoints.length} symbol checkpoints`
    );
    writeJsonFile(nextCheckpoints, 'w', 'checkpoints.json');
  }
}

function iterate(filterFn) {
  return async function (symbols = SYMBOLS, resolutions = RESOLUTIONS) {
    const result = await Promise.all(
      symbols.map(async (symbol) => {
        const tfs4symbol = await resolutions.reduce(
          async (memo, resolution) => {
            const { interval } = resolution;
            const json = await readJsonFile(`${symbol}_${interval}.json`);
            const data = JSON.parse(json);

            // ...await memo. Im using wrong tool for the work. Async makes things time consuming
            // Python? or just sync version?
            // https://stackoverflow.com/questions/41243468/javascript-array-reduce-with-async-await
            return { ...(await memo), [interval]: filterFn(data) };
          },
          {}
        );

        tfs4symbol.symbol = symbol;
        return tfs4symbol;
      })
    );

    console.log(result);
    return result;
  };
}

//
//
//
function SuperTrend(atrPeriod = 10, multiplier = 2) {
  return (data) => {
    const datetime = data.map((pt) => pt[6]);
    const src = data.map((pt) => (parseFloat(pt[2]) + parseFloat(pt[3])) / 2);
    const highs = data.map((pt) => pt[2]);
    const lows = data.map((pt) => pt[3]);
    const closes = data.map((pt) => pt[4]);
    const ATR = Indicators.atr({
      period: atrPeriod, // SuperTrend param
      high: highs,
      low: lows,
      close: closes,
    });

    // (H - L) /2
    let bot1 = src[atrPeriod] - multiplier * ATR[0];
    let top1 = src[atrPeriod] + multiplier * ATR[0];
    let trend = 1;
    let trend1 = 1;
    const band = ATR.map((atr, idx) => {
      const closeIdx = atrPeriod + idx;
      const close = closes[closeIdx];

      const bot = src[idx + atrPeriod] - multiplier * atr;
      bot1 = closes[closeIdx - 1] > bot1 ? Math.max(bot, bot1) : bot;

      const top = src[idx + atrPeriod] + multiplier * atr;
      top1 = closes[closeIdx - 1] < top1 ? Math.min(top, top1) : top;

      trend =
        trend === -1 && closes[closeIdx] > top1
          ? 1
          : trend === 1 && closes[closeIdx] < bot1
          ? -1
          : trend;

      const buySignal = trend === 1 && trend1 === -1;
      const sellSignal = trend === -1 && trend1 === 1;
      trend1 = trend;

      // console.log({
      //   date: new Date(datetime[idx + atrPeriod]).toLocaleString('en-US'),
      //   bot1,
      //   top1,
      //   trend,
      //   buySignal,
      //   sellSignal,
      // });
      return [
        new Date(datetime[idx + atrPeriod]).toLocaleString('en-US'),
        bot1,
        top1,
        trend,
        buySignal,
        sellSignal,
      ];
    });

    return band;
  };
}

function main() {
  program
    .option('-f --fetch-symbols', 'fetch symbols, in code')
    .option(
      '-b --rebuild-from-symbols',
      'rebuild checkpoints file from symbols data'
    )
    .option(
      '-s --run-supertrend <symbols...>',
      'run supertrend on fetched symbols'
    );

  program.parse(process.argv);

  const options = program.opts();

  if (options.fetchSymbols) fetchSymbols(SYMBOLS, RESOLUTIONS);
  if (options.rebuildFromSymbols)
    rebuildCheckpointsForSymbols(SYMBOLS, RESOLUTIONS);
  if (options.runSupertrend) {
    if (options.runSupertrend === 'all ') iterate(SuperTrend);
    else {
      const fnST = SuperTrend();
      iterate(fnST)(options.runSupertrend);
    }
  }
}

main();
// await fetchSymbols(SYMBOLS, RESOLUTIONS);
// await rebuildCheckpoints(SYMBOLS, RESOLUTIONS);

// const H12 = await SuperTrend('BTCUSDT', '12h', 250);

// [...Array(250 - ATR_PERIOD)].forEach((x, i) => {
//   console.log(i, H12[i][0], H12[i][1], H12[i][2], H12[i][3]);
// });
