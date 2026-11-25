"""CHECK: desktop Save. Record a 2 s clip, Save downloads an MP4/WebM; Photo, Save downloads a PNG; the note says where.
(The phone share-sheet path cannot be exercised in headless Chrome. It is not covered here.)
Needs: python3 -m http.server 8765 (repo root).  Run: python3 tests/save_test.py"""
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
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox","--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream"])
        ctx = await b.new_context(viewport={"width":560,"height":760}, accept_downloads=True)
        pg = await ctx.new_page(); logs=[]; pg.on("pageerror", lambda e: logs.append(str(e)))
        await pg.goto(BASE+"/index.html?test=1"); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('mirror.prefs',JSON.stringify({mic:false}))"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click("#rec"); await pg.wait_for_timeout(2000); await pg.click("#rec"); await pg.wait_for_timeout(1200)
        async with pg.expect_download() as dl:
            await pg.click("#clipsave")
        d = await dl.value; size = os.path.getsize(await d.path())
        note = await pg.evaluate("document.getElementById('clipnote').textContent")
        await pg.click("#clipdiscard"); await pg.click("#photo"); await pg.wait_for_timeout(600)
        async with pg.expect_download() as dl2:
            await pg.click("#clipsave")
        d2 = await dl2.value; size2 = os.path.getsize(await d2.path())
        print("Raw results:"); print("  clip:", d.suggested_filename, size, "bytes"); print("  note:", note); print("  photo:", d2.suggested_filename, size2, "bytes"); print()
        check(d.suggested_filename.endswith((".mp4",".webm")) and size > 50000, "clip downloads as a video file", "%s, %d bytes" % (d.suggested_filename, size))
        check("Downloads" in note, "note tells where the clip went", note)
        check(d2.suggested_filename.endswith(".png") and size2 > 10000, "photo downloads as a PNG", "%s, %d bytes" % (d2.suggested_filename, size2))
        check(not page_errors(logs), "no page errors", page_errors(logs))
        await b.close()
    finish()
asyncio.run(main())
