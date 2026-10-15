import urllib.request
import json
import asyncio
import websockets
import base64
import os

CDP_HTTP = "http://localhost:9222"
ARTIFACT_DIR = "/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153"

async def test_all_teachers_isolated():
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
        await asyncio.sleep(4.0)

        teachers = [
            ("raiden_shogun", "Raiden Ei / Shogun"),
            ("zhongli", "Zhongli"),
            ("barbara", "Barbara"),
            ("furina", "Lady Furina"),
            ("tsaritsa", "The Tsaritsa"),
            ("nahida", "Nahida"),
            ("ganyu", "Ganyu"),
            ("keqing", "Keqing")
        ]

        for tid, name in teachers:
            print(f"Loading {name} ({tid})...")
            res = await call("Runtime.evaluate", {
                "expression": f"""(async () => {{
                    await window.switchTutor('{tid}');
                    return {{
                        currentTutor: window.currentTutorId,
                        modelName: window.tutor3D.model ? window.tutor3D.model.name : 'none',
                        groups: window.tutor3D.scene.children.filter(c => c.type === 'Group').map(g => g.name)
                    }};
                }})()""",
                "awaitPromise": True,
                "returnByValue": True
            })
            print(f"  Result: {res.get('result', {}).get('value')}")
            await asyncio.sleep(2.5)

            # Capture screenshot
            shot = await call("Page.captureScreenshot", {"format": "png"})
            filepath = os.path.join(ARTIFACT_DIR, f"teacher_{tid}_verified_clean.png")
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print(f"  Saved screenshot to {filepath}")

        # Now test student chatbox
        print("Testing student question to active teacher...")
        await call("Runtime.evaluate", {
            "expression": """(() => {
                const input = document.getElementById('student-chat-input');
                if (input) {
                    input.value = "Can you explain how your elemental abilities relate to modern science and philosophy?";
                    document.getElementById('send-chat-btn').click();
                }
            })()"""
        })
        await asyncio.sleep(4.0)

        shot_chat = await call("Page.captureScreenshot", {"format": "png"})
        filepath_chat = os.path.join(ARTIFACT_DIR, "chatbox_active_clean.png")
        with open(filepath_chat, "wb") as f:
            f.write(base64.b64decode(shot_chat["data"]))
        print(f"Saved chatbox response screenshot to {filepath_chat}")

        print("Isolated teacher testing complete!")

asyncio.run(test_all_teachers_isolated())
