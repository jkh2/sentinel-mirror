import os, sys, pathlib
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'out'; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
BASE=os.environ.get('MIRROR_URL','http://localhost:8765')
import asyncio, json, sys
from playwright.async_api import async_playwright
POSES = {
 'neutral': dict(yaw=0.0, pitch=0.0, smileL=.25, smileR=.25),
 'happy_wave': dict(yaw=-.25, pitch=.1, roll=-.12, smileL=.9, smileR=.9, jaw=.55, browInner=.3, hands='wave'),
 'wink_turn': dict(yaw=.6, pitch=-.15, roll=.18, blinkL=1, smileL=.6, smileR=.5, browDownR=.6, lookX=.6),
 'surprise': dict(yaw=0, pitch=.25, jaw=.85, wideL=1, wideR=1, browInner=1, browOuterL=1, browOuterR=1, funnel=.4, armsUp=True),
 'angry': dict(yaw=-.1, browDownL=1, browDownR=1, frownL=.8, frownR=.8, sneer=.8, squintL=.6, squintR=.6),
 'kiss_puff': dict(yaw=.2, pucker=1, funnel=.6, puff=.9, blinkL=.95, blinkR=.95, smileL=.4, smileR=.4),
}
JS = r"""
([ci, p]) => {
  const M = window.__mirror; M.pickChar(ci); M.setBg(0);
  const W = M.W, H = M.H, hx=W/2, hy=H*0.38, hr=Math.min(W,H)*0.13;
  const o = Object.assign({hx, hy, hr}, p);
  delete o.hands; delete o.armsUp;
  const sA={x:hx-hr*2.05,y:hy+hr*2.4}, sB={x:hx+hr*2.05,y:hy+hr*2.4};
  o.sA=sA; o.sB=sB;
  const sw=hr*4.1, l1=sw*.72, l2=sw*.66;
  let wA={x:sA.x-sw*.1,y:sA.y+l1+l2*.9}, wB={x:sB.x+sw*.1,y:sB.y+l1+l2*.9};
  function openHand(w, ang, size, mirrorX){
    const pts=[w]; const dirs=[-1.0,-0.45,-0.12,0.18,0.48];
    const lens=[[.5,.85,1.15,1.4],[1.0,1.45,1.75,2.0],[1.0,1.55,1.9,2.15],[.95,1.45,1.75,1.95],[.85,1.2,1.45,1.65]];
    for(let f=0;f<5;f++){ const a=ang+dirs[f]*(mirrorX?-1:1); for(let j=0;j<4;j++){ const L=lens[f][j]*size; pts.push({x:w.x+Math.sin(a)*L,y:w.y-Math.cos(a)*L}); } }
    return pts;
  }
  if(p.hands==='wave'){ wB={x:sB.x+sw*.35,y:sB.y-sw*.55}; o.hand=[null, openHand(wB, .25, hr*.32, false)]; }
  if(p.armsUp){ wA={x:sA.x-sw*.45,y:sA.y-sw*.65}; wB={x:sB.x+sw*.45,y:sB.y-sw*.65}; }
  o.wA=wA; o.wB=wB; o.eA=M.solveElbow(sA,wA,l1,l2,0); o.eB=M.solveElbow(sB,wB,l1,l2,1);
  const hand=o.hand; delete o.hand;
  M.pose(o); if(hand) M.S.hand=hand;
}
"""
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width':560,'height':560})
        errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console:'+m.text) if m.type=='error' else None)
        await pg.goto(BASE+'/index.html?test=1')
        await pg.wait_for_timeout(500)
        names = await pg.evaluate("window.__mirror.CHARS.map(c=>c.id)")
        for ci,n in enumerate(names):
            for pn,p in POSES.items():
                await pg.evaluate(JS, [ci, p])
                await pg.wait_for_timeout(80)
                await pg.screenshot(path=str(OUT/f'shot_{n}_{pn}.png'))
        # also the start screen and UI
        await pg.goto(BASE+'/index.html')
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(OUT/'ui_start.png'))
        print('errors:', errs)
        await b.close()
asyncio.run(main())
