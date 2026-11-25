"""CHECK: voice changer end to end in Chrome with a fake mic (tests/talk.wav: 200 Hz bursts, 0.4 s on / 0.2 s off).
Pass criteria: tapping Voice turns it on with the Teddy preset (Match character); the mouth follows the bursts (jaw both
opens past .6 and closes below .45 within 1.2 s); picking Robot switches the voice to Robot; a recorded Chipmunk clip
decodes with its loudest pitch within 3 Hz of 200 Hz x 2^(11/12) = 378 Hz; no page errors.
Needs: python3 tests/make_test_media.py and python3 -m http.server 8765 (repo root).  Run: python3 tests/voice_test.py"""
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
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox","--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream","--use-file-for-fake-audio-capture="+str(HERE/"talk.wav"),"--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width":560,"height":760}, permissions=["microphone","camera"])
        pg = await ctx.new_page()
        logs=[]; pg.on("pageerror", lambda e: logs.append("ERR "+str(e))); pg.on("console", lambda m: logs.append(m.type+": "+m.text[:160]) if m.type=="error" else None)
        await pg.goto(BASE+"/index.html?test=1"); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("window.__mirror.pickChar(0)")
        await pg.click("#voicebtn"); await pg.wait_for_timeout(1500)
        st = await pg.evaluate("({on:window.__mirror.voice.on, preset:window.__mirror.VP.preset, btn:document.getElementById('voicebtn').textContent})")
        jaws=[]
        for i in range(12):
            jaws.append(round(await pg.evaluate("window.__mirror.S.jaw"),2)); await pg.wait_for_timeout(100)
        await pg.screenshot(path=str(OUT/"voice_panel.png"))
        await pg.evaluate("window.__mirror.pickChar(5)")
        robot = await pg.evaluate("window.__mirror.VP.preset")
        await pg.select_option("#vPreset","chipmunk"); await pg.wait_for_timeout(300)
        await pg.click("#rec"); await pg.wait_for_timeout(3000); await pg.click("#rec"); await pg.wait_for_timeout(1500)
        clip = await pg.evaluate("""async()=>{
          const a=document.getElementById('clipsave'); const blob=await (await fetch(a.href)).blob();
          const ac=new OfflineAudioContext(1,48000,48000);
          let buf; try{ buf=await ac.decodeAudioData(await blob.arrayBuffer()); }catch(e){ return {size:blob.size,type:blob.type,err:String(e)}; }
          const d=buf.getChannelData(0), sr=buf.sampleRate;
          let bi=0,be=0; const W=Math.round(sr*.3); for(let i=0;i+W<d.length;i+=Math.round(sr*.05)){ let e=0; for(let k=0;k<W;k+=4) e+=d[i+k]*d[i+k]; if(e>be){be=e;bi=i;} }
          const seg=d.slice(bi,bi+W); let best=0,bf=0;
          for(let f=80;f<900;f+=1){ let re=0,im=0; for(let i=0;i<seg.length;i+=2){ const a=2*Math.PI*f*i/sr; re+=seg[i]*Math.cos(a); im+=seg[i]*Math.sin(a);} const m=re*re+im*im; if(m>best){best=m;bf=f;} }
          return {size:blob.size,type:blob.type,dur:+buf.duration.toFixed(2),peakHz:bf};
        }""")
        expected = 200*2**(11/12)
        print("Raw results:"); print("  voice state:", st); print("  jaw over 1.2 s:", jaws); print("  preset after picking Robot:", robot); print("  clip:", clip, " expected peak %.1f Hz" % expected); print()
        check(st["on"] and st["preset"]=="teddy", "Voice turns on with the Teddy preset", st)
        check(max(jaws) > .6 and min(jaws) < .45, "mouth opens and closes with the speech bursts", "max %.2f, min %.2f" % (max(jaws), min(jaws)))
        check(robot=="robot", "picking Robot switches the voice to Robot (Match character)", robot)
        check("err" not in clip and clip.get("dur",0) > 1.5, "recorded clip decodes with audio", clip)
        check("peakHz" in clip and abs(clip["peakHz"]-expected) <= 3, "clip carries the Chipmunk pitch", "%s Hz vs %.1f Hz" % (clip.get("peakHz"), expected))
        check(not page_errors(logs), "no page errors", page_errors(logs))
        await b.close()
    finish()
asyncio.run(main())
