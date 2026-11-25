import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        ctx = await b.new_context(viewport={'width':560,'height':760}, accept_downloads=True)
        pg = await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(BASE+'/index.html?test=1'); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('mirror.prefs',JSON.stringify({mic:false}))"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#rec'); await pg.wait_for_timeout(2000); await pg.click('#rec'); await pg.wait_for_timeout(1200)
        async with pg.expect_download() as dl:
            await pg.click('#clipsave')
        d = await dl.value; path = await d.path()
        import os; print('downloaded', d.suggested_filename, os.path.getsize(path), 'bytes')
        print('note:', await pg.evaluate("document.getElementById('clipnote').textContent"))
        await pg.click('#clipdiscard'); await pg.click('#photo'); await pg.wait_for_timeout(600)
        async with pg.expect_download() as dl2:
            await pg.click('#clipsave')
        d2 = await dl2.value; print('photo', d2.suggested_filename)
        print('errors', errs)
        await b.close()
asyncio.run(main())
