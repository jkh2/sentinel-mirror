// CHECK: the gentle noise gate must not chop speech.
// A speech-like signal (syllables of varied loudness, soft tails, short dips) at three mic volumes goes through the
// shipped worklet at pitch 1 with the app's default gate threshold. We count 10 ms speaking moments that come out
// more than 6 dB quieter than they went in ("muted").
// Pass criteria: at most 1% of speaking moments muted at each volume (x1, x0.5, x0.25).
// For reference, the old gate (30 ms release, closing to zero) measured 4.3% / 11.2% / 41.9%.
// Run: node tests/gate_test.js
const fs=require('fs'), path=require('path');
const {check,finish}=require('./_check.js');
const sr=48000;
function speech(n){
  const out=new Float32Array(n); let t=0; let seed=3; const rnd=()=>(seed=(seed*16807)%2147483647)/2147483647;
  while(t<n){
    const len=Math.round(sr*(.12+rnd()*.18)), amp=.015+rnd()*.06, gap=Math.round(sr*(rnd()<.8?.03+rnd()*.06:.25+rnd()*.2));
    const f=110+rnd()*60;
    for(let i=0;i<len&&t+i<n;i++){ const e=Math.sin(Math.PI*i/len)**.7; let x=0; for(let h=1;h<6;h++) x+=Math.sin(2*Math.PI*f*h*(t+i)/sr)/h; out[t+i]=x*amp*e*.6; }
    t+=len+gap;
  }
  return out;
}
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const core=html.split('const SHIFTER_SRC=`')[1].split('`;')[0];
const gateDefault=+core.match(/name:'gate',defaultValue:([\d.]+)/)[1];
global.sampleRate=sr; let Proc; global.AudioWorkletProcessor=class{}; global.registerProcessor=(n,c)=>{Proc=c;}; eval(core);
function mutedPct(src){
  const p=new Proc(), n=src.length, out=new Float32Array(n);
  const P={pitch:[1],ring:[0],ringFreq:[55],wobble:[0],gate:[gateDefault]};
  for(let b=0;b<n;b+=128){ const o=new Float32Array(128); p.process([[src.subarray(b,b+128)]],[[o]],P); out.set(o,b); }
  let speakFrames=0, cut=0; const F=480;
  for(let i=0;i+F<n;i+=F){ let a=0,b=0; for(let k=0;k<F;k++){ a+=src[i+k]**2; b+=out[i+k]**2; } if(a/F>1e-6){ speakFrames++; if(b<a*.25) cut++; } }
  return {pct:cut/speakFrames*100, cut, speakFrames};
}
console.log('Gate threshold under test (worklet default): '+gateDefault+'\nRaw measurements:');
const res=[1,.5,.25].map(vol=>({vol,...mutedPct(speech(sr*8).map(v=>v*vol))}));
res.forEach(r=>console.log('  mic volume x'+r.vol+': '+r.pct.toFixed(1)+'% muted ('+r.cut+' of '+r.speakFrames+' speaking moments)'));
console.log('');
for(const r of res) check(r.pct<=1,'speech not chopped at mic volume x'+r.vol, r.pct.toFixed(1)+'% muted, limit 1%');
finish();
