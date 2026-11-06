"""Portable path-simulation generators for arithmetic Brownian, GBM and OU.

All non-Python targets use Park-Miller + Box-Muller in path-major order.
Python reference code stays NumPy-based, so bit-identical Python results are
not expected; model moments and sample contracts remain the same.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'qf_brownian', 'qf_gbm_paths', 'qf_ou_paths'})
ARGS = {
    'qf_brownian': ('years','steps','paths','seed','initial','mu','sigma'),
    'qf_gbm_paths': ('s','mu','sigma','years','steps','paths','seed'),
    'qf_ou_paths': ('x','level','kappa','sigma','years','steps','paths','seed'),
}
NOTE = ('HyunCalculator stochastic paths; Park-Miller 16807 + Box-Muller, '
        'seed 1..2147483646; different RNG from Python NumPy. '
        'Flat result: [theoretical_mean,theoretical_sd,simulated_mean,simulated_sd,'
        'first_path_at_t0,...,first_path_at_tN]; length steps+5.')


def _check(formula, opt):
    if formula.function not in SUPPORTED or opt.language == 'Python':
        raise GenerationError('Portable stochastic adapter supports non-Python stochastic paths only')
    if (opt.structure != 'function' or opt.iteration != 'auto' or opt.variable_names or
            opt.variant != 'periodic' or opt.imports not in ('auto','standard')):
        raise GenerationError('Stochastic path adapters require function/auto/standard imports/canonical parameters')


def _model_parts(func, exp, sqrt):
    """Return scalar initializer and path recurrence snippets (in shared C-style syntax)."""
    if func == 'qf_brownian':
        return ('initial', 'initial + mu*years', 'sigma*'+sqrt+'(years)',
                'mu*dt', 'sigma*'+sqrt+'(dt)', 'value + driftStep + noiseStep*z', 'sigma < 0')
    if func == 'qf_gbm_paths':
        return ('s', 's*'+exp+'(mu*years)',
                's*'+exp+'(mu*years)*'+sqrt+'('+exp+'(sigma*sigma*years)-1.0)',
                '(mu-0.5*sigma*sigma)*dt', 'sigma*'+sqrt+'(dt)',
                'value*'+exp+'(driftStep+noiseStep*z)', 's <= 0 || sigma < 0')
    return ('x', 'level+(x-level)*'+exp+'(-kappa*years)',
            'sigma*'+sqrt+'((1.0-'+exp+'(-2.0*kappa*years))/(2.0*kappa))',
            exp+'(-kappa*dt)',
            'sigma*'+sqrt+'((1.0-'+exp+'(-2.0*kappa*dt))/(2.0*kappa))',
            'level+(value-level)*driftStep+noiseStep*z', 'kappa <= 0 || sigma < 0')


def _c_style(fn, lang, func):
    mapping={
        'C':('exp','sqrt','log','cos','isfinite','double','int','long long'),
        'C++':('std::exp','std::sqrt','std::log','std::cos','std::isfinite','double','int','long long'),
        'JavaScript':('Math.exp','Math.sqrt','Math.log','Math.cos','Number.isFinite','const','let','let'),
        'TypeScript':('Math.exp','Math.sqrt','Math.log','Math.cos','Number.isFinite','const','let','let'),
        'Java':('Math.exp','Math.sqrt','Math.log','Math.cos','Double.isFinite','double','int','long'),
        'C#':('Math.Exp','Math.Sqrt','Math.Log','Math.Cos','double.IsFinite','double','int','long'),
    }
    exp,sqrt,log,cos,finite,dec,idx,integer=mapping[lang]
    args=ARGS[func]
    ints={'steps','paths','seed'}
    if lang in ('JavaScript','TypeScript'):
        typ=lambda a: f'{a}: number' if lang=='TypeScript' else a
        signature=f'export function {fn}('+','.join(map(typ,args))+')'+(': number[]' if lang=='TypeScript' else '')
        init='const' ; mutable='let'; seeddecl='let'; ret='return out;'
        fail='throw new RangeError("Invalid stochastic inputs");'
        head=''
        output_init='const out = new Array(steps+5).fill(0.0);'
        stateCast='state'
    else:
        par=lambda a: (integer if a=='seed' else idx if a in ('steps','paths') else 'double')+' '+a
        signature=(f'HyunPathResult {fn}' if lang=='C' else
                   f'std::vector<double> {fn}' if lang=='C++' else
                   f'public static double[] {fn}')+'('+','.join(map(par,args))+')'
        init='double';mutable='double';seeddecl=integer
        if lang=='C':
            head='#include <math.h>\n#include <stdint.h>\ntypedef struct {int length; double values[5006];} HyunPathResult;\n'
            output_init='HyunPathResult result = {0,{0}}; result.length=steps+5; double *out=result.values;'
            ret='return result;'
            fail='return (HyunPathResult){0,{0}};'
            stateCast='(double)state'
        elif lang=='C++':
            head='#include <vector>\n#include <cmath>\n#include <stdexcept>\n'
            output_init='std::vector<double> out(steps+5);'
            ret='return out;'
            fail='throw std::invalid_argument("Invalid stochastic inputs");'
            stateCast='static_cast<double>(state)'
        else:
            head='using System;\n' if lang=='C#' else ''
            output_init='double[] out = new double[steps+5];'
            ret='return out;'
            fail=('throw new ArgumentException("Invalid stochastic inputs");' if lang=='C#' else
                  'throw new IllegalArgumentException("Invalid stochastic inputs");')
            stateCast='(double)state'
    scalar_args=[a for a in args if a not in ints]
    invalid='||'.join(f'!{finite}({a})' for a in scalar_args)
    invalid+='||years<0||steps<1||steps>5000||paths<2||paths>100000||((long)steps)*paths>2000000||seed<1||seed>=2147483647'
    if lang in ('JavaScript','TypeScript'):
        invalid=invalid.replace('((long)steps)*paths','steps*paths')
        invalid+='||!Number.isSafeInteger(steps)||!Number.isSafeInteger(paths)||!Number.isSafeInteger(seed)'
    s0,tmean,tsd,drift,noise,nextval,guard=_model_parts(func,exp,sqrt)
    invalid+='||'+guard
    if lang in ('JavaScript','TypeScript'):
        code=f'''// {NOTE}
{signature} {{
  if ({invalid}) {{ {fail} }}
  {output_init}
  const dt=years/steps;
  const theoreticalMean={tmean};
  const theoreticalSd={tsd};
  const driftStep={drift};
  const noiseStep={noise};
  let state=seed;
  let mean=0.0, m2=0.0;
  out[0]=theoreticalMean; out[1]=theoreticalSd;
  for (let p=0;p<paths;p++) {{
    let value={s0};
    if(p===0) out[4]=value;
    for(let j=0;j<steps;j++) {{
      state=(state*16807)%2147483647; const u1=state/2147483647.0;
      state=(state*16807)%2147483647; const u2=state/2147483647.0;
      const z={sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2);
      value={nextval};
      if(p===0) out[5+j]=value;
    }}
    const delta=value-mean; mean+=delta/(p+1); m2+=delta*(value-mean);
  }}
  out[2]=mean; out[3]={sqrt}(m2/(paths-1));
  {ret}
}}
'''
    else:
        code=f'''// {NOTE}
{signature} {{
  if ({invalid}) {{ {fail} }}
  {output_init}
  double dt=years/steps;
  double theoreticalMean={tmean};
  double theoreticalSd={tsd};
  double driftStep={drift};
  double noiseStep={noise};
  {seeddecl} state=seed;
  double mean=0.0, m2=0.0;
  out[0]=theoreticalMean; out[1]=theoreticalSd;
  for (int p=0;p<paths;p++) {{
    double value={s0};
    if(p==0) out[4]=value;
    for(int j=0;j<steps;j++) {{
      state=(state*16807)%2147483647; double u1={stateCast}/2147483647.0;
      state=(state*16807)%2147483647; double u2={stateCast}/2147483647.0;
      double z={sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2);
      value={nextval};
      if(p==0) out[5+j]=value;
    }}
    double delta=value-mean; mean+=delta/(p+1); m2+=delta*(value-mean);
  }}
  out[2]=mean; out[3]={sqrt}(m2/(paths-1));
  {ret}
}}
'''
        if lang=='Java':code='public class GeneratedCalculator {\n'+''.join('  '+line+'\n' for line in code.rstrip().splitlines())+'}\n'
        if lang=='C#':code='public static class GeneratedCalculator {\n'+''.join('  '+line+'\n' for line in code.rstrip().splitlines())+'}\n'
    if lang == 'C#':
        import re
        code=re.sub(r'\bout\b','resultValues',code)
    return head+code


def _script(fn,lang,func):
    args=ARGS[func]
    s0,tmean,tsd,drift,noise,step,guard=_model_parts(func,'exp','sqrt')
    scalars=[a for a in args if a not in ('paths','steps','seed')]
    if lang=='R':
        checks=' || '.join(f'!is.finite({a})' for a in args)
        checks+=' || years<0 || steps<1 || steps>5000 || paths<2 || paths>100000 || steps*paths>2000000 || seed<1 || seed>=2147483647 || any(c(steps,paths,seed)!=floor(c(steps,paths,seed))) || '+guard
        return f'''# {NOTE}
{fn} <- function({','.join(args)}) {{
  if ({checks}) stop("Invalid stochastic inputs")
  out <- numeric(steps+5); dt <- years/steps
  theoreticalMean <- {tmean}; theoreticalSd <- {tsd}
  driftStep <- {drift}; noiseStep <- {noise}
  state <- as.numeric(seed); avg <- 0.0; m2 <- 0.0
  out[1] <- theoreticalMean; out[2] <- theoreticalSd
  for (p in seq_len(paths)) {{
    value <- {s0}; if(p==1)out[5] <- value
    for (j in seq_len(steps)) {{
      state <- (state*16807) %% 2147483647;u1 <- state/2147483647.0
      state <- (state*16807) %% 2147483647;u2 <- state/2147483647.0
      z <- sqrt(-2.0*log(u1))*cos(6.283185307179586*u2)
      value <- {step};if(p==1)out[5+j] <- value
    }}
    delta <- value-avg;avg <- avg+delta/p;m2 <- m2+delta*(value-avg)
  }}
  out[3] <- avg;out[4] <- sqrt(m2/(paths-1))
  out
}}
'''
    if lang=='MATLAB':
        checks=' || '.join(f'~isfinite({a})' for a in args)
        checks+=' || years<0 || steps<1 || steps>5000 || paths<2 || paths>100000 || steps*paths>2000000 || seed<1 || seed>=2147483647 || any([steps,paths,seed]~=floor([steps,paths,seed])) || '+guard
        return f'''% {NOTE}
function out = {fn}({','.join(args)})
  if {checks}; error('Invalid stochastic inputs'); end
  out=zeros(1,steps+5);dt=years/steps;
  theoreticalMean={tmean};theoreticalSd={tsd};
  driftStep={drift};noiseStep={noise};
  state=double(seed);avg=0;m2=0;
  out(1)=theoreticalMean;out(2)=theoreticalSd;
  for p=1:paths
    value={s0};if p==1;out(5)=value;end
    for j=1:steps
      state=mod(state*16807,2147483647);u1=state/2147483647.0;
      state=mod(state*16807,2147483647);u2=state/2147483647.0;
      z=sqrt(-2.0*log(u1))*cos(6.283185307179586*u2);
      value={step};if p==1;out(5+j)=value;end
    end
    delta=value-avg;avg=avg+delta/p;m2=m2+delta*(value-avg);
  end
  out(3)=avg;out(4)=sqrt(m2/(paths-1));
end
'''
    if lang=='Julia':
        checks=' || '.join(f'!isfinite({a})' for a in scalars)
        checks+=' || years<0 || steps<1 || steps>5000 || paths<2 || paths>100000 || steps*paths>2000000 || seed<1 || seed>=2147483647 || '+guard
        return f'''# {NOTE}
function {fn}({','.join(args)})
  if {checks}; throw(ArgumentError("Invalid stochastic inputs")); end
  out=zeros(Float64,steps+5);dt=years/steps
  theoreticalMean={tmean};theoreticalSd={tsd}
  driftStep={drift};noiseStep={noise}
  state=Int64(seed);avg=0.0;m2=0.0
  out[1]=theoreticalMean;out[2]=theoreticalSd
  for p in 1:paths
    value={s0};if p==1;out[5]=value;end
    for j in 1:steps
      state=(state*16807)%2147483647;u1=state/2147483647.0
      state=(state*16807)%2147483647;u2=state/2147483647.0
      z=sqrt(-2.0*log(u1))*cos(6.283185307179586*u2)
      value={step};if p==1;out[5+j]=value;end
    end
    delta=value-avg;avg+=delta/p;m2+=delta*(value-avg)
  end
  out[3]=avg;out[4]=sqrt(m2/(paths-1))
  return out
end
'''
    raise GenerationError(f'Unsupported script language {lang}')


def _native(fn,lang,func):
    args=ARGS[func]
    exps={'Swift':'exp','Kotlin':'exp','Go':'math.Exp','Rust':'exp'}
    sqrts={'Swift':'sqrt','Kotlin':'sqrt','Go':'math.Sqrt','Rust':'sqrt'}
    logs={'Swift':'log','Kotlin':'ln','Go':'math.Log','Rust':'ln'}
    coss={'Swift':'cos','Kotlin':'cos','Go':'math.Cos','Rust':'cos'}
    exp,sqrt,log,cos=exps[lang],sqrts[lang],logs[lang],coss[lang]
    s0,tmean,tsd,drift,noise,nxt,guard=_model_parts(func,exp,sqrt)
    if lang=='Swift':
        sig=','.join(('_ '+a+':Int' if a in ('paths','steps') else '_ '+a+':Int64' if a=='seed' else '_ '+a+':Double') for a in args)
        checks=','.join(a for a in args if a not in ('paths','steps','seed'))
        return f'''// {NOTE}
import Foundation
func {fn}({sig})->[Double] {{
  guard [{checks}].allSatisfy({{$0.isFinite}}), years>=0, steps>=1, steps<=5000, paths>=2, paths<=100000, steps*paths<=2000000, seed>=1, seed<2147483647, !({guard}) else {{return []}}
  let dt=years/Double(steps)
  let theoreticalMean={tmean},theoreticalSd={tsd}
  let driftStep={drift},noiseStep={noise}
  var out=[Double](repeating:0.0,count:steps+5)
  var state=seed,avg=0.0,m2=0.0
  out[0]=theoreticalMean;out[1]=theoreticalSd
  for p in 0..<paths {{
    var value={s0};if p==0 {{out[4]=value}}
    for j in 0..<steps {{
      state=(state*16807)%2147483647;let u1=Double(state)/2147483647.0
      state=(state*16807)%2147483647;let u2=Double(state)/2147483647.0
      let z={sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2)
      value={nxt};if p==0 {{out[5+j]=value}}
    }}
    let delta=value-avg;avg+=delta/Double(p+1);m2+=delta*(value-avg)
  }}
  out[2]=avg;out[3]={sqrt}(m2/Double(paths-1))
  return out
}}
'''
    if lang=='Kotlin':
        sig=','.join(a+(' :Int' if a in ('paths','steps') else ':Long' if a=='seed' else ':Double') for a in args)
        checks=','.join(a for a in args if a not in ('paths','steps','seed'))
        return f'''// {NOTE}
import kotlin.math.*
fun {fn}({sig}):DoubleArray {{
  require(listOf({checks}).all{{it.isFinite()}} && years>=0.0 && steps in 1..5000 && paths in 2..100000 && steps.toLong()*paths<=2000000L && seed in 1L..2147483646L && !({guard})) {{"Invalid stochastic inputs"}}
  val dt=years/steps
  val theoreticalMean={tmean};val theoreticalSd={tsd}
  val driftStep={drift};val noiseStep={noise}
  val out=DoubleArray(steps+5)
  var state=seed;var avg=0.0;var m2=0.0
  out[0]=theoreticalMean;out[1]=theoreticalSd
  for(p in 0 until paths) {{
    var value={s0};if(p==0)out[4]=value
    for(j in 0 until steps) {{
      state=(state*16807L)%2147483647L;val u1=state.toDouble()/2147483647.0
      state=(state*16807L)%2147483647L;val u2=state.toDouble()/2147483647.0
      val z={sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2)
      value={nxt};if(p==0)out[5+j]=value
    }}
    val delta=value-avg;avg+=delta/(p+1);m2+=delta*(value-avg)
  }}
  out[2]=avg;out[3]={sqrt}(m2/(paths-1))
  return out
}}
'''
    if lang=='Go':
        sig=','.join(a+(' int' if a in ('paths','steps') else ' int64' if a=='seed' else ' float64') for a in args)
        checks='||'.join('math.IsNaN('+a+')||math.IsInf('+a+',0)' for a in args if a not in ('paths','steps','seed'))
        return f'''// {NOTE}
package main
import "math"
func {fn}({sig}) []float64 {{
  if {checks}||years<0||steps<1||steps>5000||paths<2||paths>100000||int64(steps)*int64(paths)>2000000||seed<1||seed>=2147483647||{guard} {{return nil}}
  dt:=years/float64(steps)
  theoreticalMean:={tmean};theoreticalSd:={tsd}
  driftStep:={drift};noiseStep:={noise}
  out:=make([]float64,steps+5)
  state:=seed;avg:=0.0;m2:=0.0
  out[0]=theoreticalMean;out[1]=theoreticalSd
  for p:=0;p<paths;p++{{
    value:={s0};if p==0 {{out[4]=value}}
    for j:=0;j<steps;j++{{
      state=(state*16807)%2147483647;u1:=float64(state)/2147483647.0
      state=(state*16807)%2147483647;u2:=float64(state)/2147483647.0
      z:={sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2)
      value={nxt};if p==0 {{out[5+j]=value}}
    }}
    delta:=value-avg;avg+=delta/float64(p+1);m2+=delta*(value-avg)
  }}
  out[2]=avg;out[3]={sqrt}(m2/float64(paths-1))
  return out
}}
'''
    if lang=='Rust':
        sig=','.join(a+(':usize' if a in ('paths','steps') else ':i64' if a=='seed' else ':f64') for a in args)
        from .emitter import ExpressionEmitter
        em=ExpressionEmitter('Rust')
        tmean,tsd,drift,noise,nxt=[em.emit(v) for v in (tmean,tsd,drift,noise,nxt)]
        checks='||'.join('!'+a+'.is_finite()' for a in args if a not in ('paths','steps','seed'))
        guard=guard.replace('<= 0','<= 0.0').replace('< 0','< 0.0')
        return f'''// {NOTE}
pub fn {fn}({sig})->Vec<f64> {{
  if {checks}||years<0.0||steps<1||steps>5000||paths<2||paths>100000||steps*paths>2000000||seed<1||seed>=2147483647||{guard} {{return vec![]}}
  let dt=years/(steps as f64);
  let theoreticalMean={tmean};let theoreticalSd={tsd};
  let driftStep={drift};let noiseStep={noise};
  let mut out=vec![0.0;steps+5];
  let mut state=seed;let mut avg=0.0;let mut m2=0.0;
  out[0]=theoreticalMean;out[1]=theoreticalSd;
  for p in 0..paths {{
    let mut value={s0};if p==0 {{out[4]=value;}}
    for j in 0..steps {{
      state=(state*16807)%2147483647;let u1=state as f64/2147483647.0;
      state=(state*16807)%2147483647;let u2=state as f64/2147483647.0;
      let z=(-2.0_f64*u1.ln()).sqrt()*(6.283185307179586_f64*u2).cos();
      value={nxt};if p==0 {{out[5+j]=value;}}
    }}
    let delta=value-avg;avg+=delta/((p+1) as f64);m2+=delta*(value-avg);
  }}
  out[2]=avg;out[3]=(m2/((paths-1) as f64)).sqrt();
  out
}}
'''
    raise GenerationError(f'Unsupported native language {lang}')


def generate_stochastic(fn,formula,opt):
    _check(formula,opt)
    lang=opt.language
    if lang in ('C','C++','JavaScript','TypeScript','Java','C#'):
        return _c_style(fn,lang,formula.function)
    if lang in ('R','MATLAB','Julia'):
        return _script(fn,lang,formula.function)
    return _native(fn,lang,formula.function)
