// DIAGNOSTIC ONLY (no pass/fail): shows why we do not use the simple two-tap delay-line pitch shifter.
// How much energy lands on the target pitch depends wildly on how the voice period lines up with the window
// (6% to 100%). This is a self-contained copy of that old algorithm, not the shipped code. Compare with pitch_test.js.
// Run: node tests/naive_shifter_comparison.js
// compare: how much of the output energy lands on the intended pitch (voice-like harmonic input)
const sr=48000;
function makeProc(N, smart){
  const size=1<<Math.ceil(Math.log2(N*3+8)), mask=size-1, buf=new Float32Array(size);
  let w=0, ph=0;
  const read=d=>{const p=w-d,i=Math.floor(p),f=p-i,a=buf[i&mask],b=buf[(i+1)&mask];return a+(b-a)*f;};
  return (x,r)=>{
    buf[w]=x;
    ph+=(1-r)/N; ph-=Math.floor(ph);
    const p2=(ph+.5)%1, w1=Math.sin(Math.PI*ph), w2=Math.sin(Math.PI*p2);
    const y=read(ph*N+2)*w1*w1+read(p2*N+2)*w2*w2;
    w=(w+1)&mask; return y;
  };
}
function test(N,semi){
  const pr=makeProc(N); const r=Math.pow(2,semi/12), f0=150, n=sr;
  const out=new Float32Array(n);
  for(let i=0;i<n;i++){ let x=0; for(let h=1;h<=6;h++) x+=Math.sin(2*Math.PI*f0*h*i/sr)/h; out[i]=pr(x*.3,r); }
  const seg=out.slice(n/2), L=seg.length;
  const mag=f=>{let re=0,im=0;for(let i=0;i<L;i+=2){const a=2*Math.PI*f*i/sr;re+=seg[i]*Math.cos(a);im+=seg[i]*Math.sin(a);}return re*re+im*im;};
  let tot=0,on=0; const target=f0*r;
  for(let f=40;f<1400;f+=2){ const m=mag(f); tot+=m; for(let h=1;h<=6;h++) if(Math.abs(f-target*h)<=4) on+=m; }
  return (on/tot*100).toFixed(0)+'%';
}
for(const ms of [30,50,80,100]) console.log(ms+'ms', [12,7,4,-4,-7,-12].map(s=>s+':'+test(Math.round(sr*ms/1000),s)).join('  '));
