const readline = require('readline');
const tickers = require('./tickers');

let rows = tickers.length < 20 ? tickers.length : 20; 
let columnwidth = 40; 
let count = 0;
let startTime = Date.now();
let randchars = ['*','%','$','&','@','!','^','~','+','?','/','|','<','>'];

console.clear();

function drawScreen() {
  for (i = 0; i < tickers.length; i++) {
    let k = Math.floor(i / rows);
    let y = i - (rows * k);
    
    readline.cursorTo(process.stdout, k * columnwidth, y);
    
    let dashes = "-".repeat(columnwidth - tickers[i].length - 1);
    process.stdout.write(`\x1b[33m${tickers[i]}${dashes}\x1b[0m`);
  }
};

drawScreen();

readline.cursorTo(process.stdout, 0, rows + 5);

setInterval(grab, 500);

async function grab() {
    const tickerString = tickers.join(",");
    
    try {
        const res = await fetch(`https://generic709.herokuapp.com/stockc/${tickerString}`);
        const allData = await res.json();

        for (const singleticker of tickers) {
            const quote = allData[singleticker];
            if (!quote || typeof quote.price !== 'number') continue;

            let displayBid = (quote.bid > 0) ? quote.bid.toFixed(2) : "-.-";
            let displayAsk = (quote.ask > 0) ? quote.ask.toFixed(2) : "-.-";
            let displayPrice = quote.price.toFixed(2);
            
            let k = Math.floor(tickers.indexOf(singleticker) / rows);
            let y = tickers.indexOf(singleticker) - (rows * k);
            let x = (k * columnwidth) + 7;

            readline.cursorTo(process.stdout, x, y);

            let randomChar = randchars[Math.floor(Math.random() * 10)];
            
            process.stdout.write(
                `\x1b[37m${displayPrice}${randomChar} \x1b[36mB:${displayBid} \x1b[35mA:${displayAsk}\x1b[0m  ` 
            );
        }

        if (count % 50 == 0 && count > 1) { 
            let statsRow = rows + 2;

            readline.cursorTo(process.stdout, 0, statsRow);
            process.stdout.write(`Packets: ${count}  `);
            
            let elapsedSecs = (Date.now() - startTime) / 1000;
            let seconds = parseInt((elapsedSecs % 60), 10);
            seconds = seconds < 10 ? `0${seconds}` : seconds;
            
            readline.cursorTo(process.stdout, 0, statsRow + 1);
            process.stdout.write(`Time: ${(Math.floor(elapsedSecs/60))}:${seconds}  `);
            
            readline.cursorTo(process.stdout, 0, statsRow + 2);
            process.stdout.write(`Speed: ${(count / elapsedSecs).toFixed(1)} req/s   `);
        }
        count++;

    } catch (e) {
        return;
    }
}
