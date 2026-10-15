const fs = require('fs');

async function testDialogue() {
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

    // Send dialogue inquiry via window.dialogueController
    setTimeout(() => {
      ws.send(JSON.stringify({
        id: 10,
        method: 'Runtime.evaluate',
        params: {
          expression: `window.dialogueController.sendStudentMessage("Explain Arkhe Mechanics (Pneuma & Ousia)");`,
          returnByValue: true
        }
      }));
    }, 1000);

    // After 2.5 seconds, check state and mouth jaw opening
    setTimeout(() => {
      ws.send(JSON.stringify({
        id: 20,
        method: 'Runtime.evaluate',
        params: {
          expression: `({
            state: window.furina3D.animationController.getState(),
            isPlaying: window.audioPlayer.isPlaying,
            audioVolume: window.furina3D.animationController.audioVolume,
            jawPosY: window.furina3D.lipSyncController.jawBone.position.y,
            jawRotX: window.furina3D.lipSyncController.jawBone.rotation.x,
            messagesCount: document.querySelectorAll('.chat-bubble').length,
            latestMessage: document.querySelector('.chat-bubble:last-child').textContent
          })`,
          returnByValue: true
        }
      }));
    }, 2500);

    // Capture screenshot during active speaking state
    setTimeout(() => {
      ws.send(JSON.stringify({
        id: 30,
        method: 'Page.captureScreenshot',
        params: { format: 'png' }
      }));
    }, 3000);
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id === 20) {
      console.log('ACTIVE DIALOGUE METRICS:', JSON.stringify(msg.result.value, null, 2));
    }
    if (msg.id === 30 && msg.result && msg.result.data) {
      fs.writeFileSync('furina_speaking_capture.png', Buffer.from(msg.result.data, 'base64'));
      console.log('Speaking screenshot saved to furina_speaking_capture.png');
      ws.close();
      process.exit(0);
    }
  };
}

testDialogue();
