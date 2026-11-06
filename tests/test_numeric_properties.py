"""Generated Python/JavaScript boundary, randomized and invariant checks."""
import json
import math
import random
import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path
from hyuncalculator.codegen import generate, GenerationOptions

class GeneratedNumericalProperties(unittest.TestCase):
    def test_npv_class_loop_import_combinations(self):
        for loop in ('for','while'):
            for imports in ('auto','standard'):
                namespace={}
                exec(generate('FIN-004',GenerationOptions(structure='class',iteration=loop,imports=imports,class_name='Cashflows')),namespace)
                for rate,flows in [(0.,[-100.,60.,60.]),(.1,[-100.,60.,60.]),(-.2,[1.,2.,3.]),(.2,[])]:
                    expected=sum(cf/(1+rate)**t for t,cf in enumerate(flows))
                    self.assertAlmostEqual(namespace['Cashflows'].npv(rate,flows),expected)

    def test_python_seeded_time_value_invariants(self):
        functions={}
        for fid,name in [('FIN-001','fv'),('FIN-002','pv'),('FIN-003','pmt'),('FIN-009','annuity')]:
            ns={};exec(generate(fid),ns);functions[name]=ns[name]
        rng=random.Random(20261106)
        for _ in range(100):
            principal=rng.uniform(1,1e6);rate=rng.uniform(-.03,.15);n=rng.randint(1,120)
            future=functions['fv'](principal,rate,n)
            self.assertTrue(math.isclose(functions['pv'](future,rate,n),principal,rel_tol=1e-10))
            payment=functions['pmt'](principal,rate,n)
            self.assertTrue(math.isclose(functions['annuity'](payment,rate,n),principal,rel_tol=1e-9))
        self.assertEqual(functions['pmt'](1200,0,12),100)
        self.assertEqual(functions['annuity'](100,0,12),1200)

    @unittest.skipUnless(shutil.which('node'),'Node.js required for generated JavaScript properties')
    def test_javascript_seeded_boundaries_and_parity(self):
        rng=random.Random(20261106)
        vectors=[[rng.uniform(1,1e5),rng.uniform(-.03,.15),rng.randint(1,120)] for _ in range(100)]
        scripts=[]
        for loop in ('for','while'):
            scripts.append(generate('FIN-004',GenerationOptions(language='JavaScript',structure='class',iteration=loop,class_name='Cashflows'+loop)))
        for fid in ('FIN-001','FIN-002','FIN-003','FIN-009','DERIV-001'):
            scripts.append(generate(fid,GenerationOptions(language='JavaScript')))
        scripts.append('''
function assert(ok,message){if(!ok)throw new Error(message);}
function close(a,b){return Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=1e-8*Math.max(1,Math.abs(b));}
for(const [principal,rate,n] of VECTORS){
 assert(close(pv(fv(principal,rate,n),rate,n),principal),'PV/FV');
 assert(close(annuity(pmt(principal,rate,n),rate,n),principal),'payment/annuity');
}
assert(pmt(1200,0,12)===100,'zero-rate payment');
assert(annuity(100,0,12)===1200,'zero-rate annuity');
for(const rate of [0,.1,-.2]){
 const expected=-100+60/(1+rate)+60/(1+rate)**2;
 assert(close(Cashflowsfor.npv(rate,[-100,60,60]),expected),'for NPV');
 assert(close(Cashflowswhile.npv(rate,[-100,60,60]),expected),'while NPV');
}
for(let i=0;i<100;i++){
 const s=50+i,k=100,t=.1+i/100,r=.03,q=.01,vol=.2;
 const call=bs(s,k,t,r,vol,q,'call'),put=bs(s,k,t,r,vol,q,'put');
 assert(close(call[0]-put[0],s*Math.exp(-q*t)-k*Math.exp(-r*t)),'put-call parity');
 assert(call[0]>=0&&put[0]>=0,'nonnegative option price');
 assert(close(call[2],put[2])&&close(call[3],put[3]),'shared gamma/vega');
}
assert(bs(120,100,0,.03,.2,0,'call')[0]===20,'expiry intrinsic value');
assert(close(bs(120,100,1,.03,0,0,'call')[0],120-100*Math.exp(-.03)),'zero-volatility option');
for(const call of [()=>pmt(100,-1,12),()=>fv(100,.1,-1),()=>bs(0,100,1,.03,.2,0,'call')]){
 let rejected=false;try{call();}catch(e){rejected=e instanceof RangeError;}
 assert(rejected,'invalid input rejection');
}
console.log('PROPERTY CHECKS PASSED');
'''.replace('VECTORS',json.dumps(vectors)))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'properties.mjs';path.write_text('\n'.join(scripts),encoding='utf-8')
            result=subprocess.run(['node',str(path)],text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('PROPERTY CHECKS PASSED',result.stdout)

if __name__=='__main__':unittest.main()
