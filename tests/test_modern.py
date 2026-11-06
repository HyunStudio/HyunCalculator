"""Integration checks for the shared desktop UI's calculation boundary."""
import json
import threading
import shutil
import subprocess
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from hyuncalculator.modern import Handler,ThreadingHTTPServer,compute,serializable,ASSETS
from hyuncalculator.operations import GROUPS
from hyuncalculator.codegen import generate,GenerationOptions,catalog

class ModernIntegrationTests(unittest.TestCase):
 def test_every_registered_calculator_routes_with_sample_inputs(self):
  count=0
  for group,operations in GROUPS.items():
   for op in operations:
    with self.subTest(operation=op.compute.__name__):
     result=compute({'operation':op.compute.__name__,'fields':{f.key:f.example for f in op.fields}})
     json.dumps(serializable(result),allow_nan=False);count+=1
  self.assertEqual(count,57)
 def test_offline_assets_match_the_current_engine(self):
  data=json.loads((ASSETS/'catalog.json').read_text(encoding='utf-8'))
  self.assertEqual(len(data['operations']),57)
  for formula in catalog():
   with self.subTest(formula=formula.id):
    self.assertEqual((ASSETS/'formulas'/(formula.id+'.mjs')).read_text(encoding='utf-8'),generate(formula.id,GenerationOptions(language='JavaScript')))
 def test_large_integer_and_nonfinite_json(self):
  self.assertEqual(serializable(2**64-1),str(2**64-1))
  self.assertIsNone(serializable(float('nan')))
 @unittest.skipUnless(shutil.which('node'),'Node required for offline parser checks')
 def test_offline_arithmetic_and_rejection(self):
  source="""import {evaluate} from 'MODULE';
const cases=[['-2^2',-4],['2^3^2',512],['sin(pi/6)+sqrt(16)',4.5],['log(1000)+ln(e)',4],['comb(5,2)',10],['5!',120]];
for(const [expression,expected] of cases)if(Math.abs(evaluate(expression)-expected)>1e-10)throw Error(expression);
if(Math.abs(evaluate('sin(30)',true)-.5)>1e-10)throw Error('degree mode');
for(const expression of ['globalThis.process.exit()','1/0','sqrt(-1)','2;3','factorial(171)']){let rejected=false;try{evaluate(expression);}catch{rejected=true;}if(!rejected)throw Error('accepted '+expression);}
""".replace('MODULE',(ASSETS/'mathsafe.mjs').as_uri())
  result=subprocess.run(['node','--input-type=module','-e',source],capture_output=True,text=True,timeout=30)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_http_boundary_and_scientific_result(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  base=f'http://127.0.0.1:{server.server_port}'
  try:
   self.assertEqual(json.load(urlopen(base+'/api/status'))['engine'],'python')
   payload=json.dumps({'mode':'scientific','expression':'sin(pi/6)+sqrt(16)'}).encode()
   req=Request(base+'/api/compute',data=payload,headers={'Content-Type':'application/json','Origin':base})
   self.assertEqual(json.load(urlopen(req))['result'],4.5)
   req=Request(base+'/api/compute',data=payload,headers={'Origin':'https://unrelated.example'})
   with self.assertRaises(HTTPError) as error:urlopen(req)
   self.assertEqual(error.exception.code,403);error.exception.close()
   req=Request(base+'/api/compute',data=b'{broken')
   with self.assertRaises(HTTPError) as error:urlopen(req)
   self.assertEqual(error.exception.code,400);error.exception.close()
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
