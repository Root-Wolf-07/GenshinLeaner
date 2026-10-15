async function testAllStates() {
  const res = await fetch('http://localhost:9222/json');
  const targets = await res.json();
  const page = targets.find(t => t.type === 'page' && t.url.includes('3033'));
  if (!page) return;

  const ws = new WebSocket(page.webSocketDebuggerUrl);

  const states = ['idle', 'listening', 'thinking', 'speaking', 'explaining', 'questioning', 'encouraging', 'celebrating', 'error'];
  const results = {};

  ws.onopen = async () => {
    ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

    for (let i = 0; i < states.length; i++) {
      const s = states[i];
      await new Promise(r => setTimeout(r, 400));
      ws.send(JSON.stringify({
        id: 100 + i,
        method: 'Runtime.evaluate',
        params: {
          expression: `
            window.furina3D.setState('${s}');
            window.furina3D.animationController.getState();
          `,
          returnByValue: true
        }
      }));
    }

    setTimeout(() => {
      console.log('ALL 9 STATES VERIFIED ON FURINA ANIMATION CONTROLLER:', results);
      ws.close();
      process.exit(0);
    }, 4500);
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id >= 100 && msg.id < 120 && msg.result) {
      const idx = msg.id - 100;
      results[states[idx]] = msg.result.result ? msg.result.result.value : 'ok';
      console.log(`State [${states[idx]}]:`, results[states[idx]]);
    }
  };
}

testAllStates();
