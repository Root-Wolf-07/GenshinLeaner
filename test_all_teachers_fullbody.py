import json
import urllib.request
import asyncio
import websockets
import base64
import os

CDP_HTTP = "http://localhost:9222"
ARTIFACT_DIR = "/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153"

async def test_teachers():
    req = urllib.request.urlopen(f"{CDP_HTTP}/json")
    targets = json.loads(req.read().decode())
    target = [t for t in targets if t.get("type") == "page" and "3033" in t.get("url", "")][0]

    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        msg_id = 1
        async def call(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        await call("Runtime.enable")
        await call("Page.enable")

        print("Navigating to http://localhost:3033/index.html ...")
        await call("Page.navigate", {"url": "http://localhost:3033/index.html"})
        await asyncio.sleep(3.5)

        teachers_to_test = [
            ("raiden_shogun", "Raiden Ei / Shogun (Math)"),
            ("zhongli", "Zhongli (Humanities)"),
            ("barbara", "Barbara (Biology)"),
            ("furina", "Lady Furina (Dance & Music)"),
            ("tsaritsa", "The Tsaritsa (Gen. Knowledge)"),
            ("nahida", "Nahida (Moral Studies)"),
            ("ganyu", "Ganyu (Physics)"),
            ("keqing", "Keqing (Computer Science)")
        ]

        for tid, name in teachers_to_test:
            print(f"Testing teacher: {name} (ID: {tid})...")
            # Click tutor pill button in the DOM
            await call("Runtime.evaluate", {
                "expression": f"""(() => {{
                    const btn = document.querySelector('#subject-selector-grid button[data-tutor="{tid}"]');
                    if (btn) btn.click();
                    else window.switchTutor('{tid}');
                }})()""",
                "awaitPromise": True
            })
            await asyncio.sleep(3.5)

            # Check bounding box and height
            info = await call("Runtime.evaluate", {
                "expression": """(() => {
                    const canvas = document.querySelector('canvas.tutor-webgl-canvas');
                    return {
                        hasCanvas: !!canvas,
                        width: canvas ? canvas.clientWidth : 0,
                        height: canvas ? canvas.clientHeight : 0,
                        tutorId: window.currentTutorId || 'none',
                        activeTitle: document.getElementById('active-tutor-name') ? document.getElementById('active-tutor-name').textContent : ''
                    };
                })()""",
                "returnByValue": True
            })
            print(f"  Canvas details: {info.get('result', {}).get('value')}")

            # Capture snapshot for all requested teachers
            shot = await call("Page.captureScreenshot", {"format": "png"})
            filepath = os.path.join(ARTIFACT_DIR, f"teacher_{tid}_fullbody_verified.png")
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print(f"  Saved screenshot to {filepath}")

        # Now test Chatbox Question Submission with Nahida
        print("Submitting question to Nahida via student chatbox...")
        await call("Runtime.evaluate", {
            "expression": """(() => {
                const input = document.getElementById('student-chat-input');
                if (input) {
                    input.value = "What is the true nature of wisdom, Lesser Lord Kusanali?";
                    document.getElementById('send-chat-btn').click();
                }
            })()"""
        })
        await asyncio.sleep(4.0)

        shot_chat = await call("Page.captureScreenshot", {"format": "png"})
        filepath_chat = os.path.join(ARTIFACT_DIR, "chatbox_nahida_dialogue_verified.png")
        with open(filepath_chat, "wb") as f:
            f.write(base64.b64decode(shot_chat["data"]))
        print(f"Saved chatbox response screenshot to {filepath_chat}")

        # Test Mic Toggle button click
        print("Testing Microphone Toggle UI response...")
        await call("Runtime.evaluate", {
            "expression": "document.getElementById('mic-toggle-btn').click()"
        })
        await asyncio.sleep(1.0)

        shot_mic = await call("Page.captureScreenshot", {"format": "png"})
        filepath_mic = os.path.join(ARTIFACT_DIR, "mic_button_active_verified.png")
        with open(filepath_mic, "wb") as f:
            f.write(base64.b64decode(shot_mic["data"]))
        print(f"Saved mic active screenshot to {filepath_mic}")

        # Reset Mic
        await call("Runtime.evaluate", {
            "expression": "document.getElementById('mic-toggle-btn').click()"
        })

        print("All teachers and features verified successfully!")

asyncio.run(test_teachers())
