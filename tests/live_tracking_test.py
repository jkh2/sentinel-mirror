import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio, sys
from playwright.async_api import async_playwright
src=sys.argv[1]; out=sys.argv[2]; track=sys.argv[3] if len(sys.argv)>3 else '2'
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream',f'--use-file-for-fake-video-capture={src}','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        ctx = await b.new_context(viewport={'width':800,'height':600}, permissions=['camera'])
        pg = await ctx.new_page()
        logs=[]
        pg.on('pageerror', lambda e: logs.append('ERR '+str(e)))
        pg.on('console', lambda m: logs.append(m.type+': '+m.text[:200]))
        await pg.goto(BASE+'/index.html')
        await pg.evaluate(f"localStorage.setItem('mirror.prefs', JSON.stringify({{debug:true,track:{track},bg:0}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#go')
        for i in range(60):
            await pg.wait_for_timeout(1000)
            st = await pg.evaluate("document.getElementById('status').textContent")
            if 'All set' in st or 'could not' in st or 'failed' in st: break
        print('status:', st, 'after', i+1, 's')
        if len(sys.argv)>4: await pg.evaluate('setInterval(()=>{lastFaceT=performance.now();},30)')
        await pg.wait_for_timeout(3000)
        await pg.screenshot(path=out)
        info = await pg.evaluate("({hands:window.__mirror.S.hand.map(h=>!!h), sA:window.__mirror.S.sA, wB:window.__mirror.S.wB})")
        print(info)
        for l in logs:
            if 'favicon' not in l and 'INFO' not in l: print(l)
        await b.close()
asyncio.run(main())
