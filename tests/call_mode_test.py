"""CHECK: mic and output pickers, and Call mode.
Pass criteria: the Listen to and Voice goes to pickers list the browser's devices (the output row shows where
AudioContext.setSinkId exists); Call mode hides the top bar, dock and Voice panel; Esc brings the dock back; no page errors.
Needs: python3 tests/make_test_media.py and python3 -m http.server 8765 (repo root).  Run: python3 tests/call_mode_test.py"""
import os, sys, pathlib, asyncio
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _check import check, finish, page_errors
OUT=HERE/"out"; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get("CHROME","/usr/bin/google-chrome")
BASE=os.environ.get("MIRROR_URL","http://localhost:8765")
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox","--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream","--use-file-for-fake-audio-capture="+str(HERE/"talk.wav")])
        ctx = await b.new_context(viewport={"width":640,"height":480}, permissions=["microphone","camera"])
        pg = await ctx.new_page(); logs=[]; pg.on("pageerror", lambda e: logs.append(str(e)))
        await pg.goto(BASE+"/index.html?test=1"); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click("#voicebtn"); await pg.wait_for_timeout(1500)
        info = await pg.evaluate("({on:window.__mirror.voice.on, canSink:!!(window.AudioContext&&AudioContext.prototype.setSinkId), mics:[...document.getElementById('vMic').options].map(o=>o.textContent), sinks:[...document.getElementById('vSink').options].map(o=>o.textContent), sinkRow:getComputedStyle(document.getElementById('vSinkRow')).display})")
        await pg.screenshot(path=str(OUT/"call_panel.png"))
        await pg.click("#callbtn"); await pg.wait_for_timeout(3000)
        await pg.screenshot(path=str(OUT/"call_mode.png"))
        hidden = await pg.evaluate("Object.fromEntries(['top','dock','voice','settings'].map(id=>[id,getComputedStyle(document.getElementById(id)).display]))")
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200)
        after = await pg.evaluate("getComputedStyle(document.getElementById('dock')).display")
        print("Raw results:"); print("  devices:", info); print("  in call mode:", hidden); print("  dock after Esc:", after); print()
        check(info["on"], "voice changer is on")
        check(len(info["mics"]) >= 2, "Listen to lists the mics", info["mics"])
        check((len(info["sinks"]) >= 2 and info["sinkRow"] != "none") if info["canSink"] else info["sinkRow"] == "none", "Voice goes to lists outputs where supported (hidden otherwise)", info["sinks"])
        check(all(v == "none" for v in hidden.values()), "Call mode hides every control", hidden)
        check(after != "none", "Esc brings the buttons back", after)
        check(not page_errors(logs), "no page errors", page_errors(logs))
        await b.close()
    finish()
asyncio.run(main())
