"""Conservative, AST-based emitters for the first v1.2.0 vertical slice.

No generated code is executed here. Only explicitly modeled formulas are
exportable, and this implementation refuses unverified option combinations.
"""
from __future__ import annotations

import ast
import keyword
import re
from dataclasses import dataclass

from .registry import get_formula

LANGUAGES = ('Python','R','C','C++','JavaScript','TypeScript','Java','C#',
             'Swift','Kotlin','Go','Rust','MATLAB','Julia')
EXTENSIONS = dict(zip(LANGUAGES,('py','R','c','cpp','js','ts','java','cs','swift','kt','go','rs','m','jl')))
CLASS_LANGUAGES = frozenset(('Python','C++','JavaScript','TypeScript','Java','C#','Swift','Kotlin'))

@dataclass(frozen=True)
class GenerationOptions:
    language: str='Python'
    structure: str='function'  # function or class (only for supported languages)
    iteration: str='auto'    # auto/for/while (NPV only)
    imports: str='auto'      # auto or standard
    function_name: str|None=None
    variant: str='periodic'  # FIN-001 only: periodic or continuous
    class_name: str='GeneratedCalculator'
    variable_names: tuple[tuple[str,str],...] = ()  # canonical source name -> emitted identifier

class GenerationError(ValueError):
    pass

# (Python expression, argument names, argument integer names, invalid input conditions)
SCALARS = {
    'fin_fv':('pv * (1 + rate)**n', ('pv','rate','n'), ('n',), ('n < 0','rate <= -1')),
    'fin_pv':('fv / (1 + rate)**n', ('fv','rate','n'), ('n',), ('n < 0','rate <= -1')),
    'fin_pmt':('principal / n if abs(rate) < 1e-14 else principal * rate / (1 - (1 + rate)**(-n))',
               ('principal','rate','n'),('n',),('principal < 0','rate <= -1','n <= 0')),
    'fin_cagr':('(end / start)**(1 / years) - 1', ('start','end','years'),(),
                ('start <= 0','end < 0','years <= 0')),
    'fin_effective':('(1 + rate / m)**m - 1', ('rate','m'),('m',),('m <= 0','rate / m <= -1')),
    'fin_annuity':('payment * n if abs(rate) < 1e-14 else payment * (1 - (1 + rate)**(-n)) / rate',
                   ('payment','rate','n'),('n',),('n <= 0','rate <= -1')),
}

# Reserve broadly to avoid unsupported identifiers in the first phase.
RESERVED = frozenset((keyword.kwlist + ['class','function','func','fn','fun','let','var','const','default',
                   'import','package','module','end','while','for','if','else','return','do','new',
                   'public','private','static','namespace','operator','def','int','double','float',
                   'String','Object','Array','list','vector','match','switch','export','struct',
                   'main','true','false','null','nil','None','self','this','super',
                   'type','float64','Double','continue','break','goto','var','use','mod','pub',
                   'crate','impl','trait','enum','when','override','interface','extends',
                   'await','async','yield','record','final','template','constexpr','volatile',
                   'mut','throws','protocol','struct','switch','case','new','object',
                   'open','sealed','internal','extern','typeof','delete','try','catch',
                   'boolean','long','short','char','void','bool','using','typedef','static_cast']))


