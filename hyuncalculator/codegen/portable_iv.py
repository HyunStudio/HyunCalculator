"""Portable European implied-volatility code generation for 13 non-Python targets.

Includes the already tested Black--Scholes price helper from portable_bs and a
bounded bisection inversion.  Uses identical no-arbitrage conventions to the
existing qf_iv calculator.  The full Python exporter remains unchanged.
"""
from __future__ import annotations

from .emitter import GenerationError
from .portable_bs import generate_bs

SUPPORTED = frozenset({'qf_iv'})
HELPER = 'hyun_bs_for_iv'


def generate_iv(fn, formula, opt):
    if opt.language == 'Python':
        raise GenerationError('Python uses reference implementation')
    if opt.structure != 'function' or opt.iteration != 'auto' or opt.variable_names or opt.variant != 'periodic':
        raise GenerationError('Implied volatility supports function/auto with fixed parameters')
    if fn in (HELPER, 'hyun_cdf'):
        raise GenerationError('Function name would shadow a required numerical helper')
    lang = opt.language
    base = generate_bs(HELPER, formula, opt)
    comment = 'European call/put implied volatility; option premium is in currency units; annual rates, continuous dividend yield.'
    if lang == 'C':
        wrapper = f'''/* {comment} */
double {fn}(double price,double s,double k,double t,double r,double q,const char* option){{
  if(!option||!isfinite(price)||!isfinite(s)||!isfinite(k)||!isfinite(t)||!isfinite(r)||!isfinite(q)||s<=0||k<=0||t<=0||price<0||(strcmp(option,"call")&&strcmp(option,"put")))return NAN;
  const double ds=s*exp(-q*t),dk=k*exp(-r*t),sign=strcmp(option,"call")==0?1:-1;
  const double lower=fmax(sign*(ds-dk),0.0),upper=sign>0?ds:dk;
  if(price<lower-1e-9||price>=upper)return NAN;
  if(price<=lower+1e-12)return 0;
  double lo=1e-10,hi=10.0;
  if({HELPER}(s,k,t,r,hi,q,option).values[0]<price)return NAN;
  for(int i=0;i<180;i++){{double mid=(lo+hi)/2.0;if({HELPER}(s,k,t,r,mid,q,option).values[0]<price)lo=mid;else hi=mid;}}
  return (lo+hi)/2.0;
}}
'''
    elif lang == 'C++':
        wrapper = f'''// {comment}
double {fn}(double price,double s,double k,double t,double r,double q,const std::string& option){{
  if(!std::isfinite(price)||!std::isfinite(s)||!std::isfinite(k)||!std::isfinite(t)||!std::isfinite(r)||!std::isfinite(q)||s<=0||k<=0||t<=0||price<0||(option!="call"&&option!="put"))throw std::invalid_argument("Invalid IV inputs");
  const double ds=s*std::exp(-q*t),dk=k*std::exp(-r*t),sign=option=="call"?1:-1;
  const double lower=std::max(sign*(ds-dk),0.0),upper=sign>0?ds:dk;
  if(price<lower-1e-9||price>=upper)throw std::invalid_argument("IV violates no-arbitrage bound");
  if(price<=lower+1e-12)return 0;
  double lo=1e-10,hi=10.0;
  if({HELPER}(s,k,t,r,hi,q,option)[0]<price)throw std::invalid_argument("Unable to bracket IV");
  for(int i=0;i<180;i++){{double mid=(lo+hi)/2.0;if({HELPER}(s,k,t,r,mid,q,option)[0]<price)lo=mid;else hi=mid;}}
  return (lo+hi)/2.0;
}}
'''
    elif lang in ('JavaScript', 'TypeScript'):
        args = 'price: number,s: number,k: number,t: number,r: number,q: number,option: string' if lang == 'TypeScript' else 'price,s,k,t,r,q,option'
        rettype = ': number' if lang == 'TypeScript' else ''
        wrapper = f'''// {comment}
export function {fn}({args}){rettype}{{
  if(![price,s,k,t,r,q].every(Number.isFinite)||s<=0||k<=0||t<=0||price<0||(option!=="call"&&option!=="put"))throw new RangeError("Invalid IV inputs");
  const ds=s*Math.exp(-q*t),dk=k*Math.exp(-r*t),sign=option==="call"?1:-1;
  const lower=Math.max(sign*(ds-dk),0),upper=sign>0?ds:dk;
  if(price<lower-1e-9||price>=upper)throw new RangeError("IV violates no-arbitrage bound");
  if(price<=lower+1e-12)return 0;
  let lo=1e-10,hi=10;
  if({HELPER}(s,k,t,r,hi,q,option)[0]<price)throw new RangeError("Unable to bracket IV");
  for(let i=0;i<180;i++){{const mid=(lo+hi)/2;if({HELPER}(s,k,t,r,mid,q,option)[0]<price)lo=mid;else hi=mid;}}
  return (lo+hi)/2;
}}
'''
    elif lang == 'Java':
        wrapper = f'''  // {comment}
  public static double {fn}(double price,double s,double k,double t,double r,double q,String option){{
    if(!Double.isFinite(price)||!Double.isFinite(s)||!Double.isFinite(k)||!Double.isFinite(t)||!Double.isFinite(r)||!Double.isFinite(q)||s<=0||k<=0||t<=0||price<0||(!"call".equals(option)&&!"put".equals(option)))throw new IllegalArgumentException("Invalid IV inputs");
    double ds=s*Math.exp(-q*t),dk=k*Math.exp(-r*t),sign="call".equals(option)?1:-1;
    double lower=Math.max(sign*(ds-dk),0),upper=sign>0?ds:dk;
    if(price<lower-1e-9||price>=upper)throw new IllegalArgumentException("IV violates no-arbitrage bound");
    if(price<=lower+1e-12)return 0;
    double lo=1e-10,hi=10;
    if({HELPER}(s,k,t,r,hi,q,option)[0]<price)throw new IllegalArgumentException("Unable to bracket IV");
    for(int i=0;i<180;i++){{double mid=(lo+hi)/2;if({HELPER}(s,k,t,r,mid,q,option)[0]<price)lo=mid;else hi=mid;}}
    return (lo+hi)/2;
  }}
'''
    elif lang == 'C#':
        wrapper = f'''  // {comment}
  public static double {fn}(double price,double s,double k,double t,double r,double q,string option){{
    if(!double.IsFinite(price)||!double.IsFinite(s)||!double.IsFinite(k)||!double.IsFinite(t)||!double.IsFinite(r)||!double.IsFinite(q)||s<=0||k<=0||t<=0||price<0||(option!="call"&&option!="put"))throw new ArgumentException("Invalid IV inputs");
    double ds=s*Math.Exp(-q*t),dk=k*Math.Exp(-r*t),sign=option=="call"?1:-1;
    double lower=Math.Max(sign*(ds-dk),0),upper=sign>0?ds:dk;
    if(price<lower-1e-9||price>=upper)throw new ArgumentException("IV violates no-arbitrage bound");
    if(price<=lower+1e-12)return 0;
    double lo=1e-10,hi=10;
    if({HELPER}(s,k,t,r,hi,q,option)[0]<price)throw new ArgumentException("Unable to bracket IV");
    for(int i=0;i<180;i++){{double mid=(lo+hi)/2;if({HELPER}(s,k,t,r,mid,q,option)[0]<price)lo=mid;else hi=mid;}}
    return (lo+hi)/2;
  }}
'''
    elif lang == 'Swift':
        wrapper = f'''// {comment}
func {fn}(_ price:Double,_ s:Double,_ k:Double,_ t:Double,_ r:Double,_ q:Double,_ option:String)->Double{{
  guard [price,s,k,t,r,q].allSatisfy({{$0.isFinite}}),s>0,k>0,t>0,price>=0,(option=="call"||option=="put") else {{return Double.nan}}
  let ds=s*exp(-q*t),dk=k*exp(-r*t),sign=option=="call" ? 1.0 : -1.0
  let lower=max(sign*(ds-dk),0),upper=sign>0 ? ds:dk
  if price<lower-1e-9 || price>=upper{{return Double.nan}}
  if price<=lower+1e-12{{return 0}}
  var lo=1e-10,hi=10.0
  if {HELPER}(s,k,t,r,hi,q,option)[0]<price{{return Double.nan}}
  for _ in 0..<180{{let mid=(lo+hi)/2;if {HELPER}(s,k,t,r,mid,q,option)[0]<price{{lo=mid}}else{{hi=mid}}}}
  return (lo+hi)/2
}}
'''
    elif lang == 'Kotlin':
        wrapper = f'''// {comment}
fun {fn}(price:Double,s:Double,k:Double,t:Double,r:Double,q:Double,option:String):Double{{
  require(listOf(price,s,k,t,r,q).all{{it.isFinite()}}&&s>0&&k>0&&t>0&&price>=0&&(option=="call"||option=="put")){{"Invalid IV inputs"}}
  val ds=s*exp(-q*t);val dk=k*exp(-r*t);val sign=if(option=="call")1.0 else -1.0
  val lower=max(sign*(ds-dk),0.0);val upper=if(sign>0)ds else dk
  require(price>=lower-1e-9&&price<upper){{"IV violates no-arbitrage bound"}}
  if(price<=lower+1e-12)return 0.0
  var lo=1e-10;var hi=10.0
  require({HELPER}(s,k,t,r,hi,q,option)[0]>=price){{"Unable to bracket IV"}}
  repeat(180){{val mid=(lo+hi)/2;if({HELPER}(s,k,t,r,mid,q,option)[0]<price)lo=mid else hi=mid}}
  return (lo+hi)/2
}}
'''
    elif lang == 'Go':
        wrapper = f'''// {comment}
func {fn}(price,s,k,t,r,q float64,option string)float64{{
  for _,v:=range []float64{{price,s,k,t,r,q}}{{if math.IsNaN(v)||math.IsInf(v,0){{return math.NaN()}}}}
  if s<=0||k<=0||t<=0||price<0||(option!="call"&&option!="put"){{return math.NaN()}}
  ds:=s*math.Exp(-q*t);dk:=k*math.Exp(-r*t);sign:=1.0;if option=="put"{{sign=-1}}
  lower:=math.Max(sign*(ds-dk),0);upper:=dk;if sign>0{{upper=ds}}
  if price<lower-1e-9||price>=upper{{return math.NaN()}}
  if price<=lower+1e-12{{return 0}}
  lo,hi:=1e-10,10.0
  if {HELPER}(s,k,t,r,hi,q,option)[0]<price{{return math.NaN()}}
  for i:=0;i<180;i++{{mid:=(lo+hi)/2;if {HELPER}(s,k,t,r,mid,q,option)[0]<price{{lo=mid}}else{{hi=mid}}}}
  return (lo+hi)/2
}}
'''
    elif lang == 'Rust':
        wrapper = f'''// {comment}
pub fn {fn}(price:f64,s:f64,k:f64,t:f64,r:f64,q:f64,option:&str)->f64{{
  if ![price,s,k,t,r,q].iter().all(|x|x.is_finite())||s<=0.0||k<=0.0||t<=0.0||price<0.0||(option!="call"&&option!="put"){{return f64::NAN;}}
  let ds=s*(-q*t).exp();let dk=k*(-r*t).exp();let sign=if option=="call"{{1.0}}else{{-1.0}};
  let lower=(sign*(ds-dk)).max(0.0);let upper=if sign>0.0{{ds}}else{{dk}};
  if price<lower-1e-9||price>=upper{{return f64::NAN;}}
  if price<=lower+1e-12{{return 0.0;}}
  let mut lo=1e-10_f64;let mut hi=10.0_f64;
  if {HELPER}(s,k,t,r,hi,q,option)[0]<price{{return f64::NAN;}}
  for _ in 0..180{{let mid=(lo+hi)/2.0;if {HELPER}(s,k,t,r,mid,q,option)[0]<price{{lo=mid;}}else{{hi=mid;}}}}
  (lo+hi)/2.0
}}
'''
    elif lang == 'R':
        wrapper = f'''# {comment}
{fn} <- function(price,s,k,t,r,q=0,option="call"){{
  if(any(!is.finite(c(price,s,k,t,r,q)))||s<=0||k<=0||t<=0||price<0||!(option %in% c("call","put")))stop("Invalid IV inputs")
  ds<-s*exp(-q*t);dk<-k*exp(-r*t);sign<-if(option=="call")1 else -1
  lower<-max(sign*(ds-dk),0);upper<-if(sign>0)ds else dk
  if(price<lower-1e-9||price>=upper)stop("IV violates no-arbitrage bound")
  if(price<=lower+1e-12)return(0)
  lo<-1e-10;hi<-10
  if({HELPER}(s,k,t,r,hi,q,option)[1]<price)stop("Unable to bracket IV")
  for(i in 1:180){{mid<-(lo+hi)/2;if({HELPER}(s,k,t,r,mid,q,option)[1]<price)lo<-mid else hi<-mid}}
  (lo+hi)/2
}}
'''
    elif lang == 'MATLAB':
        wrapper = f'''% {comment}
function result = {fn}(price,s,k,t,r,q,option)
  if ~isscalar(price) || any(~isfinite([price,s,k,t,r,q])) || s<=0 || k<=0 || t<=0 || price<0 || ~(strcmp(option,'call') || strcmp(option,'put'))
    error('Invalid IV inputs');
  end
  ds=s*exp(-q*t);dk=k*exp(-r*t);sign=1;if strcmp(option,'put'),sign=-1;end
  lower=max(sign*(ds-dk),0);upper=dk;if sign>0,upper=ds;end
  if price<lower-1e-9 || price>=upper,error('IV violates no-arbitrage bound');end
  if price<=lower+1e-12,result=0;return;end
  lo=1e-10;hi=10;
  vals={HELPER}(s,k,t,r,hi,q,option);if vals(1)<price,error('Unable to bracket IV');end
  for i=1:180
    mid=(lo+hi)/2;vals={HELPER}(s,k,t,r,mid,q,option);
    if vals(1)<price,lo=mid;else,hi=mid;end
  end
  result=(lo+hi)/2;
end
'''
    elif lang == 'Julia':
        wrapper = f'''# {comment}
function {fn}(price,s,k,t,r,q=0.0,option="call")
  if !all(isfinite,(price,s,k,t,r,q)) || s<=0 || k<=0 || t<=0 || price<0 || !(option in ("call","put"))
    throw(ArgumentError("Invalid IV inputs"))
  end
  ds=s*exp(-q*t);dk=k*exp(-r*t);sign=option=="call" ? 1.0 : -1.0
  lower=max(sign*(ds-dk),0);upper=sign>0 ? ds:dk
  if price<lower-1e-9 || price>=upper;throw(ArgumentError("IV violates no-arbitrage bound"));end
  if price<=lower+1e-12;return 0.0;end
  lo=1e-10;hi=10.0
  if {HELPER}(s,k,t,r,hi,q,option).Price<price;throw(ArgumentError("Unable to bracket IV"));end
  for _ in 1:180
    mid=(lo+hi)/2
    if {HELPER}(s,k,t,r,mid,q,option).Price<price;lo=mid;else;hi=mid;end
  end
  return (lo+hi)/2
end
'''
    else:
        raise GenerationError(f'{lang} IV emitter not available')
    if lang in ('Java', 'C#'):
        close = base.rfind('}')
        assert close > 0
        return base[:close] + wrapper + base[close:]
    if lang == 'MATLAB':
        # The primary MATLAB function must have the exported filename.
        return wrapper + '\n' + base
    return base + '\n' + wrapper
