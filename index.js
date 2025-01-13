// require('dotenv').config();
// const Web3 = require('web3');
// const fs = require('fs');

// // Initialize Web3 with the Infura provider
// const web3 = new Web3(`https://mainnet.infura.io/v3/${process.env.INFURA_PROJECT_ID}`);

// const pairAddress = '0x3041cbd36888becc7bbcbc0045e3b1f144466f5f'; // USDT-USDC pair address on Uniswap V2
// const pairABI = [
//   {
//     "inputs": [],
//     "name": "getReserves",
//     "outputs": [
//       {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
//       {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
//       {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
//     ],
//     "stateMutability": "view",
//     "type": "function"
//   },
//   {
//     "inputs": [],
//     "name": "token0",
//     "outputs": [{"internalType": "address", "name": "", "type": "address"}],
//     "stateMutability": "view",
//     "type": "function"
//   },
//   {
//     "inputs": [],
//     "name": "token1",
//     "outputs": [{"internalType": "address", "name": "", "type": "address"}],
//     "stateMutability": "view",
//     "type": "function"
//   },
//   {
//     "inputs": [],
//     "name": "totalSupply",
//     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
//     "stateMutability": "view",
//     "type": "function"
//   },
//   {
//     "inputs": [{"internalType": "address", "name": "", "type": "address"}],
//     "name": "balanceOf",
//     "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
//     "stateMutability": "view",
//     "type": "function"
//   }
// ];
// const pairContract = new web3.eth.Contract(pairABI, pairAddress);

// async function getPoolDetails() {
//   const [reserves, token0, token1, totalSupply] = await Promise.all([
//     pairContract.methods.getReserves().call(),
//     pairContract.methods.token0().call(),
//     pairContract.methods.token1().call(),
//     pairContract.methods.totalSupply().call()
//   ]);
//   return { reserves, token0, token1, totalSupply };
// }

// async function getLpTokenBalances(lpAddress) {
//   const balance = await pairContract.methods.balanceOf(lpAddress).call();
//   return balance;
// }

// function listenForEvents() {
//   pairContract.events.Mint({
//     filter: {},
//     fromBlock: 0
//   })
//   .on('data', function(event){
//     console.log(event);
//   })
//   .on('changed', function(event){
//     // remove event from local database
//   })
//   .on('error', console.error);
// }

// async function saveDataToJson(data) {
//   fs.writeFileSync('liquidity_data.json', JSON.stringify(data, null, 2));
// }

// async function monitorPool() {
//   setInterval(async () => {
//     const poolDetails = await getPoolDetails();
//     const decimals = 6; // USDT and USDC have 6 decimal places
//     const reserve0 = poolDetails.reserves._reserve0 / (10 ** decimals);
//     const reserve1 = poolDetails.reserves._reserve1 / (10 ** decimals);
//     const totalSupply = poolDetails.totalSupply / (10 ** 18);

//     console.log(`Reserve 0 (USDT): ${reserve0}`);
//     console.log(`Reserve 1 (USDC): ${reserve1}`);
//     console.log(`Total Supply: ${totalSupply}`);
//   }, 60000); // Check every 60 seconds
// }

// (async () => {
//   const poolDetails = await getPoolDetails();
//   const liquidityData = { pairAddress, ...poolDetails };

//   await saveDataToJson(liquidityData);
//   console.log('Data saved to liquidity_data.json');

//   // Listen for events on the USDT-USDC pair
//   listenForEvents();

//   // Monitor the pool
//   monitorPool();
// })();


require('dotenv').config();
const Web3 = require('web3');
const fs = require('fs');
const BigNumber = require('bignumber.js');