def _check_options(formula, opt):
    if formula is None: raise GenerationError('Unknown Formula ID')
    if not formula.exportable:
        raise GenerationError(f'{formula.id} ({formula.title_en}) is registered but its code adapter is not yet implemented')
    if opt.language not in LANGUAGES: raise GenerationError('Unsupported language')
    if opt.language not in formula.supported_languages:
        raise GenerationError(f'{formula.id}: {opt.language} adapter not implemented (Python available)')
    if opt.structure not in ('function','class'): raise GenerationError('Structure must be function or class')
    if opt.structure=='class': _identifier(opt.class_name)
    if opt.structure=='class' and opt.language not in CLASS_LANGUAGES:
        raise GenerationError(f'{opt.language} class architecture is not implemented; select function')
    if opt.iteration not in ('auto','for','while'):
        raise GenerationError('Iteration must be auto, for, or while')
    if formula.function!='fin_npv' and opt.iteration not in ('auto',):
        raise GenerationError('Explicit loops apply to NPV; use auto for this analytic formula')
    if opt.structure=='class' and formula.function=='fin_npv':
        raise GenerationError('NPV class architecture is not implemented yet; use function')
    if opt.imports not in ('auto','standard'):
        raise GenerationError('Only automatic or standard-library imports are implemented')
    if opt.variant not in ('periodic','continuous') or (formula.function!='fin_fv' and opt.variant!='periodic'):
        raise GenerationError('Continuous variant applies only to Future Value')


def _identifier(s):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',s) or s in RESERVED or s.startswith('__') or len(s)>80:
        raise GenerationError(f'Invalid or reserved function name: {s!r}')
    return s


class ExpressionEmitter:
    def __init__(self,language,integer_names=(),rename=None):
        self.lang=language
        self.intnames=frozenset(integer_names)
        self.rename=rename or {}

    def name(self,n):
        named=self.rename.get(n,n)
        if n in self.intnames:
            if self.lang=='Go': return f'float64({named})'
            if self.lang=='Rust': return f'({named} as f64)'
            if self.lang=='Kotlin': return f'{named}.toDouble()'
            if self.lang=='Swift': return f'Double({named})'
        return named

    def call(self,func,arg):
        if func=='exp':
            return {'Python':f'math.exp({arg})','C++':f'std::exp({arg})','JavaScript':f'Math.exp({arg})',
                    'TypeScript':f'Math.exp({arg})','Java':f'Math.exp({arg})','C#':f'Math.Exp({arg})',
                    'Swift':f'exp({arg})','Kotlin':f'exp({arg})','Go':f'math.Exp({arg})',
                    'Rust':f'({arg}).exp()','MATLAB':f'exp({arg})',
                    'Julia':f'exp({arg})','R':f'exp({arg})','C':f'exp({arg})'}[self.lang]
        if func=='sqrt':
            return {'Python':f'math.sqrt({arg})','C':f'sqrt({arg})','C++':f'std::sqrt({arg})',
                    'JavaScript':f'Math.sqrt({arg})','TypeScript':f'Math.sqrt({arg})',
                    'Java':f'Math.sqrt({arg})','C#':f'Math.Sqrt({arg})','Swift':f'sqrt({arg})',
                    'Kotlin':f'sqrt({arg})','Go':f'math.Sqrt({arg})','Rust':f'({arg}).sqrt()',
                    'R':f'sqrt({arg})','MATLAB':f'sqrt({arg})','Julia':f'sqrt({arg})'}[self.lang]
        if func=='abs':
            return {'Python':f'abs({arg})','C':f'fabs({arg})','C++':f'std::abs({arg})',
                    'JavaScript':f'Math.abs({arg})','TypeScript':f'Math.abs({arg})',
                    'Java':f'Math.abs({arg})','C#':f'Math.Abs({arg})','Swift':f'abs({arg})',
                    'Kotlin':f'abs({arg})','Go':f'math.Abs({arg})','Rust':f'({arg}).abs()',
                    'R':f'abs({arg})','MATLAB':f'abs({arg})','Julia':f'abs({arg})'}[self.lang]
        raise GenerationError(f'Unapproved call {func}')

    def pow(self,a,b):
        if self.lang in ('Python','R','MATLAB','Julia'):return f'({a} ^ {b})' if self.lang!='Python' else f'({a} ** {b})'
        if self.lang=='C':return f'pow({a}, {b})'
        if self.lang=='C++':return f'std::pow({a}, {b})'
        if self.lang in ('JavaScript','TypeScript','Java'):return f'Math.pow({a}, {b})'
        if self.lang=='C#':return f'Math.Pow({a}, {b})'
        if self.lang=='Swift':return f'pow({a}, {b})'
        if self.lang=='Kotlin':return f'({a}).pow({b})'
        if self.lang=='Go':return f'math.Pow({a}, {b})'
        if self.lang=='Rust':return f'({a}).powf({b})'
        raise AssertionError('Language not mapped')

    def emit(self,source):
        node=ast.parse(source,mode='eval').body if isinstance(source,str) else source
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            return repr(float(node.value))
        if isinstance(node,ast.Name) and not node.id.startswith('_'):return self.name(node.id)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            return ('-' if isinstance(node.op,ast.USub) else '+')+f'({self.emit(node.operand)})'
        if isinstance(node,ast.BinOp):
            a,b=self.emit(node.left),self.emit(node.right)
            if isinstance(node.op,ast.Pow):return self.pow(a,b)
            syms={ast.Add:'+',ast.Sub:'-',ast.Mult:'*',ast.Div:'/'}
            if type(node.op) not in syms:raise GenerationError('Unsupported expression operator')
            return f'({a} {syms[type(node.op)]} {b})'
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('exp','abs','sqrt') and len(node.args)==1 and not node.keywords:
            return self.call(node.func.id,self.emit(node.args[0]))
        if isinstance(node,ast.Compare) and len(node.ops)==1 and len(node.comparators)==1:
            op={ast.Lt:'<',ast.LtE:'<=',ast.Gt:'>',ast.GtE:'>=',ast.Eq:'==',ast.NotEq:'!='}
            if type(node.ops[0]) not in op: raise GenerationError('Bad comparator')
            return f'({self.emit(node.left)} {op[type(node.ops[0])]} {self.emit(node.comparators[0])})'
        if isinstance(node,ast.IfExp):
            test,yes,no=(self.emit(node.test),self.emit(node.body),self.emit(node.orelse))
            if self.lang=='Python':return f'({yes} if {test} else {no})'
            if self.lang=='R':return f'(if ({test}) {yes} else {no})'
            if self.lang=='Kotlin':return f'(if ({test}) {yes} else {no})'
            if self.lang=='Rust':return f'(if {test} {{ {yes} }} else {{ {no} }})'
            if self.lang=='Go':raise GenerationError('Go conditional expression must be handled as an if/return block')
            if self.lang=='MATLAB':raise GenerationError('MATLAB conditional expression must be handled as an if/else block')
            if self.lang=='Julia':return f'({test} ? {yes} : {no})'
            return f'({test} ? {yes} : {no})'
        raise GenerationError('Unsafe or unsupported formula AST node')


