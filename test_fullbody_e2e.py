import json
import urllib.request
import asyncio
import websockets
import base64
import time

CDP_HTTP = "http://localhost:9222"

async def run_fullbody_test():
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

        # 1. Switch to Raiden Shogun (Mathematics)
        print("Switching to Raiden Shogun full body...")
        await call("Runtime.evaluate", {
            "expression": "window.switchTutor('raiden_shogun')",
            "awaitPromise": True
        })
        await asyncio.sleep(2.5)

        # Capture Raiden full-body screenshot
        shot1 = await call("Page.captureScreenshot", {"format": "png"})
        with open("/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153/fullbody_raiden_verified.png", "wb") as f:
            f.write(base64.b64decode(shot1["data"]))
        print("Saved fullbody_raiden_verified.png")

        # 2. Type custom question into the chatbox and press Enter
        print("Typing student question into chatbox...")
        custom_question = "What is Euler's Identity and why is it considered the most beautiful theorem in Mathematics?"
        await call("Runtime.evaluate", {
            "expression": f"""(() => {{
                const input = document.getElementById('student-chat-input');
                if (input) {{
                    input.value = "{custom_question}";
                    document.getElementById('send-chat-btn').click();
                }}
            }})()"""
        })
        await asyncio.sleep(4.5)

        # Capture Raiden answering screenshot
        shot2 = await call("Page.captureScreenshot", {"format": "png"})
        with open("/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153/chatbox_custom_answer_verified.png", "wb") as f:
            f.write(base64.b64decode(shot2["data"]))
        print("Saved chatbox_custom_answer_verified.png")

        # 3. Switch to Zhongli (Humanities) full body
        print("Switching to Zhongli full body...")
        await call("Runtime.evaluate", {
            "expression": "window.switchTutor('zhongli')",
            "awaitPromise": True
        })
        await asyncio.sleep(2.5)

        shot3 = await call("Page.captureScreenshot", {"format": "png"})
        with open("/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153/fullbody_zhongli_verified.png", "wb") as f:
            f.write(base64.b64decode(shot3["data"]))
        print("Saved fullbody_zhongli_verified.png")

        # 4. Open API key modal
        print("Opening API key settings modal...")
        await call("Runtime.evaluate", {
            "expression": "document.getElementById('api-key-config-btn').click()"
        })
        await asyncio.sleep(1.0)

        shot4 = await call("Page.captureScreenshot", {"format": "png"})
        with open("/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153/api_key_modal_verified.png", "wb") as f:
            f.write(base64.b64decode(shot4["data"]))
        print("Saved api_key_modal_verified.png")

        # Close modal
        await call("Runtime.evaluate", {
            "expression": "document.getElementById('close-api-key-modal-btn').click()"
        })

asyncio.run(run_fullbody_test())
