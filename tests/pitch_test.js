// Pitch accuracy of the shipped WSOLA shifter: feeds a 220 Hz tone through the real worklet code and measures the output pitch.
// Run: node tests/pitch_test.js
const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const src=html.split('const SHIFTER_SRC=`')[1].split('`;')[0];
let Proc; global.sampleRate=48000;
global.AudioWorkletProcessor=class{}; global.registerProcessor=(n,c)=>{Proc=c;};
eval(src);
function run(semi,wob=0,ring=0){
  const p=new Proc(); const sr=48000, secs=1.0, n=sr*secs, f0=220;
  const out=new Float32Array(n);
  const P={pitch:[Math.pow(2,semi/12)],ring:[ring],ringFreq:[55],wobble:[wob],gate:[.006]};
  for(let b=0;b<n;b+=128){
    const inp=new Float32Array(128), o=new Float32Array(128);
    for(let i=0;i<128;i++) inp[i]=.5*Math.sin(2*Math.PI*f0*(b+i)/sr);
    p.process([[inp]],[[o]],P); out.set(o,b);
  }
  // estimate dominant frequency over the last 0.5 s with a DFT scan
  const seg=out.slice(n/2); let best=0,bf=0;
  for(let f=50;f<1200;f+=1){ let re=0,im=0; for(let i=0;i<seg.length;i+=2){ const a=2*Math.PI*f*i/sr; re+=seg[i]*Math.cos(a); im+=seg[i]*Math.sin(a);} const m=re*re+im*im; if(m>best){best=m;bf=f;} }
  let rms=0; for(const v of seg) rms+=v*v; rms=Math.sqrt(rms/seg.length);
  return {semi,expected:+(f0*Math.pow(2,semi/12)).toFixed(1),measured:bf,rms:+rms.toFixed(3)};
}
for(const s of [0,3.5,5,8,11,12,-4,-5.5,-10,-12]) console.log(JSON.stringify(run(s)));
// gate: silence in stays silent, NaN check
const p=new Proc(); const o=new Float32Array(128); p.process([[new Float32Array(128)]],[[o]],{pitch:[1.5],ring:[.8],ringFreq:[55],wobble:[.5],gate:[.006]});
console.log('silence max', Math.max(...o.map(Math.abs)), 'nan', o.some(Number.isNaN));
