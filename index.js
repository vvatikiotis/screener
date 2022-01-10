import fs, { constants } from 'fs';
import { readFile, writeFile, access } from 'fs/promises';
import fetch from 'node-fetch';
import chalk from 'chalk';
import Indicators from 'technicalindicators';

const ATR_PERIOD = 10;
const ATR_MULTIPLIER = 2;

const SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'SOLUSDT',
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

const mod = (a, n) => ((a % n) + n) % n;

//
//
//
async function writeJsonFile(data, flag, filename) {
  try {
    await writeFile(`./symbols/${filename}`, JSON.stringify(data), { flag });
  } catch (err) {
    console.error(`Error writing ./symbols/${filename}`);
    throw err;
  }
}

async function readJsonFile(filename) {
  try {
    const data = await readFile(`./symbols/${filename}`);
    return data;
  } catch (err) {
    console.error(`Error reading ./symbols/${filename}`);
    throw err;
  }
}

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
// check integrity. All  symbol files have to be present in the checkpoint file
//
async function checkIntegrity() {}

//
// rebuilds checkpoints.json from existing symbol data files
//
const DATA_PATH = './symbols';
async function rebuildCheckpoints(symbols, resolutions) {
  const checkpoints = [];
  // https://advancedweb.hu/how-to-use-async-functions-with-array-foreach-in-javascript/
  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;
        const { interval } = resol;

        const data = readJsonFile(`${DATA_PATH}/${symbol}_${interval}.json`);

        const checkpoint = Object.values(JSON.parse(data)).at(-1)[6];
        checkpoints.push({
          symbol,
          interval,
          checkpoint,
        });
      }, undefined);
    })
  );

  // write ticker datetime checkpoints
  console.log('Found following checkpoints\n', checkpoints);
  writeJsonFile(checkpoints, 'w', 'checkpoints.json');
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

  let existCheckpoints = true;
  let checkpointsJson = [];

  try {
    checkpointsJson = await readJsonFile(`checkpoints.json`);
  } catch (err) {
    console.log('Cannot find checkpoints file', err);
    existCheckpoints = false;
  }
  const checkpoints = existCheckpoints ? JSON.parse(checkpointsJson) : [];
  let nextCheckpoints = [];

  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;
        let doneSymbolSeed = true;
        const { interval, seedPeriod } = resol;

        // check if symbol data exists
        try {
          await access(
            `${DATA_PATH}/${symbol}_${interval}.json`,
            constants.F_OK
          );
        } catch (err) {
          doneSymbolSeed = false;
        }

        let data;
        let checkpoint;
        if (!existCheckpoints || !doneSymbolSeed) {
          console.log(`Seeding ${symbol}, ${interval} ...`);
          data = await fetchData(symbol, interval, seedPeriod);
          checkpoint = `${Object.values(data).at(-1)[6]}`;
        } else {
          const nowUTC = Date.parse(new Date());
          const o = checkpoints.find((o) => {
            return o.symbol === symbol && interval === interval
              ? o.checkpoint
              : 0;
          });
          let diff;
          checkpoint = o.checkpoint;
          // checkpoint is close datetime. Binance API sets current bar's
          // close datetime in the future. So, nowUTC - checkpoint is negative
          const needUpdate = (diff = (nowUTC - checkpoint) / 1000) > 0;
          // console.log({
          //   symbol,
          //   interval,
          //   needUpdate,
          //   diff,
          //   nowUTC,
          //   checkpoint,
          //   interval,

          //   period:
          //     diff === nowUTC / 1000
          //       ? seedPeriod
          //       : Math.floor(diff / i2secs[interval]) + 1,
          // });

          needUpdate && console.log(`Updating ${symbol} ${interval} ...`);
          data = needUpdate
            ? await fetchData(
                symbol,
                interval,
                diff === nowUTC / 1000
                  ? seedPeriod
                  : Math.floor(diff / i2secs[interval]) + 1
              )
            : undefined;
        }

        if (data) {
          writeJsonFile(data, 'a', `${symbol}_${interval}.json`);
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
      `Writing next checkpoints, ${nextCheckpoints.length} symbol checkpoints`
    );
    writeJsonFile(nextCheckpoints, 'w', 'checkpoints.json');
  }
}

//
//
//
async function SuperTrend(
  data,
  atrPeriod = ATR_PERIOD,
  multiplier = ATR_MULTIPLIER
) {
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
}

await fetchSymbols(SYMBOLS, RESOLUTIONS);
// await rebuildCheckpoints(SYMBOLS, RESOLUTIONS);

// const H12 = await SuperTrend('BTCUSDT', '12h', 250);

// [...Array(250 - ATR_PERIOD)].forEach((x, i) => {
//   console.log(i, H12[i][0], H12[i][1], H12[i][2], H12[i][3]);
// });
