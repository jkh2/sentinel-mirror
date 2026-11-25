import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio, json
from playwright.async_api import async_playwright
JS = r"""() => {
  const mk=(wx,wy,wv,ev)=>{ const lm=[]; for(let i=0;i<33;i++) lm.push({x:.5,y:.5,visibility:.9});
    lm[11]={x:.6,y:.6,visibility:.95}; lm[12]={x:.4,y:.6,visibility:.95};
    lm[13]={x:.68,y:.75,visibility:ev}; lm[15]={x:wx,y:wy,visibility:wv};
    lm[14]={x:.32,y:.75,visibility:.2}; lm[16]={x:.3,y:.95,visibility:.2};
    return {landmarks:[lm]}; };
  const t=armTrust, out=[]; const A=()=>{ const a=t[0]; return a.wOk?('trusted@'+Math.round(a.w.x)+','+Math.round(a.w.y)):'not trusted'; };
  // note: mirrored, so landmark 15 (subject's left wrist, x=.7) lands on screen-left -> side 0
  let now=1000;
  for(const v of [.3,.5,.2,.6,.4]){ processPose(mk(.7+Math.random()*.1,.5+Math.random()*.2,v,.3),now+=33); }
  out.push('5 unclear guesses: '+A());
  for(let k=0;k<3;k++){ processPose(mk(.72,.55,.9,.9),now+=33); out.push('clear frame '+(k+1)+': '+A()); }
  processPose(mk(.15,.2,.9,.9),now+=33); out.push('one-frame leap: '+A());
  processPose(mk(.72,.56,.9,.9),now+=33); out.push('back to normal: '+A());
  for(let k=0;k<3;k++){ processPose(mk(.4,.3,.9,.9),now+=33); out.push('real move frame '+(k+1)+': '+A()); }
  processPose(mk(.4,.3,.55,.9),now+=33); out.push('a bit unclear (.55): '+A());
  processPose(mk(.4,.3,.35,.9),now+=33); out.push('leaves view (.35): '+A());
  // hands: a giant blob far away is rejected, a normal hand near the trusted wrist needs 2 frames
  for(let k=0;k<3;k++) processPose(mk(.72,.55,.9,.9),now+=33);
  T.hr=60;
  const hand=(cx,cy,sz)=>{ const h=[]; for(let i=0;i<21;i++) h.push({x:cx,y:cy-(i?sz*(1+i%4)/4:0),z:0}); return h; };
  const wpt=armTrust[0].w; const nx=1-(wpt.x/ (innerWidth))/1; 
  processHands({landmarks:[hand(.5,.5,.6)],handednesses:[[{score:.95}]]},now+=33); out.push('giant hand: shown='+!!T.hand[0]);
  return out.join('\n');
}"""
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width':1280,'height':720}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(BASE+'/index.html?test=1'); await pg.wait_for_timeout(300)
        print(await pg.evaluate(JS)); print('errors', errs)
        await b.close()
asyncio.run(main())
