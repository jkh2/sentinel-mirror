"""CHECK + VISUAL REVIEW: renders all six characters in six expressions (no camera, via the window.__mirror test hook).
Pass criteria: six characters; each of the 36 renders actually draws (head pixel differs from background, PNG not blank);
no page errors. Screenshots go to tests/out/ for review by eye. Looking right is a human judgment, not asserted.
Needs: python3 -m http.server 8765 (repo root).  Run: python3 tests/render_test.py"""
import os, sys, pathlib, asyncio
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _check import check, finish, page_errors
OUT=HERE/"out"; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get("CHROME","/usr/bin/google-chrome")
BASE=os.environ.get("MIRROR_URL","http://localhost:8765")
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
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width":560,"height":560})
        logs=[]
        pg.on("pageerror", lambda e: logs.append(str(e)))
        pg.on("console", lambda m: logs.append("console: "+m.text) if m.type=="error" else None)
        await pg.goto(BASE+"/index.html?test=1")
        await pg.wait_for_timeout(500)
        names = await pg.evaluate("window.__mirror.CHARS.map(c=>c.id)")
        drawn, missing = 0, []
        for ci,n in enumerate(names):
            for pn,p in POSES.items():
                await pg.evaluate(JS, [ci, p])
                await pg.wait_for_timeout(80)
                f = OUT/f"shot_{n}_{pn}.png"
                await pg.screenshot(path=str(f))
                # something must be drawn across the head: scan a vertical line through the head and take the biggest
                # color difference from the background at a top corner (a single pixel can match, e.g. robot's dark screen)
                diff = await pg.evaluate("""()=>{ const c=document.getElementById('c'), x=c.getContext('2d'), d=window.devicePixelRatio||1;
                  const px=(X,Y)=>x.getImageData(Math.round(X*d),Math.round(Y*d),1,1).data, b=px(6, 70); let mx=0;
                  for(let k=0;k<40;k++){ const a=px(innerWidth/2, innerHeight*(0.22+0.33*k/39)); mx=Math.max(mx,Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])+Math.abs(a[2]-b[2])); }
                  return mx; }""")
                if f.exists() and f.stat().st_size > 15000 and diff > 120: drawn += 1
                else: missing.append(f"{n}/{pn} (bytes {f.stat().st_size if f.exists() else 0}, diff {diff})")
        await pg.goto(BASE+"/index.html")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(OUT/"ui_start.png"))
        total = len(names)*len(POSES)
        print(f"Raw results:\n  characters: {names}\n  expressions: {list(POSES)}\n  screenshots in {OUT}\n")
        check(len(names) == 6, "six characters defined", names)
        check(drawn == total, "every character draws in every expression", f"{drawn}/{total}" + (f"; missing {missing}" if missing else ""))
        check(not page_errors(logs), "no page errors", page_errors(logs))
        print("\nThe checks above only prove each character drew. Whether it LOOKS right is a human call:")
        print("open tests/out/shot_*.png and review by eye (expressions, proportions, nothing resembling a known character).")
        await b.close()
    finish()
asyncio.run(main())
