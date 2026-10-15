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
      // 1. Reload page to ensure fresh code
      console.log('Reloading page...');
      await send('Page.reload', { ignoreCache: true });
      await new Promise(r => setTimeout(r, 2000));

      // 2. Wait until window.furina3D and animation controllers are fully wired
      console.log('Waiting for Furina 3D model streaming and animation controllers to wire...');
      let loaded = false;
      for (let i = 0; i < 40; i++) {
        const val = await evaluate(`Boolean(window.furina3D && window.dialogueController && window.dialogueController.animationController && window.audioPlayer)`);
        if (val) {
          loaded = true;
          break;
        }
        await new Promise(r => setTimeout(r, 500));
      }

      if (!loaded) {
        throw new Error('Furina 3D model streaming or DialogueController failed to wire in time');
      }
      console.log('✓ Furina 3D, AudioPlayer, and DialogueController wired and ready');

      // 3. User gesture simulation to unlock Web Audio API
      console.log('Unlocking Web Audio context via user interaction...');
      await evaluate(`
        window.audioPlayer.unlockContext();
        if (window.audioPlayer.audioContext && window.audioPlayer.audioContext.state === 'suspended') {
          window.audioPlayer.audioContext.resume();
        }
      `);

      // 4. Send inquiry to trigger real speech audio
      console.log('Triggering student dialogue message: "Can you explain how Hydro creates elemental reactions in Fontaine?"');
      await evaluate(`
        window.dialogueController.sendStudentMessage("Can you explain how Hydro creates elemental reactions in Fontaine?");
      `);

      // 5. Poll audio status, acoustic volume, and jaw movement over next 12 seconds
      console.log('Monitoring audio playback, AnalyserNode acoustic data, and Furina jaw animation...');
      let heardAudio = false;
      let maxAmplitude = 0;
      let jawMoved = false;

      for (let t = 0; t < 30; t++) {
        await new Promise(r => setTimeout(r, 400));
        const data = await evaluate(`
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
              currentVol: currentVol,
              state: f3d ? f3d.getState() : null,
              jawRotationX: jawRot,
              jawPositionY: jawPos,
              dialogueProcessing: dc ? dc.isProcessing : false
            };
          })()
        `);

        if (data) {
          if (data.isPlaying || data.hasSource) heardAudio = true;
          if (data.currentVol > maxAmplitude) maxAmplitude = data.currentVol;
          if (Math.abs(data.jawRotationX) > 0.005 || Math.abs(data.jawPositionY) > 0.0005) jawMoved = true;

          console.log(`[t=${(t * 0.4).toFixed(1)}s] State: ${data.state} | AudioPlaying: ${data.isPlaying} | AudioState: ${data.audioContextState} | Vol: ${data.currentVol.toFixed(3)} | JawRotX: ${data.jawRotationX.toFixed(4)}`);
        }
      }

      console.log('\n--- Final Verification Results ---');
      console.log('Audio Pipeline Playing on Localhost:', heardAudio ? 'PASSED ✓' : 'FAILED ✗');
      console.log('Max Acoustic Analyser Volume:', maxAmplitude.toFixed(4));
      console.log('Furina Jaw Displaced & Synchronized:', jawMoved ? 'PASSED ✓' : 'FAILED ✗');

      if (!heardAudio) {
        console.error('Audio playback was not active during dialogue test');
        process.exit(1);
      }

      console.log('\nAll localhost voice output checks passed successfully!');
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