// Initialize Web3 with the Infura provider
const web3 = new Web3(`https://mainnet.infura.io/v3/${process.env.INFURA_PROJECT_ID}`);
const pairAddress = '0x3041cbd36888becc7bbcbc0045e3b1f144466f5f'; // USDT-USDC pair address on Uniswap V2
const pairABI = [
    {"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Burn","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1In","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount0Out","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1Out","type":"uint256"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"Swap","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint112","name":"reserve0","type":"uint112"},{"indexed":false,"internalType":"uint112","name":"reserve1","type":"uint112"}],"name":"Sync","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},
    {"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"MINIMUM_LIQUIDITY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"_token0","type":"address"},{"internalType":"address","name":"_token1","type":"address"}],"name":"initialize","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"kLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"mint","outputs":[{"internalType":"uint256","name":"liquidity","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"price0CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"price1CumulativeLast","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"}],"name":"skim","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":false,"inputs":[{"internalType":"uint256","name":"amount0Out","type":"uint256"},{"internalType":"uint256","name":"amount1Out","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[],"name":"sync","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}
  ]; // Your ABI here

const pairContract = new web3.eth.Contract(pairABI, pairAddress);

async function getPoolDetails() {
    const [reserves, token0, token1, totalSupply] = await Promise.all([
        pairContract.methods.getReserves().call(),
        pairContract.methods.token0().call(),
        pairContract.methods.token1().call(),
        pairContract.methods.totalSupply().call()
    ]);
    return { reserves, token0, token1, totalSupply };
}

async function getLpTokenBalances(lpAddress) {
    const balance = await pairContract.methods.balanceOf(lpAddress).call();
    return new BigNumber(balance);
}

async function getAllLiquidityProviders() {
    console.log('Fetching all liquidity providers...');
    const liquidityProviders = new Set();
    const blockNumber = await web3.eth.getBlockNumber();
    console.log(`Current block number: ${blockNumber}`);

    const batchSize = 100000; // Increased batch size
    for (let i = 0; i <= blockNumber; i += batchSize) {
        try {
            console.log(`Fetching events from block ${i} to ${i + batchSize - 1}...`);
            const events = await pairContract.getPastEvents('Transfer', { fromBlock: i, toBlock: i + batchSize - 1 });
            events.forEach(event => {
                const lpAddress = event.returnValues.to;
                liquidityProviders.add(lpAddress);
            });
            console.log(`Fetched ${events.length} events from block ${i} to ${i + batchSize - 1}`);
            await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limiting
        } catch (error) {
            console.error('Error fetching events:', error);
            await new Promise(resolve => setTimeout(resolve, 5000)); // Wait before retrying
            i -= batchSize; // Retry the same batch
        }
    }

    console.log('Fetching LP token balances for all liquidity providers...');
    const providersWithBalances = await Promise.allSettled([...liquidityProviders].map(async lpAddress => {
        const balance = await getLpTokenBalances(lpAddress);
        return { lpAddress, balance: balance.toString() }; // Convert BigNumber to string
    }));

    console.log('LP token balances fetched for all liquidity providers.');
    return providersWithBalances.filter(result => result.status === 'fulfilled').map(result => result.value);
}

function listenForEvents() {
    pairContract.events.Transfer({ filter: {}, fromBlock: 'latest' })
        .on('data', function(event) {
            console.log(event);
        })
        .on('error', console.error);
}

async function saveDataToJson(data) {
    fs.writeFileSync('liquidity_data.json', JSON.stringify(data, null, 2));
}

async function monitorPool() {
    setInterval(async () => {
        const poolDetails = await getPoolDetails();
        const decimals = 6; // USDT and USDC have 6 decimal places
        const reserve0 = poolDetails.reserves._reserve0 / (10 ** decimals);
        const reserve1 = poolDetails.reserves._reserve1 / (10 ** decimals);
        const totalSupply = poolDetails.totalSupply / (10 ** 18);
        
        console.log(`Reserve 0 (USDT): ${reserve0}`);
        console.log(`Reserve 1 (USDC): ${reserve1}`);
        console.log(`Total Supply: ${totalSupply}`);
    }, 60000); // Check every 60 seconds
}

(async () => {
    const poolDetails = await getPoolDetails();
    const liquidityProviders = await getAllLiquidityProviders();
    const liquidityData = { pairAddress, ...poolDetails, liquidityProviders };
    
    await saveDataToJson(liquidityData);
    console.log('Data saved to liquidity_data.json');

    listenForEvents(); // Listen for events on the USDT-USDC pair
    monitorPool(); // Monitor the pool
})();