def _param(lang, name, integer):
    ty= 'int' if integer else 'double'
    if lang=='Python':return f'{name}: {"int" if integer else "float"}'
    if lang=='R':return name
    if lang in ('C','C++','Java','C#'):return f'{ty} {name}'
    if lang=='JavaScript':return name
    if lang=='TypeScript':return f'{name}: number'
    if lang=='Swift':return f'_ {name}: {"Int" if integer else "Double"}'
    if lang=='Kotlin':return f'{name}: {"Int" if integer else "Double"}'
    if lang=='Go':return f'{name} {"int" if integer else "float64"}'
    if lang=='Rust':return f'{name}: {"i32" if integer else "f64"}'
    if lang=='MATLAB':return name
    if lang=='Julia':return name
    raise GenerationError('Unsupported language')


def _guard(lang, condition):
    fail={'Python':'raise ValueError("Invalid formula inputs")',
          'R':'stop("Invalid formula inputs")','C':'return NAN;',
          'C++':'throw std::invalid_argument("Invalid formula inputs");',
          'JavaScript':'throw new RangeError("Invalid formula inputs");',
          'TypeScript':'throw new RangeError("Invalid formula inputs");',
          'Java':'throw new IllegalArgumentException("Invalid formula inputs");',
          'C#':'throw new ArgumentOutOfRangeException("Invalid formula inputs");',
          'Swift':'return Double.nan','Kotlin':'throw IllegalArgumentException("Invalid formula inputs")',
          'Go':'return math.NaN()','Rust':'return f64::NAN;',
          'MATLAB':"error('Invalid formula inputs');",'Julia':'throw(ArgumentError("Invalid formula inputs"))'}[lang]
    if lang=='Python':return f'    if {condition}: {fail}'
    if lang=='R':return f'  if ({condition}) {fail}'
    if lang=='MATLAB':return f'    if {condition}\n        {fail}\n    end'
    if lang=='Julia':return f'    if {condition}; {fail}; end'
    if lang=='Kotlin':return f'    if ({condition}) {fail}'
    if lang=='Rust':return f'    if {condition} {{ {fail} }}'
    if lang=='Go':return f'    if {condition} {{ {fail} }}'
    return f'    if ({condition}) {{ {fail} }}'


