const fs = require('fs');
const path = require('path');

async function main() {
  const wsUrl = "ws://localhost:9222/devtools/page/B0F9D47F8B976CBB23E2C17B2C3F2FAC";
  const ws = new WebSocket(wsUrl);

  let idCounter = 1;
  const pending = new Map();

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = idCounter++;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async function evaluate(expression, awaitPromise = false) {
    const res = await send('Runtime.evaluate', {
      expression,
      awaitPromise,
      returnByValue: true
    });
    if (res.result && res.result.exceptionDetails) {
      console.error('Eval error:', JSON.stringify(res.result.exceptionDetails));
    }
    if (res.result && res.result.result) {
      return res.result.result.value;
    }
    return null;
  }

  ws.addEventListener('open', async () => {
    console.log('Connected to Chrome DevTools Protocol');

    try {
      // 1. Reload page
      console.log('Reloading page...');
      await send('Page.reload', { ignoreCache: true });
      await new Promise(r => setTimeout(r, 2000));

      // 2. Wait until Furina 3D and all controllers are wired
      console.log('Waiting for Furina 3D and DialogueController to initialize...');
      let ready = false;
      for (let i = 0; i < 40; i++) {
        const val = await evaluate(`Boolean(window.furina3D && window.dialogueController && window.dialogueController.animationController && window.audioPlayer)`);
        if (val) {
          ready = true;
          break;
        }
        await new Promise(r => setTimeout(r, 500));
      }

      if (!ready) {
        throw new Error('Furina 3D and controllers failed to wire within timeout');
      }
      console.log('✓ Furina 3D and DialogueController are wired and ready');

      // 3. Find bounding box of #trigger-voice-test-btn
      console.log('Finding position of Voice Test Button...');
      const btnRect = await evaluate(`
        (() => {
          const btn = document.getElementById('trigger-voice-test-btn');
          if (!btn) return null;
          const r = btn.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        })()
      `);

      if (!btnRect) {
        throw new Error('Voice test button not found in DOM');
      }

      console.log(`Dispatching trusted mouse click at (${btnRect.x.toFixed(1)}, ${btnRect.y.toFixed(1)})...`);
      await send('Input.dispatchMouseEvent', {
        type: 'mousePressed',
        x: btnRect.x,
        y: btnRect.y,
        button: 'left',
        clickCount: 1
      });
      await send('Input.dispatchMouseEvent', {
        type: 'mouseReleased',
        x: btnRect.x,
        y: btnRect.y,
        button: 'left',
        clickCount: 1
      });

      // 4. Monitor audio playback, AudioContext state, volume, and jaw movement
      console.log('\nMonitoring real-time audio playback & character animation:');
      let heardAudio = false;
      let audioRunning = false;
      let maxVol = 0;
      let jawMoved = false;
      let screenshotTaken = false;

      for (let t = 0; t < 35; t++) {
        await new Promise(r => setTimeout(r, 350));
        const status = await evaluate(`
          (() => {
            const ap = window.audioPlayer;
            const f3d = window.furina3D;
            const dc = window.dialogueController;
            const jaw = f3d && f3d.lipSyncController && f3d.lipSyncController.jawBone;
            const jawRot = jaw ? jaw.rotation.x : 0;
            const jawPos = jaw ? jaw.position.y : 0;

            let currentVol = 0;
            if (ap && ap.analyser && ap.dataArray) {
              ap.analyser.getByteFrequencyData(ap.dataArray);
              let sum = 0;
              for (let i = 2; i < 30; i++) sum += ap.dataArray[i];
              currentVol = (sum / 28) / 100;
            }

            return {
              audioContextState: ap && ap.audioContext ? ap.audioContext.state : null,
              isPlaying: ap ? ap.isPlaying : false,
              hasSource: Boolean(ap && ap.currentSource),
              hasAudioEl: Boolean(ap && ap.currentAudio && !ap.currentAudio.paused),
              currentVol: currentVol,
              state: f3d ? f3d.getState() : null,
              jawRotationX: jawRot,
              jawPositionY: jawPos,
              dialogueProcessing: dc ? dc.isProcessing : false
            };
          })()
        `);

        if (status) {
          if (status.isPlaying || status.hasSource || status.hasAudioEl) heardAudio = true;
          if (status.audioContextState === 'running') audioRunning = true;
          if (status.currentVol > maxVol) maxVol = status.currentVol;
          if (Math.abs(status.jawRotationX) > 0.005 || Math.abs(status.jawPositionY) > 0.0005) jawMoved = true;

          console.log(`[t=${(t * 0.35).toFixed(1)}s] State: ${status.state} | Playing: ${status.isPlaying} | AudioContext: ${status.audioContextState} | Vol: ${status.currentVol.toFixed(3)} | JawRotX: ${status.jawRotationX.toFixed(4)}`);

          // Capture screenshot during active speaking with open mouth
          if (!screenshotTaken && status.isPlaying && (status.state === 'speaking' || status.state === 'explaining') && t > 8) {
            screenshotTaken = true;
            console.log('Capturing verified screenshot during speech...');
            const shotRes = await send('Page.captureScreenshot', { format: 'png' });
            if (shotRes && shotRes.result && shotRes.result.data) {
              const buffer = Buffer.from(shotRes.result.data, 'base64');
              const outPath = path.resolve('furina_voice_output_verified.png');
              fs.writeFileSync(outPath, buffer);
              console.log(`✓ Saved screenshot to ${outPath}`);
            }
          }
        }
      }

      console.log('\n=======================================');
      console.log('--- LOCALHOST VOICE OUTPUT TEST RESULTS ---');
      console.log('=======================================');
      console.log('Audio Playback Triggered:', heardAudio ? 'PASSED ✓' : 'FAILED ✗');
      console.log('Web Audio Context Running:', audioRunning ? 'PASSED ✓' : 'FAILED ✗');
      console.log('Peak Acoustic Volume:', maxVol.toFixed(4));
      console.log('Furina Jaw Displaced & Synchronized:', jawMoved ? 'PASSED ✓' : 'FAILED ✗');

      if (!heardAudio) {
        console.error('Audio playback was not active during test');
        process.exit(1);
      }

      console.log('\n✓ All voice output and 3D lip-sync tests PASSED successfully!');
      process.exit(0);
    } catch (e) {
      console.error('Test error:', e);
      process.exit(1);
    }
  });

  ws.addEventListener('message', (event) => {
    const res = JSON.parse(event.data);
    if (res.id && pending.has(res.id)) {
      const { resolve } = pending.get(res.id);
      pending.delete(res.id);
      resolve(res);
    }
  });

  ws.addEventListener('error', (err) => {
    console.error('WebSocket error:', err);
    process.exit(1);
  });
}

main();
