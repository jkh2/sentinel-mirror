"""CHECK: arm and hand trust rules (processPose / processHands in index.html), fed synthetic tracker frames.
Pass criteria: unclear guesses ignored; a clear wrist trusted on the 3rd clear frame, not before; a one-frame leap held
back; a repeated big move accepted on its 3rd frame; trust kept at visibility .55 and dropped at .35; a hand that is
too big, low-confidence, or far from the trusted wrist rejected; a normal hand at the wrist shown on its 2nd frame.
Needs: python3 -m http.server 8765 (repo root).  Run: python3 tests/arm_trust_test.py"""
import os, sys, pathlib, asyncio
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _check import check, finish, page_errors
OUT=HERE/"out"; OUT.mkdir(exist_ok=True)
CHROME=os.environ.get("CHROME","/usr/bin/google-chrome")
BASE=os.environ.get("MIRROR_URL","http://localhost:8765")
from playwright.async_api import async_playwright
JS = r"""() => {
  // landmarks in camera coords; the page mirrors x, so landmark 15 (x=.72) lands on screen-left = side 0
  const mk=(wx,wy,wv,ev)=>{ const lm=[]; for(let i=0;i<33;i++) lm.push({x:.5,y:.5,visibility:.9});
    lm[11]={x:.6,y:.6,visibility:.95}; lm[12]={x:.4,y:.6,visibility:.95};
    lm[13]={x:.68,y:.75,visibility:ev}; lm[15]={x:wx,y:wy,visibility:wv};
    lm[14]={x:.32,y:.75,visibility:.2}; lm[16]={x:.3,y:.95,visibility:.2};
    return {landmarks:[lm]}; };
  const R={}, A=()=>armTrust[0].wOk?{x:Math.round(armTrust[0].w.x),y:Math.round(armTrust[0].w.y)}:null;
  let now=1000, seed=5; const rnd=()=>(seed=(seed*16807)%2147483647)/2147483647;
  for(const v of [.3,.5,.2,.6,.4]) processPose(mk(.7+rnd()*.1,.5+rnd()*.2,v,.3),now+=33);
  R.afterUnclear=A();
  R.clear=[]; for(let k=0;k<3;k++){ processPose(mk(.72,.55,.9,.9),now+=33); R.clear.push(A()); }
  processPose(mk(.15,.2,.9,.9),now+=33); R.leap=A();
  processPose(mk(.72,.56,.9,.9),now+=33); R.back=A();
  R.move=[]; for(let k=0;k<3;k++){ processPose(mk(.4,.3,.9,.9),now+=33); R.move.push(A()); }
  processPose(mk(.4,.3,.55,.9),now+=33); R.vis55=A();
  processPose(mk(.4,.3,.35,.9),now+=33); R.vis35=A();
  // hands: re-trust the wrist at (.72,.55), then try hands. Test page: no video, 1280x720 viewport, so 1 unit = 1280 x 720 px.
  for(let k=0;k<3;k++) processPose(mk(.72,.55,.9,.9),now+=33);
  T.hr=60; T.hand=[null,null]; handSeen[0]=handSeen[1]=0;
  const hand=(cx,cy,sz)=>{ const h=[]; for(let i=0;i<21;i++) h.push({x:cx,y:cy-(i?sz*(1+i%4)/4:0),z:0}); return h; };
  const ok=sc=>[[{score:sc}]];
  processHands({landmarks:[hand(.72,.55,.6)],handednesses:ok(.95)},now+=33); R.giant=!!T.hand[0];
  processHands({landmarks:[hand(.72,.55,.167)],handednesses:ok(.5)},now+=33); R.lowConf=!!T.hand[0];
  processHands({landmarks:[hand(.45,.2,.167)],handednesses:ok(.95)},now+=33); R.far=!!T.hand[0];
  handSeen[0]=0;
  processHands({landmarks:[hand(.72,.55,.167)],handednesses:ok(.95)},now+=33); R.good1=!!T.hand[0];
  processHands({landmarks:[hand(.72,.55,.167)],handednesses:ok(.95)},now+=33); R.good2=!!T.hand[0];
  return R;
}"""
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width":1280,"height":720}); logs=[]; pg.on("pageerror", lambda e: logs.append(str(e)))
        await pg.goto(BASE+"/index.html?test=1"); await pg.wait_for_timeout(300)
        R = await pg.evaluate(JS)
        print("Raw results:"); [print("  ",k,"=",v) for k,v in R.items()]; print()
        check(R["afterUnclear"] is None, "5 unclear guesses (visibility <= .6) are ignored", R["afterUnclear"])
        check(R["clear"][0] is None and R["clear"][1] is None and R["clear"][2] is not None, "wrist trusted on the 3rd clear frame, not before", R["clear"])
        check(R["leap"] == R["clear"][2], "one-frame leap across the body is held back", R["leap"])
        check(R["back"] is not None and abs(R["back"]["y"]-R["clear"][2]["y"]) < 20, "normal small move after the glitch is accepted", R["back"])
        check(R["move"][0] == R["back"] and R["move"][1] == R["back"] and R["move"][2] != R["back"], "repeated big move accepted on its 3rd frame", R["move"])
        check(R["vis55"] is not None, "trust kept when visibility dips to .55 (hysteresis)")
        check(R["vis35"] is None, "trust dropped when visibility falls to .35")
        check(not R["giant"], "hand far too big for the face is rejected")
        check(not R["lowConf"], "low-confidence hand (score .5) is rejected")
        check(not R["far"], "hand far from the trusted wrist is rejected")
        check(not R["good1"] and R["good2"], "normal hand at the wrist is shown on its 2nd frame, not the 1st", (R["good1"], R["good2"]))
        check(not page_errors(logs), "no page errors", page_errors(logs))
        await b.close()
    finish()
asyncio.run(main())
