const sdk = require('./node_modules/@modelcontextprotocol/sdk/dist/cjs/client/index.js');

const nodeSDK = new sdk.NodeSDK({
  transport: 'stdio',
  instructions: 'ruflo v3.6.27'
});

let initialized = false;

nodeSDK.on('notification', (msg) => {
  console.error('[NOTIF]', msg.method);
  if (msg.method === 'initialized' && !initialized) {
    initialized = true;
    console.error('[READY] sending embeddings_init...');
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'embeddings_init',arguments:{model:'Xenova/all-MiniLM-L6-v2',hyperbolic:true,force:false}}}) + '\n');
  }
});

nodeSDK.on('response', (msg) => {
  console.error('[RESP]', JSON.stringify(msg).substring(0, 200));
});

nodeSDK.on('error', (err) => {
  console.error('[ERR]', err.message);
});

nodeSDK.start().catch(e => { console.error(e); process.exit(1); });
setTimeout(() => process.exit(0), 10000);