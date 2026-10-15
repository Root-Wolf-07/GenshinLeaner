import json
import urllib.request
import asyncio
import websockets
import base64
import time

CDP_HTTP = "http://localhost:9222"

async def run_test():
    # 1. Get targets
    req = urllib.request.urlopen(f"{CDP_HTTP}/json")
    targets = json.loads(req.read().decode())
    page_target = None
    for t in targets:
        if t.get("type") == "page" and "3033" in t.get("url", ""):
            page_target = t
            break
    if not page_target:
        # Fall back to first page
        page_target = [t for t in targets if t.get("type") == "page"][0]

    ws_url = page_target["webSocketDebuggerUrl"]
    print(f"Connecting to CDP WebSocket: {ws_url}")

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        msg_id = 1
        async def call(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            payload = {"id": cid, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        # Enable runtime & page
        await call("Runtime.enable")
        await call("Page.enable")

        print("Navigating to http://localhost:3033/index.html ...")
        await call("Page.navigate", {"url": "http://localhost:3033/index.html"})
        await asyncio.sleep(3)

        # Check initial state
        eval_res = await call("Runtime.evaluate", {
            "expression": """(() => {
                return {
                    hasTutor3D: !!window.universalTutor3D,
                    activeTutor: window.universalTutor3D ? window.universalTutor3D.activeTutor.id : null,
                    isLoaded: window.universalTutor3D ? window.universalTutor3D.isLoaded : false,
                    title: document.title
                };
            })()""",
            "returnByValue": True
        })
        print("Initial state:", eval_res.get("result", {}).get("value"))

        # Wait until loaded
        for _ in range(20):
            res = await call("Runtime.evaluate", {
                "expression": "window.universalTutor3D && window.universalTutor3D.isLoaded",
                "returnByValue": True
            })
            if res.get("result", {}).get("value") == True:
                print("Initial 3D tutor loaded successfully!")
                break
            await asyncio.sleep(0.5)

        # Switch to Zhongli (Humanities)
        print("Switching tutor to Zhongli (Humanities)...")
        await call("Runtime.evaluate", {
            "expression": "window.switchTutor('zhongli')",
            "awaitPromise": True
        })
        await asyncio.sleep(2)

        # Switch to Furina (Dance & Music)
        print("Switching tutor to Furina (Dance & Music)...")
        await call("Runtime.evaluate", {
            "expression": "window.switchTutor('furina')",
            "awaitPromise": True
        })
        await asyncio.sleep(2)

        # Send dialogue question
        print("Sending dialogue question to Furina...")
        await call("Runtime.evaluate", {
            "expression": """(() => {
                window.audioPlayer.unlockContext();
                window.dialogueController.sendStudentMessage("Can you explain how Hydro and Electro create continuous elemental reactions?");
            })()"""
        })
        await asyncio.sleep(5)

        # Check dialogue transcript and tutor response
        transcript_res = await call("Runtime.evaluate", {
            "expression": """(() => {
                const bubbles = Array.from(document.querySelectorAll('#chat-transcript .chat-bubble'));
                return bubbles.map(b => b.innerText);
            })()""",
            "returnByValue": True
        })
        print("Chat transcript bubbles:")
        for b in transcript_res.get("result", {}).get("value", []):
            print(" - ", b.replace('\\n', ' | ')[:120])

        # Capture screenshot
        print("Capturing verification screenshot...")
        shot = await call("Page.captureScreenshot", {"format": "png"})
        img_data = base64.b64decode(shot["data"])
        out_path = "/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153/tutor_multicharacter_verified.png"
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"Screenshot saved to {out_path} ({len(img_data)} bytes)")

asyncio.run(run_test())
