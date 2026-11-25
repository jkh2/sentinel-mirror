"""SMOKE CHECK: the real MediaPipe models on a fake camera feed (no GPU needed; runs on SwiftShader).
Pass criteria: all three trackers load ("All set" status); no page errors; with --expect-hand, a hand from the feed
reaches the character within 3 s. Note --fake-face: our sample feeds contain no usable face, so the arm and hand
paths (which only run while a face is seen) need face freshness faked. FACE TRACKING ITSELF IS NOT COVERED HERE.
Needs: python3 tests/make_test_media.py and python3 -m http.server 8765 (repo root).
Run:   python3 tests/live_tracking_test.py --video tests/thumb_up.y4m --fake-face --expect-hand
       python3 tests/live_tracking_test.py --video tests/pose.y4m --fake-face"""
import os, sys, pathlib, asyncio
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _check import check, finish, page_errors
OUT=HERE/"out"; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get("CHROME","/usr/bin/google-chrome")
BASE=os.environ.get("MIRROR_URL","http://localhost:8765")
from playwright.async_api import async_playwright
import argparse
ap=argparse.ArgumentParser()
ap.add_argument("--video", default=str(HERE/"thumb_up.y4m")); ap.add_argument("--out", default=str(OUT/"live.png"))
ap.add_argument("--track", default="2"); ap.add_argument("--fake-face", action="store_true"); ap.add_argument("--expect-hand", action="store_true")
args=ap.parse_args()
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox","--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream",f"--use-file-for-fake-video-capture={args.video}","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        ctx = await b.new_context(viewport={"width":800,"height":600}, permissions=["camera"])
        pg = await ctx.new_page()
        logs=[]
        pg.on("pageerror", lambda e: logs.append("ERR "+str(e)))
        pg.on("console", lambda m: logs.append("console: "+m.text[:200]) if m.type=="error" else None)
        await pg.goto(BASE+"/index.html")
        await pg.evaluate(f"localStorage.setItem('mirror.prefs', JSON.stringify({{debug:true,track:{args.track},bg:0}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click("#go")
        st=""
        for i in range(60):
            await pg.wait_for_timeout(1000)
            st = await pg.evaluate("document.getElementById('status').textContent")
            if "All set" in st or "could not" in st or "failed" in st: break
        if args.fake_face: await pg.evaluate("setInterval(()=>{lastFaceT=performance.now();},30)")
        await pg.wait_for_timeout(3000)
        await pg.screenshot(path=args.out)
        info = await pg.evaluate("({hands:window.__mirror.S.hand.map(h=>!!h), detected:handDbg.length, detIntervalMs:Math.round(detInt)})")
        print("Raw results:"); print("  status:", st, f"(after {i+1} s)"); print("  ", info); print("   screenshot:", args.out); print()
        check("All set" in st, "face, pose and hand trackers all load", st)
        if args.expect_hand: check(any(info["hands"]), "a hand from the camera feed reaches the character", info)
        check(not page_errors(logs), "no page errors", page_errors(logs))
        await b.close()
    finish()
asyncio.run(main())
