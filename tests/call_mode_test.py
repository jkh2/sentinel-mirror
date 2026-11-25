import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+str(HERE/'talk.wav')+''])
        ctx = await b.new_context(viewport={'width':640,'height':480}, permissions=['microphone','camera'])
        pg = await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(BASE+'/index.html?test=1'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#voicebtn'); await pg.wait_for_timeout(1500)
        info = await pg.evaluate("({on:window.__mirror.voice.on, mics:[...document.getElementById('vMic').options].map(o=>o.textContent), sinks:[...document.getElementById('vSink').options].map(o=>o.textContent), sinkRow:getComputedStyle(document.getElementById('vSinkRow')).display})")
        print(info)
        await pg.screenshot(path=str(OUT/'call_panel.png'))
        await pg.click('#callbtn'); await pg.wait_for_timeout(3000)
        await pg.screenshot(path=str(OUT/'call_mode.png'))
        vis = await pg.evaluate("['top','dock','voice','toast'].map(id=>id+':'+getComputedStyle(document.getElementById(id)).display+'/'+getComputedStyle(document.getElementById(id)).opacity)")
        print('in call mode:', vis)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        print('after Esc dock:', await pg.evaluate("getComputedStyle(document.getElementById('dock')).display"))
        print('errors', errs)
        await b.close()
asyncio.run(main())
