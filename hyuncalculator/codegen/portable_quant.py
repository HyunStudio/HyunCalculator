"""Auditable standard-library multi-output quantitative emitters.

Emits 4 exact, scalar-input formulas to 13 languages (Python is implemented
separately). No templated shell imports HyunCalculator; source is standalone.
Output order is explicitly documented for languages without native named records.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from .emitter import ExpressionEmitter, GenerationError, _identifier, _param


@dataclass(frozen=True)
class PortableSpec:
    fields: tuple[str, ...]
    integers: frozenset[str]
    guards: tuple[str, ...]
    outputs: tuple[tuple[str, str], ...]


PORTABLE = {
    'qf_garch': PortableSpec(
        ('lastvar','shock','omega','alpha','beta'), frozenset(),
        ('lastvar < 0', 'omega < 0', 'alpha < 0', 'beta < 0', 'alpha + beta >= 1'),
        (('Forecast variance','omega + alpha * shock**2 + beta * lastvar'),
         ('Forecast volatility','sqrt(omega + alpha * shock**2 + beta * lastvar)'),
         ('Unconditional variance','omega / (1 - alpha - beta)'))),
    'qf_gbm': PortableSpec(
        ('s','mu','sigma','t'),frozenset(),('s <= 0','sigma < 0','t < 0'),
        (('Expected price','s * exp(mu*t)'),
         ('Std. deviation','s * exp(mu*t) * sqrt(exp(sigma**2*t)-1)'))),
    'qf_ou': PortableSpec(
        ('x','level','kappa','sigma','t'),frozenset(),('kappa <= 0','sigma < 0','t < 0'),
        (('Expected state','level + (x - level) * exp(-kappa*t)'),
         ('Std. deviation','sigma * sqrt((1-exp(-2*kappa*t))/(2*kappa))'))),
    'qf_cost': PortableSpec(
        ('notional','commission','slippage','spread','sides'),frozenset({'sides'}),
        ('notional < 0','commission < 0','slippage < 0','spread < 0','sides < 1','sides > 2'),
        (('One-way effective cost (bps)','commission+slippage+spread'),
         ('Total traded notional','notional*sides'),
         ('Total estimated trading cost','notional*sides*(commission+slippage+spread)/10000'),
         ('Total cost / single-side notional','sides*(commission+slippage+spread)/10000'))),
}


def _finite(lang,name):
    return {
        'R':f'!is.finite({name})','C':f'!isfinite({name})',
        'C++':f'!std::isfinite({name})',
        'JavaScript':f'!Number.isFinite({name})','TypeScript':f'!Number.isFinite({name})',
        'Java':f'!Double.isFinite({name})','C#':f'!double.IsFinite({name})',
        'Swift':f'!{name}.isFinite',
        'Kotlin':f'!{name}.isFinite()',
        'Go':f'(math.IsNaN({name}) || math.IsInf({name}, 0))',
        'Rust':f'!{name}.is_finite()',
        'MATLAB':f'~isfinite({name})','Julia':f'!isfinite({name})',
    }[lang]


def _invalid(lang,predicate,size):
    msg='Invalid quantitative inputs'
    if lang=='R':return f'  if ({predicate}) stop("{msg}")'
    if lang=='MATLAB':return f'    if {predicate}\n        error(\'{msg}\');\n    end'
    if lang=='Julia':return f'    if {predicate}; throw(ArgumentError("{msg}")); end'
    if lang=='C':return f'    if ({predicate}) {{ HyunResult invalid = {{ {{'+', '.join('NAN' for _ in range(size))+'} }; return invalid; }'
    if lang=='C++':return f'    if ({predicate}) throw std::invalid_argument("{msg}");'
    if lang=='JavaScript' or lang=='TypeScript':return f'    if ({predicate}) throw new RangeError("{msg}");'
    if lang=='Java':return f'    if ({predicate}) throw new IllegalArgumentException("{msg}");'
    if lang=='C#':return f'    if ({predicate}) throw new ArgumentOutOfRangeException("{msg}");'
    if lang=='Swift':return f'    if {predicate} {{ return [{", ".join("Double.nan" for _ in range(size))}] }}'
    if lang=='Kotlin':return f'    if ({predicate}) throw IllegalArgumentException("{msg}")'
    if lang=='Go':return f'    if {predicate} {{ return [{size}]float64{{{", ".join("math.NaN()" for _ in range(size))}}} }}'
    if lang=='Rust':return f'    if {predicate} {{ return [{", ".join("f64::NAN" for _ in range(size))}]; }}'
    raise GenerationError('Unsupported target language')


def generate_portable(function_name,form,options):
    lang=options.language
    spec=PORTABLE[form.function]
    if lang=='Python':raise GenerationError('Python uses full reference implementation instead')
    if options.structure!='function':raise GenerationError('Record-valued portable formulas currently support function structure only')
    if options.iteration!='auto':raise GenerationError('This analytic formula has no iteration option')
    if options.variant!='periodic':raise GenerationError('Variant applies only to Future Value')
    renames=dict(options.variable_names)
    if len(renames)!=len(options.variable_names) or any(k not in spec.fields for k in renames):
        raise GenerationError('Invalid repeated or unknown variable name')
    names={source: _identifier(renames.get(source,source)) for source in spec.fields}
    if len(set(names.values()))!=len(names) or function_name in names.values() or options.class_name in names.values():
        raise GenerationError('Generated parameter names collide')
    em=ExpressionEmitter(lang,spec.integers,names)
    params=', '.join(_param(lang,names[name],name in spec.integers) for name in spec.fields)
    expressions=[em.emit(expr) for _,expr in spec.outputs]
    finite_checks=[_finite(lang,names[name]) for name in spec.fields if name not in spec.integers]
    predicate=' || '.join([f'({em.emit(expr)})' for expr in spec.guards]+finite_checks) if lang not in ('R','MATLAB','Julia') else None
    if lang=='R':predicate=' | '.join([f'({em.emit(expr)})' for expr in spec.guards]+finite_checks)
    if lang=='MATLAB':predicate=' || '.join([f'({em.emit(expr)})' for expr in spec.guards]+finite_checks)
    if lang=='Julia':predicate=' || '.join([f'({em.emit(expr)})' for expr in spec.guards]+finite_checks)
    n=len(expressions)
    check=_invalid(lang,predicate,n)
    labels=', '.join(f'[{i}] {label}' for i,(label,_) in enumerate(spec.outputs))
    note='// Output indices: '+labels+'\n'
    if lang=='R':
        vals=', '.join(f'`{key}` = {value}' for (key,_),value in zip(spec.outputs,expressions))
        return f'# HyunCalculator {form.id}; named results in a list\n{function_name} <- function({params}) {{\n{check}\n  return(list({vals}))\n}}\n'
    if lang=='MATLAB':
        vals=', '.join(f"'{key.replace(' ','_').replace('.','').replace('/','_').replace('(','').replace(')','').replace('-','_')}', {val}" for (key,_),val in zip(spec.outputs,expressions))
        return f'% HyunCalculator {form.id}; named struct output\nfunction result = {function_name}({params})\n{check}\n    result = struct({vals});\nend\n'
    if lang=='Julia':
        def symbol(key):return ''.join(c if c.isalnum() else '_' for c in key).strip('_').lower()
        vals=', '.join(f'{symbol(key)} = {value}' for (key,_),value in zip(spec.outputs,expressions))
        return f'# HyunCalculator {form.id}; named tuple output\nfunction {function_name}({params})\n{check}\n    return ({vals})\nend\n'
    if lang=='C':
        head='#include <math.h>\n\n'+f'typedef struct {{ double values[{n}]; }} HyunResult;\n'+note
        return head+f'HyunResult {function_name}({params}) {{\n{check}\n    HyunResult result = {{ {{'+', '.join(expressions)+'} };\n    return result;\n}\n'
    if lang=='C++':
        head='#include <cmath>\n#include <array>\n#include <stdexcept>\n'+note
        return head+f'std::array<double,{n}> {function_name}({params}) {{\n{check}\n    return {{'+', '.join(expressions)+'};\n}\n'
    if lang in ('JavaScript','TypeScript'):
        result_type=(': Record<string, number>' if lang=='TypeScript' else '')
        fields=', '.join('"'+key+'": '+expr for (key,_),expr in zip(spec.outputs,expressions))
        return f'// HyunCalculator {form.id}\nexport function {function_name}({params}){result_type} {{\n{check}\n    return {{ {fields} }};\n}}\n'
    if lang=='Java':
        return note+f'public class GeneratedCalculator {{\n  public static double[] {function_name}({params}) {{\n{check}\n    return new double[] {{'+', '.join(expressions)+'};\n  }\n}\n'
    if lang=='C#':
        return 'using System;\n'+note+f'public static class GeneratedCalculator {{\n  public static double[] {function_name}({params}) {{\n{check}\n    return new double[] {{'+', '.join(expressions)+'};\n  }\n}\n'
    if lang=='Swift':
        return 'import Foundation\n'+note+f'func {function_name}({params}) -> [Double] {{\n{check}\n    return ['+', '.join(expressions)+']\n}\n'
    if lang=='Kotlin':
        return 'import kotlin.math.*\n'+note+f'fun {function_name}({params}): DoubleArray {{\n{check}\n    return doubleArrayOf('+', '.join(expressions)+')\n}\n'
    if lang=='Go':
        return 'package main\nimport "math"\n'+note+f'func {function_name}({params}) [{n}]float64 {{\n{check}\n    return [{n}]float64{{'+', '.join(expressions)+'}\n}\n'
    if lang=='Rust':
        return '// HyunCalculator '+form.id+'\n'+note+f'pub fn {function_name}({params}) -> [f64; {n}] {{\n{check}\n    ['+', '.join(expressions)+']\n}\n'
    raise GenerationError('Language not mapped')
