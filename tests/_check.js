// Tiny shared helper for the Node checks: print PASS/FAIL per check, exit nonzero if any failed.
const fails=[];
function check(ok,label,detail){ console.log((ok?'PASS  ':'FAIL  ')+label+(detail!==undefined?'  ('+detail+')':'')); if(!ok) fails.push(label); return ok; }
function finish(){ if(fails.length){ console.log('\n'+fails.length+' check(s) FAILED: '+fails.join('; ')); process.exit(1); } console.log('\nAll checks passed.'); }
module.exports={check,finish};
