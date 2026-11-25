// Noise-gate test: a speech-like signal (syllables of varied loudness, soft tails, short dips) at three mic volumes.
// Reports how many 10 ms speaking moments the shipped gate mutes. Before the gentle gate it was 4% / 11% / 42%.
// Run: node tests/gate_test.js
const fs=require('fs'), path=require('path'); const sr=48000;
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
global.sampleRate=sr; let Proc; global.AudioWorkletProcessor=class{}; global.registerProcessor=(n,c)=>{Proc=c;}; eval(core);
function run(src){
  const p=new Proc(), n=src.length, out=new Float32Array(n);
  const P={pitch:[1],ring:[0],ringFreq:[55],wobble:[0],gate:[.0035]}; // .0035 is the parameter's default in the app
  for(let b=0;b<n;b+=128){ const o=new Float32Array(128); p.process([[src.subarray(b,b+128)]],[[o]],P); out.set(o,b); }
  let speakFrames=0, cut=0; const F=480;
  for(let i=0;i+F<n;i+=F){ let a=0,b=0; for(let k=0;k<F;k++){ a+=src[i+k]**2; b+=out[i+k]**2; } if(a/F>1e-6){ speakFrames++; if(b<a*.25) cut++; } }
  return (cut/speakFrames*100).toFixed(1)+'% of speaking moments muted';
}
for(const vol of [1,.5,.25]) console.log('mic volume x'+vol+': '+run(speech(sr*8).map(v=>v*vol)));
