import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+str(HERE/'talk.wav')+'','--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width':560,'height':760}, permissions=['microphone','camera'])
        pg = await ctx.new_page()
        logs=[]; pg.on('pageerror', lambda e: logs.append('ERR '+str(e))); pg.on('console', lambda m: logs.append(m.type+': '+m.text[:160]))
        await pg.goto(BASE+'/index.html?test=1')
        await pg.evaluate("localStorage.clear()")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.evaluate("window.__mirror.pickChar(0)")
        await pg.click('#voicebtn'); await pg.wait_for_timeout(1500)
        st = await pg.evaluate("({on:window.__mirror.voice.on, preset:window.__mirror.VP.preset, btn:document.getElementById('voicebtn').textContent, status:document.getElementById('status').textContent})")
        print(st)
        jaws=[]
        for i in range(12):
            jaws.append(round(await pg.evaluate("window.__mirror.S.jaw"),2)); await pg.wait_for_timeout(100)
        print('jaw over time:', jaws)
        await pg.screenshot(path=str(OUT/'voice_panel.png'))
        # switch to robot via character (match on) and check preset follows
        await pg.evaluate("window.__mirror.pickChar(5)")
        print('after robot pick:', await pg.evaluate("window.__mirror.VP.preset"))
        # chipmunk, record 2.5 s, decode the clip's audio and measure its pitch
        await pg.select_option('#vPreset','chipmunk'); await pg.wait_for_timeout(300)
        await pg.click('#rec'); await pg.wait_for_timeout(3000); await pg.click('#rec'); await pg.wait_for_timeout(1500)
        res = await pg.evaluate("""async()=>{
          const a=document.getElementById('clipsave'); const blob=await (await fetch(a.href)).blob();
          const ac=new OfflineAudioContext(1,48000,48000);
          let buf; try{ buf=await ac.decodeAudioData(await blob.arrayBuffer()); }catch(e){ return {size:blob.size,type:blob.type,err:String(e)}; }
          const d=buf.getChannelData(0), sr=buf.sampleRate;
          // loudest 0.3 s window, then DFT scan
          let bi=0,be=0; const W=Math.round(sr*.3); for(let i=0;i+W<d.length;i+=Math.round(sr*.05)){ let e=0; for(let k=0;k<W;k+=4) e+=d[i+k]*d[i+k]; if(e>be){be=e;bi=i;} }
          const seg=d.slice(bi,bi+W); let best=0,bf=0;
          for(let f=80;f<900;f+=1){ let re=0,im=0; for(let i=0;i<seg.length;i+=2){ const a=2*Math.PI*f*i/sr; re+=seg[i]*Math.cos(a); im+=seg[i]*Math.sin(a);} const m=re*re+im*im; if(m>best){best=m;bf=f;} }
          return {size:blob.size,type:blob.type,dur:buf.duration.toFixed(2),peakHz:bf,expectedHz:Math.round(200*Math.pow(2,11/12))};
        }""")
        print('clip:', res)
        print([l for l in logs if 'favicon' not in l and '404' not in l])
        await b.close()
asyncio.run(main())
