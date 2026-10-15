const fs = require('fs');

async function inspectAndCapture() {
  const res = await fetch('http://localhost:9222/json');
  const targets = await res.json();
  const page = targets.find(t => t.type === 'page' && t.url.includes('3033'));
  if (!page) {
    console.log('No page target found');
    return;
  }

  const ws = new WebSocket(page.webSocketDebuggerUrl);

  ws.onopen = () => {
    ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
    ws.send(JSON.stringify({ id: 2, method: 'Page.enable' }));
    ws.send(JSON.stringify({ id: 3, method: 'Page.reload' }));

    // Evaluate model and loading indicator status after model download completes
    setTimeout(() => {
      ws.send(JSON.stringify({
        id: 10,
        method: 'Runtime.evaluate',
        params: {
          expression: `({
            modelLoaded: !!(window.furina3D && window.furina3D.model),
            spinnerDisplay: document.getElementById('model-loading-indicator') ? document.getElementById('model-loading-indicator').style.display : null,
            spinnerOpacity: document.getElementById('model-loading-indicator') ? document.getElementById('model-loading-indicator').style.opacity : null,
            furinaBones: window.furina3D && window.furina3D.animationController ? Object.keys(window.furina3D.animationController.bones).filter(k => !!window.furina3D.animationController.bones[k]) : [],
            jawBone: !!(window.furina3D && window.furina3D.lipSyncController && window.furina3D.lipSyncController.jawBone),
            currentState: window.furina3D && window.furina3D.animationController ? window.furina3D.animationController.getState() : null
          })`,
          returnByValue: true
        }
      }));
    }, 5000);

    // Capture screenshot via Page.captureScreenshot
    setTimeout(() => {
      ws.send(JSON.stringify({
        id: 20,
        method: 'Page.captureScreenshot',
        params: { format: 'png' }
      }));
    }, 6000);
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id === 10) {
      console.log('EVALUATION RESULT:', JSON.stringify(msg.params ? msg.params.result : msg.result, null, 2));
    }
    if (msg.id === 20 && msg.result && msg.result.data) {
      fs.writeFileSync('furina_cdp_capture.png', Buffer.from(msg.result.data, 'base64'));
      console.log('Screenshot successfully saved to furina_cdp_capture.png');
      ws.close();
      process.exit(0);
    }
  };
}

inspectAndCapture();
