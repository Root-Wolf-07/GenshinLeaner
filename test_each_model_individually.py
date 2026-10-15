import urllib.request
import json
import asyncio
import websockets
import base64
import os

CDP_HTTP = "http://localhost:9222"
ARTIFACT_DIR = "/Users/gojo/.gemini/antigravity-ide/brain/728d5eec-53b6-406e-9d71-0521891b0153"

async def test_all():
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
        await call("Page.navigate", {"url": "http://localhost:3033/index.html"})
        await asyncio.sleep(3.5)

        teachers = [
            "raiden_shogun",
            "zhongli",
            "barbara",
            "furina",
            "tsaritsa",
            "nahida",
            "ganyu",
            "keqing"
        ]

        diagnostics = {}

        for tid in teachers:
            print(f"--- Diagnosing {tid} ---")
            res = await call("Runtime.evaluate", {
                "expression": f"""(async () => {{
                    try {{
                        await window.switchTutor('{tid}');
                        await new Promise(r => setTimeout(r, 1500));
                        const m = window.tutor3D.model;
                        if (!m) return {{ ok: false, err: 'no model' }};
                        const b = new window.THREE.Box3().setFromObject(m);
                        const s = new window.THREE.Vector3();
                        b.getSize(s);
                        const c = new window.THREE.Vector3();
                        b.getCenter(c);

                        let meshCount = 0;
                        let vertCount = 0;
                        m.traverse(node => {{
                            if (node.isMesh) {{
                                meshCount++;
                                if (node.geometry && node.geometry.attributes.position) {{
                                    vertCount += node.geometry.attributes.position.count;
                                }}
                            }}
                        }});

                        return {{
                            ok: true,
                            modelName: m.name,
                            meshCount: meshCount,
                            vertCount: vertCount,
                            size: {{ x: s.x, y: s.y, z: s.z }},
                            center: {{ x: c.x, y: c.y, z: c.z }},
                            minY: b.min.y,
                            maxY: b.max.y,
                            camPos: {{
                                x: window.tutor3D.camera.position.x,
                                y: window.tutor3D.camera.position.y,
                                z: window.tutor3D.camera.position.z
                            }}
                        }};
                    }} catch(e) {{
                        return {{ ok: false, err: e.toString(), stack: e.stack }};
                    }}
                }})()""",
                "awaitPromise": True,
                "returnByValue": True
            })
            info = res.get("result", {}).get("value", {})
            diagnostics[tid] = info
            print(f"  Info for {tid}: {json.dumps(info, indent=2)}")

            # Capture screenshot
            shot = await call("Page.captureScreenshot", {"format": "png"})
            filepath = os.path.join(ARTIFACT_DIR, f"diag_{tid}.png")
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print(f"  Saved screenshot to {filepath}")

        with open(os.path.join(ARTIFACT_DIR, "all_teachers_diag.json"), "w") as f:
            json.dump(diagnostics, f, indent=2)

asyncio.run(test_all())