def _headers(lang, needs_math=True):
    if lang=='Python': return 'import math\n' if needs_math else ''
    if lang=='C':return '#include <math.h>\n'
    if lang=='C++':return '#include <cmath>\n#include <stdexcept>\n'
    if lang=='Swift':return 'import Foundation\n'
    if lang=='Kotlin':return 'import kotlin.math.*\n'
    if lang=='Go':return 'package main\n\nimport "math"\n'
    if lang=='Java':return ''
    if lang=='C#':return 'using System;\n'
    return ''


def _render_scalar(formula,options,fn,renames):
    expr,args,ints,guards=SCALARS[formula.function]
    if formula.function=='fin_fv' and options.variant=='continuous':
        expr='pv * exp(rate*n)'
        guards=('n < 0',)
    lang=options.language; emitter=ExpressionEmitter(lang,ints,renames)
    params=', '.join(_param(lang,renames.get(a,a),a in ints) for a in args)
    node=ast.parse(expr,mode='eval').body
    branches=[]
    if isinstance(node,ast.IfExp) and lang in ('Go','MATLAB'):
        branches=[(emitter.emit(node.test),emitter.emit(node.body),emitter.emit(node.orelse))]
        output=None
    else:
        output=emitter.emit(node)
    checks='\n'.join(_guard(lang,emitter.emit(g)) for g in guards)
    if lang=='Python':
        body=f'    return {output}'
        pre=f'def {fn}({params}) -> float:\n'
        if options.structure=='class': pre=f'class GeneratedCalculator:\n    @staticmethod\n    def {fn}({params}) -> float:\n';body='    '+body;checks='\n'.join('    '+s for s in checks.splitlines())
        return _headers(lang)+ '\n'+pre+(checks+'\n' if checks else '')+body+'\n'
    if lang=='R':return f'{fn} <- function({params}) {{\n'+(checks+'\n' if checks else '')+f'  return({output})\n}}\n'
    if lang in ('C','C++'):
        head='double '+fn+'('+params+')'
        body=f'{checks}\n    return {output};' if checks else f'    return {output};'
        if lang=='C++' and options.structure=='class':return _headers(lang)+f'\nclass GeneratedCalculator {{\npublic:\n  static {head} {{\n{body}\n  }}\n}};\n'
        return _headers(lang)+f'\n{head} {{\n{body}\n}}\n'
    if lang in ('JavaScript','TypeScript'):
        returntype=': number' if lang=='TypeScript' else ''
        prefix=(f'export function {fn}({params}){returntype} {{' if options.structure=='function'
                else f'export class GeneratedCalculator {{\n  static {fn}({params}){returntype} {{')
        ending='  }\n}\n' if options.structure=='class' else '}\n'
        return prefix+'\n'+(checks+'\n' if checks else '')+f'    return {output};\n'+ending
    if lang=='Java':
        static='static ' if options.structure=='function' else ''
        return f'public class GeneratedCalculator {{\n  public {static}double {fn}({params}) {{\n'+(checks+'\n' if checks else '')+f'    return {output};\n  }}\n}}\n'
    if lang=='C#':
        static='static ' if options.structure=='function' else ''
        return _headers(lang)+f'\npublic {static}class GeneratedCalculator {{\n  public {static}double {fn}({params}) {{\n'+(checks+'\n' if checks else '')+f'    return {output};\n  }}\n}}\n'
    if lang=='Swift':
        # Swift instance methods and global functions use external label underscore.
        definition=f'func {fn}({params}) -> Double {{\n'+(checks+'\n' if checks else '')+f'    return {output}\n}}\n'
        if options.structure=='class':definition='class GeneratedCalculator {\n'+''.join('  '+line+'\n' for line in definition.rstrip().splitlines())+'}\n'
        return _headers(lang)+ '\n'+definition
    if lang=='Kotlin':
        definition=f'fun {fn}({params}): Double {{\n'+(checks+'\n' if checks else '')+f'    return {output}\n}}\n'
        if options.structure=='class':definition='class GeneratedCalculator {\n'+''.join('  '+line+'\n' for line in definition.rstrip().splitlines())+'}\n'
        return _headers(lang)+'\n'+definition
    if lang=='Go':
        block=f'    return {output}' if not branches else f'    if {branches[0][0]} {{ return {branches[0][1]} }}\n    return {branches[0][2]}'
        return _headers(lang)+f'\nfunc {fn}({params}) float64 {{\n'+(checks+'\n' if checks else '')+block+'\n}\n'
    if lang=='Rust':
        return f'pub fn {fn}({params}) -> f64 {{\n'+(checks+'\n' if checks else '')+f'    {output}\n}}\n'
    if lang=='MATLAB':
        block=f'    result = {output};' if not branches else f'    if {branches[0][0]}\n        result = {branches[0][1]};\n    else\n        result = {branches[0][2]};\n    end'
        return f'function result = {fn}({params})\n'+(checks+'\n' if checks else '')+block+'\nend\n'
    if lang=='Julia':return f'function {fn}({params})\n'+(checks+'\n' if checks else '')+f'    return {output}\nend\n'
    raise AssertionError('Unsupported language')


