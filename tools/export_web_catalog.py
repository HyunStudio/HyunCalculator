"""Export the offline catalog and standalone JS formulas for the shared UI."""
import json
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator import __version__
from hyuncalculator.operations import GROUPS
from hyuncalculator import legacy_ml
from hyuncalculator.codegen import catalog,generate,GenerationOptions
root=Path(__file__).resolve().parents[1]/'hyuncalculator'/'webui'
(root/'formulas').mkdir(exist_ok=True)
registry={f.function:f for f in catalog()}
items=[]
for group,ops in GROUPS.items():
 for op in ops:
  en=legacy_ml.EN_OPERATIONS[op.compute.__name__]
  formula=registry.get(op.compute.__name__)
  outputs=[]
  if formula:
   sample=op.compute(dict(formula.fields))
   for key,value in (sample.items() if isinstance(sample,dict) else [('Result',sample)]):
    array=np.asarray(value)
    outputs.append({'label':key,'size':int(array.size),'shape':list(array.shape)})
  items.append({'id':op.compute.__name__,'group':group,'ko':op.title,'en':en[0],'description':{'ko':op.description,'en':en[1]},'formula':op.formula,'code':formula.id if formula else None,'function':({'qf_target':'target_portfolio','fin_irr':'calculate_irr'}.get(op.compute.__name__,op.compute.__name__.removeprefix('fin_').removeprefix('qf_'))),'outputs':outputs,'fields':[{'key':f.key,'ko':f.label,'en':en[3].get(f.key,f.label),'example':f.example} for f in op.fields]})
(root/'catalog.json').write_text(json.dumps({'version':__version__,'operations':items},ensure_ascii=False,indent=2),encoding='utf-8')
for formula in catalog():
 (root/'formulas'/(formula.id+'.mjs')).write_text(generate(formula.id,GenerationOptions(language='JavaScript')),encoding='utf-8')
print(f'Exported {len(items)} calculators and {len(registry)} offline formula modules')
