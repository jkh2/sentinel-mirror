// CHECK: pitch accuracy of the shipped WSOLA shifter (the AudioWorklet source inside index.html).
// Feeds a 220 Hz tone through the real worklet code at every preset's pitch range and measures the output pitch.
// Pass criteria: measured pitch within max(2 Hz, 1%) of expected; output RMS within 10% of input RMS (no level loss);
// silence in -> exact silence out; no NaN.
// Run: node tests/pitch_test.js
const fs=require('fs'), path=require('path');
const {check,finish}=require('./_check.js');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const src=html.split('const SHIFTER_SRC=`')[1].split('`;')[0];
let Proc; global.sampleRate=48000;
global.AudioWorkletProcessor=class{}; global.registerProcessor=(n,c)=>{Proc=c;};
eval(src);
const sr=48000, f0=220, inRms=.5/Math.SQRT2;
function run(semi,wob=0,ring=0){
  const p=new Proc(), n=sr, out=new Float32Array(n);
  const P={pitch:[Math.pow(2,semi/12)],ring:[ring],ringFreq:[55],wobble:[wob],gate:[.0035]};
  for(let b=0;b<n;b+=128){
    const inp=new Float32Array(128), o=new Float32Array(128);
    for(let i=0;i<128;i++) inp[i]=.5*Math.sin(2*Math.PI*f0*(b+i)/sr);
    p.process([[inp]],[[o]],P); out.set(o,b);
  }
  const seg=out.slice(n/2); let best=0,bf=0;
  for(let f=50;f<1200;f+=1){ let re=0,im=0; for(let i=0;i<seg.length;i+=2){ const a=2*Math.PI*f*i/sr; re+=seg[i]*Math.cos(a); im+=seg[i]*Math.sin(a);} const m=re*re+im*im; if(m>best){best=m;bf=f;} }
  let rms=0; for(const v of seg) rms+=v*v; rms=Math.sqrt(rms/seg.length);
  return {semi,expected:+(f0*Math.pow(2,semi/12)).toFixed(1),measured:bf,rms:+rms.toFixed(3)};
}
console.log('Raw measurements (input 220 Hz, RMS '+inRms.toFixed(3)+'):');
const rows=[0,3.5,5,8,11,12,-4,-5.5,-10,-12].map(s=>run(s));
rows.forEach(r=>console.log('  '+JSON.stringify(r)));
console.log('');
for(const r of rows){
  const tol=Math.max(2,r.expected*.01);
  check(Math.abs(r.measured-r.expected)<=tol, 'pitch '+(r.semi>0?'+':'')+r.semi+' semitones', 'expected '+r.expected+' Hz, measured '+r.measured+' Hz, tolerance '+tol.toFixed(1));
  check(Math.abs(r.rms-inRms)<=inRms*.1, 'level kept at '+(r.semi>0?'+':'')+r.semi+' semitones', 'RMS '+r.rms+' vs input '+inRms.toFixed(3));
}
const p=new Proc(); const o=new Float32Array(128);
p.process([[new Float32Array(128)]],[[o]],{pitch:[1.5],ring:[.8],ringFreq:[55],wobble:[.5],gate:[.0035]});
const mx=Math.max(...o.map(Math.abs));
check(mx===0,'silence in gives silence out','max '+mx);
check(!o.some(Number.isNaN),'no NaN in output');
finish();