def _render_npv(options,fn):
    """Emit a conventional indexed cashflow loop, first cashflow at t=0."""
    l=options.language
    loop=options.iteration if options.iteration!='auto' else 'for'
    if l=='Python':
        inner=('    for t, cf in enumerate(flows):\n        total += cf / (1.0 + rate) ** t' if loop=='for' else
               '    t = 0\n    while t < len(flows):\n        total += flows[t] / (1.0 + rate) ** t\n        t += 1')
        return f'def {fn}(rate: float, flows: list[float]) -> float:\n    if rate <= -1: raise ValueError("Invalid rate")\n    total = 0.0\n{inner}\n    return total\n'
    if l=='R':
        inner=('  for (i in seq_along(flows)) { total <- total + flows[i] / (1 + rate)^(i - 1) }' if loop=='for' else
               '  i <- 1\n  while (i <= length(flows)) { total <- total + flows[i] / (1 + rate)^(i - 1); i <- i + 1 }')
        return f'{fn} <- function(rate, flows) {{\n  if (rate <= -1) stop("Invalid rate")\n  total <- 0.0\n{inner}\n  return(total)\n}}\n'
    # code for each runtime has an explicit counted loop; no dynamic eval.
    data={
     'C':('double rate, const double *flows, size_t count','size_t t = 0;','t < count','t++','flows[t] / pow(1.0 + rate, (double)t)','double','return NAN;'),
     'C++':('double rate, const std::vector<double>& flows','size_t t = 0;','t < flows.size()','t++','flows[t] / std::pow(1.0 + rate, (double)t)','double','throw std::invalid_argument("Invalid rate");'),
     'JavaScript':('rate, flows','let t = 0;','t < flows.length','t++','flows[t] / Math.pow(1 + rate, t)','let','throw new RangeError("Invalid rate");'),
     'TypeScript':('rate: number, flows: number[]','let t = 0;','t < flows.length','t++','flows[t] / Math.pow(1 + rate, t)','let','throw new RangeError("Invalid rate");'),
     'Java':('double rate, double[] flows','int t = 0;','t < flows.length','t++','flows[t] / Math.pow(1 + rate, t)','double','throw new IllegalArgumentException("Invalid rate");'),
     'C#':('double rate, double[] flows','int t = 0;','t < flows.Length','t++','flows[t] / Math.Pow(1 + rate, t)','double','throw new ArgumentOutOfRangeException("Invalid rate");'),
     'Swift':('_ rate: Double, _ flows: [Double])','var t = 0','t < flows.count','t += 1','flows[t] / pow(1 + rate, Double(t))','var','return Double.nan'),
     'Kotlin':('rate: Double, flows: DoubleArray','var t = 0','t < flows.size','t++','flows[t] / (1 + rate).pow(t)','var','throw IllegalArgumentException("Invalid rate")'),
     'Go':('rate float64, flows []float64','t := 0','t < len(flows)','t++','flows[t] / math.Pow(1 + rate, float64(t))','var','return math.NaN()'),
     'Rust':('rate: f64, flows: &[f64]','let mut t = 0usize;','t < flows.len()','t += 1','flows[t] / (1.0 + rate).powf(t as f64)','let mut','return f64::NAN;'),
     'MATLAB':('rate, flows','t = 1;','t <= numel(flows)','t = t + 1;','flows(t) / (1 + rate)^(t - 1)','',"error('Invalid rate');"),
     'Julia':('rate, flows','t = 1','t <= length(flows)','t += 1','flows[t] / (1 + rate)^(t-1)','', 'throw(ArgumentError("Invalid rate"))'),
    }
    p,init,check,inc,formula,decl,error=data[l]
    if l=='C':
        h='#include <math.h>\n#include <stddef.h>\n';signature=f'double {fn}({p})';
    elif l=='C++':
        h='#include <cmath>\n#include <vector>\n#include <stdexcept>\n';signature=f'double {fn}({p})';
    elif l in ('JavaScript','TypeScript'):
        h=''; signature=f'export function {fn}({p})'+(': number' if l=='TypeScript' else '')
    elif l=='Java':h='';signature=f'public static double {fn}({p})'
    elif l=='C#':h='using System;\n';signature=f'public static double {fn}({p})'
    elif l=='Swift':h='import Foundation\n';signature=f'func {fn}({p} -> Double'
    elif l=='Kotlin':h='import kotlin.math.pow\n';signature=f'fun {fn}({p}): Double'
    elif l=='Go':h='package main\nimport "math"\n';signature=f'func {fn}({p}) float64'
    elif l=='Rust':h='';signature=f'pub fn {fn}({p}) -> f64'
    elif l=='MATLAB':h='';signature=f'function result = {fn}({p})'
    elif l=='Julia':h='';signature=f'function {fn}({p})'
    if l in ('MATLAB','Julia'):
        i=f'    {init}'
        if loop=='for':
            loopbody=(f'    for t = 1:numel(flows)\n        total = total + {formula};\n    end' if l=='MATLAB' else
                      f'    for t in eachindex(flows)\n        total += {formula}\n    end')
        else:
            loopbody=(f'    while {check}\n        total = total + {formula};\n        {inc}\n    end' if l=='MATLAB' else
                      f'    while {check}\n        total += {formula}\n        {inc}\n    end')
        guard=(f'    if rate <= -1\n        {error}\n    end' if l=='MATLAB' else f'    if rate <= -1; {error}; end')
        finish='    result = total;' if l=='MATLAB' else '    return total'
        return h+signature+'\n'+guard+'\n    total = 0.0;\n'+(i+'\n' if loop=='while' else '')+loopbody+'\n'+finish+'\nend\n'
    # Go/Rust have different counted-loop syntax.
    if l=='Go':
        loopbody=(f'    for {init}; {check}; {inc} {{ total += {formula} }}' if loop=='for' else
                  f'    {init}\n    for {check} {{ total += {formula}; {inc} }}')
        return h+signature+f' {{\n    if rate <= -1 {{ {error} }}\n    total := 0.0\n'+loopbody+'\n    return total\n}\n'
    if l=='Rust':
        loopbody=(f'    for t in 0..flows.len() {{ total += {formula}; }}' if loop=='for' else
                  f'    {init}\n    while {check} {{ total += {formula}; {inc}; }}')
        return h+signature+f' {{\n    if rate <= -1.0 {{ {error} }}\n    let mut total = 0.0;\n'+loopbody+'\n    total\n}\n'
    if l=='Swift':
        loopbody=(f'    for t in 0..<flows.count {{ total += {formula} }}' if loop=='for' else
                  f'    {init}\n    while {check} {{ total += {formula}; {inc} }}')
        return h+signature+f' {{\n    if rate <= -1 {{ {error} }}\n    var total = 0.0\n'+loopbody+'\n    return total\n}\n'
    if l=='Kotlin':
        loopbody=(f'    for (t in flows.indices) {{ total += {formula} }}' if loop=='for' else
                  f'    {init}\n    while ({check}) {{ total += {formula}; {inc} }}')
        return h+signature+f' {{\n    if (rate <= -1.0) {{ {error} }}\n    var total = 0.0\n'+loopbody+'\n    return total\n}\n'
    guard=f'    if (rate <= -1) {{ {error} }}'
    loopbody=(f'    for ({init} {check}; {inc}) {{ total += {formula}; }}' if loop=='for' else
              f'    {init}\n    while ({check}) {{ total += {formula}; {inc}; }}')
    declaration=f'    {decl} total = 0.0;'
    body=signature+' {\n'+guard+'\n'+declaration+'\n'+loopbody+'\n    return total;\n}\n'
    if l=='Java':body='public class GeneratedCalculator {\n  '+body.replace('\n','\n  ').rstrip()+'\n}\n'
    if l=='C#':body='public static class GeneratedCalculator {\n  '+body.replace('\n','\n  ').rstrip()+'\n}\n'
    return h+'\n'+body


def generate(formula_id:str, options:GenerationOptions|None=None)->str:
    opt=options or GenerationOptions()
    formula=get_formula(formula_id)
    _check_options(formula,opt)
    default_name = {'qf_target': 'target_portfolio', 'fin_irr': 'calculate_irr'}.get(formula.function, formula.function.removeprefix('fin_').removeprefix('qf_'))
    fn=_identifier(opt.function_name or default_name)
    if formula.function not in SCALARS and formula.function != 'fin_npv':
        if opt.language == 'Python':
            from .python_full import generate_python
            return generate_python(formula,opt,fn)
        from .portable_quant import PORTABLE, generate_portable
        from .portable_loops import SUPPORTED as LOOP_PROFILES, generate_loops
        if formula.function in PORTABLE:
            return generate_portable(fn,formula,opt)
        if formula.function in LOOP_PROFILES:
            return generate_loops(fn,formula,opt)
        from .portable_stochastic import SUPPORTED as STOCHASTIC_PROFILES, generate_stochastic
        if formula.function in STOCHASTIC_PROFILES:
            return generate_stochastic(fn,formula,opt)
        from .portable_mc import SUPPORTED as MC_PROFILES, generate_mc
        if formula.function in MC_PROFILES:
            return generate_mc(fn,formula,opt)
        from .portable_bl import SUPPORTED as BL_PROFILES, generate_bl
        if formula.function in BL_PROFILES:
            return generate_bl(fn,formula,opt)
        from .portable_allocation import SUPPORTED as ALLOCATION_PROFILES, generate_allocation
        if formula.function in ALLOCATION_PROFILES:
            return generate_allocation(fn,formula,opt)
        from .portable_risk import SUPPORTED as RISK_PROFILES, generate_risk
        if formula.function in RISK_PROFILES:
            return generate_risk(fn,formula,opt)
        from .portable_moving import SUPPORTED as MOVING_PROFILES, generate_moving
        if formula.function in MOVING_PROFILES:
            return generate_moving(fn,formula,opt)
        from .portable_portfolio import SUPPORTED as PORTFOLIO_PROFILES, generate_portfolio
        if formula.function in PORTFOLIO_PROFILES:
            return generate_portfolio(fn,formula,opt)
        from .portable_bs import SUPPORTED as BS_PROFILES, generate_bs
        if formula.function in BS_PROFILES:
            return generate_bs(fn,formula,opt)
        from .portable_iv import SUPPORTED as IV_PROFILES, generate_iv
        if formula.function in IV_PROFILES:
            return generate_iv(fn,formula,opt)
        from .portable_normal_risk import SUPPORTED as NORMAL_RISK_PROFILES, generate_normal_risk
        if formula.function in NORMAL_RISK_PROFILES:
            return generate_normal_risk(fn,formula,opt)
        from .portable_finance import SUPPORTED as FINANCE_PROFILES, generate_finance
        if formula.function in FINANCE_PROFILES:
            return generate_finance(fn,formula,opt)
        from .portable_stats import SUPPORTED as STAT_PROFILES, generate_stats
        if formula.function in STAT_PROFILES:
            return generate_stats(fn,formula,opt)
        from .portable_performance import SUPPORTED as PERFORMANCE_PROFILES, generate_performance
        if formula.function in PERFORMANCE_PROFILES:
            return generate_performance(fn,formula,opt)
        from .portable_backtest import SUPPORTED as BACKTEST_PROFILES, generate_backtest
        if formula.function in BACKTEST_PROFILES:
            return generate_backtest(fn,formula,opt)
        if formula.function == 'qf_ytm':
            from .portable_ytm import generate_ytm
            return generate_ytm(fn,formula,opt)
        raise GenerationError(f'{formula.id}: {opt.language} adapter not implemented')
    valid_names= {'rate','flows'} if formula.function=='fin_npv' else set(SCALARS[formula.function][1])
    renames={}
    for src,dst in opt.variable_names:
        if src not in valid_names or src in renames: raise GenerationError(f'Unknown or repeated variable name: {src!r}')
        renames[src]=_identifier(dst)
    final_names=[renames.get(a,a) for a in valid_names]
    if len(set(final_names))!=len(final_names) or fn in final_names or opt.class_name in final_names:
        raise GenerationError('Variable names must be unique and must not shadow function/class identifiers')
    if formula.function=='fin_npv':
        if any(v in ('total','t','i','cf') for v in final_names):
            raise GenerationError('NPV variables must not shadow internal accumulators')
        code=_render_npv(opt,fn)
        # Internal NPV snippets are generated from a fixed template; the only
        # text identifiers replaced here are the two known argument tokens.
        for i,(src,dst) in enumerate(renames.items()):
            code=re.sub(r'\b'+src+r'\b','__USER_VAR_'+str(i)+'__',code)
        for i,(_,dst) in enumerate(renames.items()):
            code=code.replace('__USER_VAR_'+str(i)+'__',dst)
    else:
        code=_render_scalar(formula,opt,fn,renames)
    if opt.structure=='class' and opt.class_name!='GeneratedCalculator':
        code=code.replace('GeneratedCalculator',opt.class_name)
    return code
