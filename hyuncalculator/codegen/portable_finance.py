"""Standalone multi-language finance code generation: amortization and IRR.

All exported financial rates use decimal per-payment/per-period units.
Outputs and limitations are spelled out for each target; this module does not
execute user-entered code or import project internals into generated sources.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'fin_loan', 'fin_irr'})


def generate_finance(fn: str, formula, options) -> str:
    if options.language == 'Python':
        raise GenerationError('Python uses reference exporter')
    if options.structure != 'function' or options.iteration != 'auto' or options.variable_names:
        raise GenerationError('Portable finance supports function / auto with canonical parameter names')
    if options.variant != 'periodic' or options.imports not in ('auto','standard'):
        raise GenerationError('Portable finance requires periodic and standard math imports')
    if formula.function == 'fin_loan':
        return _loan(options.language, fn)
    if formula.function == 'fin_irr':
        return _irr(options.language, fn)
    raise GenerationError('Finance adapter is not implemented')


def _loan(lang: str, fn: str) -> str:
    """Return [payment, interest, principal_paid, remaining_balance]."""
    note='HyunCalculator FIN-006: [payment, interest, principal paid, remaining balance]. Rate is per installment.'
    if lang == 'R':
        return f'''# {note}
{fn} <- function(principal, rate, n, period) {{
  if (any(!is.finite(c(principal,rate,n,period))) || principal<0 || rate<=-1 || n<1 || n!=trunc(n) || period<1 || period>n || period!=trunc(period)) stop('Invalid loan inputs')
  if (abs(rate)<1e-14) {{
    payment<-principal/n; interest<-0; paid<-payment; balance<-max(0,principal-payment*period)
  }} else {{
    payment<-principal*rate/(1-(1+rate)^(-n))
    factor<-(1+rate)^(period-1)
    prev<-principal*factor-payment*(factor-1)/rate
    interest<-prev*rate; paid<-payment-interest; balance<-max(0,prev-paid)
  }}
  c(Payment=payment, Interest=interest, Principal=paid, Balance=balance)
}}
'''
    if lang == 'MATLAB':
        return f'''% {note}
function result = {fn}(principal,rate,n,period)
    if any(~isfinite([principal,rate,n,period])) || principal<0 || rate<=-1 || n<1 || n~=fix(n) || period<1 || period>n || period~=fix(period)
        error('Invalid loan inputs');
    end
    if abs(rate)<1e-14
        payment=principal/n;interest=0;paid=payment;balance=max(0,principal-payment*period);
    else
        payment=principal*rate/(1-(1+rate)^(-n));
        factor=(1+rate)^(period-1);
        prev=principal*factor-payment*(factor-1)/rate;
        interest=prev*rate;paid=payment-interest;balance=max(0,prev-paid);
    end
    result=[payment,interest,paid,balance];
end
'''
    if lang == 'Julia':
        return f'''# {note}
function {fn}(principal,rate,n,period)
    if !all(isfinite,(principal,rate,n,period)) || principal<0 || rate<=-1 || n<1 || n!=trunc(n) || period<1 || period>n || period!=trunc(period)
        throw(ArgumentError("Invalid loan inputs"))
    end
    if abs(rate)<1e-14
        payment=principal/n;interest=0.;paid=payment;balance=max(0.,principal-payment*period)
    else
        payment=principal*rate/(1-(1+rate)^(-n))
        factor=(1+rate)^(period-1)
        prev=principal*factor-payment*(factor-1)/rate
        interest=prev*rate;paid=payment-interest;balance=max(0.,prev-paid)
    end
    return [payment,interest,paid,balance]
end
'''
    if lang == 'C':
        return f'''/* {note} Invalid inputs return NaNs. */
#include <math.h>
typedef struct {{ double values[4]; }} HyunLoanResult;
HyunLoanResult {fn}(double principal,double rate,int n,int period) {{
    HyunLoanResult fail={{{{NAN,NAN,NAN,NAN}}}};
    if(!isfinite(principal)||!isfinite(rate)||principal<0||rate<=-1||n<1||period<1||period>n) return fail;
    double payment,interest,paid,balance;
    if(fabs(rate)<1e-14){{payment=principal/n;interest=0;paid=payment;balance=fmax(0,principal-payment*period);}}
    else {{
        payment=principal*rate/(1-pow(1+rate,-n));
        double factor=pow(1+rate,period-1);
        double prev=principal*factor-payment*(factor-1)/rate;
        interest=prev*rate;paid=payment-interest;balance=fmax(0,prev-paid);
    }}
    HyunLoanResult out={{{{payment,interest,paid,balance}}}};return out;
}}
'''
    if lang == 'C++':
        return f'''// {note}
#include <array>
#include <algorithm>
#include <cmath>
#include <stdexcept>
std::array<double,4> {fn}(double principal,double rate,int n,int period) {{
    if(!std::isfinite(principal)||!std::isfinite(rate)||principal<0||rate<=-1||n<1||period<1||period>n) throw std::invalid_argument("Invalid loan inputs");
    double payment,interest,paid,balance;
    if(std::abs(rate)<1e-14){{payment=principal/n;interest=0;paid=payment;balance=std::max(0.0,principal-payment*period);}}
    else {{
        payment=principal*rate/(1-std::pow(1+rate,-n));
        double factor=std::pow(1+rate,period-1);
        double prev=principal*factor-payment*(factor-1)/rate;
        interest=prev*rate;paid=payment-interest;balance=std::max(0.0,prev-paid);
    }}
    return {{payment,interest,paid,balance}};
}}
'''
    if lang in ('JavaScript','TypeScript'):
        params='principal: number, rate: number, n: number, period: number' if lang=='TypeScript' else 'principal, rate, n, period'
        typ=': number[]' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({params}){typ} {{
  if (![principal,rate,n,period].every(Number.isFinite)||principal<0||rate<=-1||!Number.isInteger(n)||n<1||!Number.isInteger(period)||period<1||period>n) throw new RangeError("Invalid loan inputs");
  let payment,interest,paid,balance;
  if(Math.abs(rate)<1e-14){{payment=principal/n;interest=0;paid=payment;balance=Math.max(0,principal-payment*period);}}
  else {{
    payment=principal*rate/(1-Math.pow(1+rate,-n));
    const factor=Math.pow(1+rate,period-1);
    const prev=principal*factor-payment*(factor-1)/rate;
    interest=prev*rate;paid=payment-interest;balance=Math.max(0,prev-paid);
  }}
  return [payment,interest,paid,balance];
}}
'''
    if lang == 'Java':
        return f'''// {note}
public class GeneratedCalculator {{
  public static double[] {fn}(double principal,double rate,int n,int period) {{
    if(!Double.isFinite(principal)||!Double.isFinite(rate)||principal<0||rate<=-1||n<1||period<1||period>n) throw new IllegalArgumentException("Invalid loan inputs");
    double payment,interest,paid,balance;
    if(Math.abs(rate)<1e-14){{payment=principal/n;interest=0;paid=payment;balance=Math.max(0,principal-payment*period);}}
    else {{
      payment=principal*rate/(1-Math.pow(1+rate,-n));
      double factor=Math.pow(1+rate,period-1);
      double prev=principal*factor-payment*(factor-1)/rate;
      interest=prev*rate;paid=payment-interest;balance=Math.max(0,prev-paid);
    }}
    return new double[]{{payment,interest,paid,balance}};
  }}
}}
'''
    if lang == 'C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double principal,double rate,int n,int period) {{
    if(double.IsNaN(principal)||double.IsInfinity(principal)||double.IsNaN(rate)||double.IsInfinity(rate)||principal<0||rate<=-1||n<1||period<1||period>n) throw new ArgumentException("Invalid loan inputs");
    double payment,interest,paid,balance;
    if(Math.Abs(rate)<1e-14){{payment=principal/n;interest=0;paid=payment;balance=Math.Max(0,principal-payment*period);}}
    else {{
      payment=principal*rate/(1-Math.Pow(1+rate,-n));
      double factor=Math.Pow(1+rate,period-1);
      double prev=principal*factor-payment*(factor-1)/rate;
      interest=prev*rate;paid=payment-interest;balance=Math.Max(0,prev-paid);
    }}
    return new double[]{{payment,interest,paid,balance}};
  }}
}}
'''
    if lang == 'Swift':
        return f'''// {note}
import Foundation
func {fn}(_ principal: Double,_ rate: Double,_ n: Int,_ period: Int) -> [Double] {{
  if !principal.isFinite || !rate.isFinite || principal<0 || rate <= -1 || n<1 || period<1 || period>n {{return Array(repeating: Double.nan,count: 4)}}
  let payment: Double,interest: Double,paid: Double,balance: Double
  if abs(rate)<1e-14 {{payment=principal/Double(n);interest=0;paid=payment;balance=max(0,principal-payment*Double(period))}}
  else {{
    payment=principal*rate/(1-pow(1+rate,-Double(n)))
    let factor=pow(1+rate,Double(period-1))
    let prev=principal*factor-payment*(factor-1)/rate
    interest=prev*rate;paid=payment-interest;balance=max(0,prev-paid)
  }}
  return [payment,interest,paid,balance]
}}
'''
    if lang == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(principal: Double,rate: Double,n: Int,period: Int): DoubleArray {{
  require(principal.isFinite() && rate.isFinite() && principal>=0 && rate> -1 && n>=1 && period>=1 && period<=n) {{"Invalid loan inputs"}}
  val payment: Double; val interest: Double; val paid: Double; val balance: Double
  if(abs(rate)<1e-14){{payment=principal/n;interest=0.0;paid=payment;balance=max(0.0,principal-payment*period)}}
  else {{
    payment=principal*rate/(1-(1+rate).pow(-n))
    val factor=(1+rate).pow(period-1)
    val prev=principal*factor-payment*(factor-1)/rate
    interest=prev*rate;paid=payment-interest;balance=max(0.0,prev-paid)
  }}
  return doubleArrayOf(payment,interest,paid,balance)
}}
'''
    if lang == 'Go':
        return f'''// {note}
package main
import "math"
func {fn}(principal,rate float64,n,period int) []float64 {{
  if math.IsNaN(principal)||math.IsInf(principal,0)||math.IsNaN(rate)||math.IsInf(rate,0)||principal<0||rate<=-1||n<1||period<1||period>n {{return []float64{{math.NaN(),math.NaN(),math.NaN(),math.NaN()}}}}
  var payment,interest,paid,balance float64
  if math.Abs(rate)<1e-14 {{payment=principal/float64(n);interest=0;paid=payment;balance=math.Max(0,principal-payment*float64(period))}} else {{
    payment=principal*rate/(1-math.Pow(1+rate,-float64(n)))
    factor:=math.Pow(1+rate,float64(period-1))
    prev:=principal*factor-payment*(factor-1)/rate
    interest=prev*rate;paid=payment-interest;balance=math.Max(0,prev-paid)
  }}
  return []float64{{payment,interest,paid,balance}}
}}
'''
    if lang == 'Rust':
        return f'''// {note}
pub fn {fn}(principal:f64,rate:f64,n:i32,period:i32)->[f64;4] {{
  if !principal.is_finite()||!rate.is_finite()||principal<0.0||rate<=-1.0||n<1||period<1||period>n {{return [f64::NAN;4];}}
  let (payment,interest,paid,balance):(f64,f64,f64,f64);
  if rate.abs()<1e-14 {{payment=principal/(n as f64);interest=0.0;paid=payment;balance=(principal-payment*(period as f64)).max(0.0);}}
  else {{
    payment=principal*rate/(1.0-(1.0+rate).powi(-n));
    let factor=(1.0+rate).powi(period-1);
    let prev=principal*factor-payment*(factor-1.0)/rate;
    interest=prev*rate;paid=payment-interest;balance=(prev-paid).max(0.0);
  }}
  [payment,interest,paid,balance]
}}
'''
    raise GenerationError(f'Loan adapter unavailable for {lang}')


def _irr(lang: str, fn: str) -> str:
    """IRR by bounded grid scan + bisection, rejecting multiple roots.

    Matches v1.1 policy: two signs, 680 rates across [-.9999,1e5], no
    unbounded Newton iteration; tangential roots can be missed. Returns scalar.
    """
    note='HyunCalculator FIN-005: scan 680 rates, bisect brackets, reject multiple IRRs. Returns annual/per-period rate as decimal.'
    if lang == 'R':
        return f'''# {note}
{fn} <- function(flows) {{
  if(length(flows)<2 || length(flows)>10000 || any(!is.finite(flows)) || !any(flows>0) || !any(flows<0)) stop("Invalid IRR cashflows")
  value_at <- function(rate) {{
    factor<-1/(1+rate); result<-flows[length(flows)]
    if(length(flows)>1) for(j in (length(flows)-1):1) result<-result*factor+flows[j]
    result
  }}
  rates<-c(seq(-0.9999,-0.9,length.out=80),seq(-0.9,1,length.out=400),exp(seq(log(2),log(1e5),length.out=200)))
  roots<-numeric(0);prev<-0;prev_val<-0;hasprev<-FALSE
  for(rate in rates) {{
    val<-value_at(rate); if(!is.finite(val)) {{hasprev<-FALSE;next}}
    root<-NA_real_
    if(val==0) root<-rate
    else if(hasprev && ((prev_val<0 && val>0)||(prev_val>0 && val<0))) {{
      lo<-prev; hi<-rate; fl<-prev_val
      for(j in 1:120) {{
        mid<-(lo+hi)/2; fm<-value_at(mid)
        if(fm==0) {{lo<-mid;hi<-mid;break}}
        if((fl<0 && fm<0)||(fl>0 && fm>0)) {{lo<-mid;fl<-fm}} else hi<-mid
      }}
      root<-(lo+hi)/2
    }}
    if(is.finite(root) && !any(abs(roots-root)<1e-7)) {{roots<-c(roots,root);if(length(roots)>1)stop("Multiple IRRs")}}
    prev<-rate;prev_val<-val;hasprev<-TRUE
  }}
  if(length(roots)!=1) stop("No unique IRR in scanned range")
  roots[1]
}}
'''
    if lang == 'MATLAB':
        return f'''% {note}
function result = {fn}(flows)
    flows=flows(:);
    if numel(flows)<2 || numel(flows)>10000 || any(~isfinite(flows)) || ~any(flows>0) || ~any(flows<0)
        error('Invalid IRR cashflows');
    end
    rates=[linspace(-0.9999,-0.9,80),linspace(-0.9,1,400),exp(linspace(log(2),log(1e5),200))];
    roots=[];hasprev=false;prev=0;prevval=0;
    for rate=rates
        val=irr_value(flows,rate);
        if ~isfinite(val)
            hasprev=false;continue;
        end
        root=NaN;
        if val==0
            root=rate;
        elseif hasprev && ((prevval<0 && val>0)||(prevval>0 && val<0))
            lo=prev;hi=rate;fl=prevval;
            for j=1:120
                mid=(lo+hi)/2;fm=irr_value(flows,mid);
                if fm==0
                    lo=mid;hi=mid;break;
                end
                if (fl<0 && fm<0)||(fl>0 && fm>0)
                    lo=mid;fl=fm;
                else
                    hi=mid;
                end
            end
            root=(lo+hi)/2;
        end
        if isfinite(root) && ~any(abs(roots-root)<1e-7)
            roots=[roots,root];
            if numel(roots)>1;error('Multiple IRRs');end
        end
        prev=rate;prevval=val;hasprev=true;
    end
    if numel(roots)~=1;error('No unique IRR');end
    result=roots(1);
end
function result=irr_value(flows,rate)
    factor=1/(1+rate);result=flows(end);
    for i=(numel(flows)-1):-1:1
        result=result*factor+flows(i);
    end
end
'''
    if lang == 'Julia':
        return f'''# {note}
function {fn}(flows)
    if length(flows)<2 || length(flows)>10000 || !all(isfinite,flows) || !any(x->x>0,flows) || !any(x->x<0,flows)
        throw(ArgumentError("Invalid IRR cashflows"))
    end
    value_at(rate)=begin
        factor=1/(1+rate);value=flows[end]
        for i in (length(flows)-1):-1:1
            value=value*factor+flows[i]
        end
        value
    end
    rates=vcat(range(-.9999,-.9,length=80),range(-.9,1,length=400),exp.(range(log(2),log(1e5),length=200)))
    roots=Float64[];hasprev=false;prev=0.;prevval=0.
    for rate in rates
        val=value_at(rate)
        if !isfinite(val);hasprev=false;continue;end
        root=NaN
        if val==0
            root=rate
        elseif hasprev && ((prevval<0 && val>0)||(prevval>0 && val<0))
            lo=prev;hi=rate;fl=prevval
            for _ in 1:120
                mid=(lo+hi)/2;fm=value_at(mid)
                if fm==0;lo=mid;hi=mid;break;end
                if (fl<0 && fm<0)||(fl>0 && fm>0)
                    lo=mid;fl=fm
                else
                    hi=mid
                end
            end
            root=(lo+hi)/2
        end
        if isfinite(root) && !any(x->abs(x-root)<1e-7,roots)
            push!(roots,root)
            if length(roots)>1;throw(ArgumentError("Multiple IRRs"));end
        end
        prev=rate;prevval=val;hasprev=true
    end
    length(roots)==1 || throw(ArgumentError("No unique IRR"))
    return roots[1]
end
'''
    if lang == 'C':
        return f'''/* {note} Invalid inputs return NaN. */
#include <math.h>
#include <stddef.h>
static double hyun_irr_value(const double *flows,size_t n,double rate) {{
  double factor=1.0/(1.0+rate),value=flows[n-1];
  for(size_t i=n-1;i>0;i--) value=value*factor+flows[i-1];
  return value;
}}
double {fn}(const double *flows,size_t n) {{
  if(!flows||n<2||n>10000) return NAN;
  int pos=0,neg=0;
  for(size_t i=0;i<n;i++){{if(!isfinite(flows[i]))return NAN;pos|=flows[i]>0;neg|=flows[i]<0;}}
  if(!pos||!neg)return NAN;
  int count=0;double root=0,prev=0,prevval=0;int hasprev=0;
  for(int i=0;i<680;i++){{
    double rate=(i<80)?(-0.9999+0.0999*i/79.0):((i<480)?(-0.9+1.9*(i-80)/399.0):exp(log(2.0)+log(50000.0)*(i-480)/199.0));
    double val=hyun_irr_value(flows,n,rate);
    if(!isfinite(val)){{hasprev=0;continue;}}
    double candidate=NAN;
    if(val==0)candidate=rate;
    else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){{
      double lo=prev,hi=rate,fl=prevval;
      for(int j=0;j<120;j++){{
        double mid=(lo+hi)/2.0,fm=hyun_irr_value(flows,n,mid);
        if(fm==0){{lo=hi=mid;break;}}
        if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm;}}else hi=mid;
      }}
      candidate=(lo+hi)/2.0;
    }}
    if(isfinite(candidate) && (!count||fabs(candidate-root)>=1e-7)){{root=candidate;if(++count>1)return NAN;}}
    prev=rate;prevval=val;hasprev=1;
  }}
  return count==1?root:NAN;
}}
'''
    if lang == 'C++':
        return f'''// {note}
#include <cmath>
#include <stdexcept>
#include <vector>
static double hyun_irr_value(const std::vector<double>& flows,double rate) {{
  double factor=1.0/(1.0+rate),value=flows.back();
  for(size_t i=flows.size()-1;i>0;i--)value=value*factor+flows[i-1];
  return value;
}}
double {fn}(const std::vector<double>& flows) {{
  if(flows.size()<2||flows.size()>10000)throw std::invalid_argument("Invalid IRR cashflows");
  bool pos=false,neg=false;
  for(double x:flows){{if(!std::isfinite(x))throw std::invalid_argument("Nonfinite cashflow");pos|=x>0;neg|=x<0;}}
  if(!pos||!neg)throw std::invalid_argument("IRR requires positive and negative cashflows");
  std::vector<double> roots;double prev=0,prevval=0;bool hasprev=false;
  for(int i=0;i<680;i++){{
    double rate=i<80?(-0.9999+0.0999*i/79.0):i<480?(-0.9+1.9*(i-80)/399.0):std::exp(std::log(2.0)+std::log(50000.0)*(i-480)/199.0);
    double val=hyun_irr_value(flows,rate);
    if(!std::isfinite(val)){{hasprev=false;continue;}}
    double root=NAN;
    if(val==0)root=rate;
    else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){{
      double lo=prev,hi=rate,fl=prevval;
      for(int j=0;j<120;j++){{
        double mid=(lo+hi)/2,fm=hyun_irr_value(flows,mid);
        if(fm==0){{lo=hi=mid;break;}}
        if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm;}}else hi=mid;
      }}
      root=(lo+hi)/2;
    }}
    if(std::isfinite(root)){{
      bool duplicate=false;for(double x:roots)duplicate|=std::abs(x-root)<1e-7;
      if(!duplicate){{roots.push_back(root);if(roots.size()>1)throw std::invalid_argument("Multiple IRRs");}}
    }}
    prev=rate;prevval=val;hasprev=true;
  }}
  if(roots.size()!=1)throw std::invalid_argument("No unique IRR");
  return roots[0];
}}
'''
    if lang in ('JavaScript','TypeScript'):
        params='flows: number[]' if lang=='TypeScript' else 'flows'
        ret=': number' if lang=='TypeScript' else ''
        ann=': number' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({params}){ret} {{
  if(!Array.isArray(flows)||flows.length<2||flows.length>10000||!flows.every(Number.isFinite)||!flows.some(x=>x>0)||!flows.some(x=>x<0)) throw new RangeError("Invalid IRR cashflows");
  const valueAt=(rate{ann}){ann}=>{{let result=flows[flows.length-1],factor=1/(1+rate);for(let j=flows.length-2;j>=0;j--)result=result*factor+flows[j];return result;}};
  const roots{': number[]' if lang=='TypeScript' else ''}=[];let prev=0,prevval=0,hasprev=false;
  for(let i=0;i<680;i++){{
    const rate=i<80?(-0.9999+0.0999*i/79):i<480?(-0.9+1.9*(i-80)/399):Math.exp(Math.log(2)+Math.log(50000)*(i-480)/199);
    const val=valueAt(rate);if(!Number.isFinite(val)){{hasprev=false;continue;}}
    let root=NaN;
    if(val===0)root=rate;
    else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){{
      let lo=prev,hi=rate,fl=prevval;
      for(let j=0;j<120;j++){{const mid=(lo+hi)/2,fm=valueAt(mid);if(fm===0){{lo=hi=mid;break;}}if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm;}}else hi=mid;}}
      root=(lo+hi)/2;
    }}
    if(Number.isFinite(root)&&!roots.some(x=>Math.abs(x-root)<1e-7)){{roots.push(root);if(roots.length>1)throw new RangeError("Multiple IRRs");}}
    prev=rate;prevval=val;hasprev=true;
  }}
  if(roots.length!==1)throw new RangeError("No unique IRR");return roots[0];
}}
'''
    if lang == 'Java':
        return f'''// {note}
public class GeneratedCalculator {{
  private static double hyunValue(double[] flows,double rate) {{
    double factor=1/(1+rate),result=flows[flows.length-1];
    for(int j=flows.length-2;j>=0;j--)result=result*factor+flows[j];return result;
  }}
  public static double {fn}(double[] flows) {{
    if(flows==null||flows.length<2||flows.length>10000)throw new IllegalArgumentException("Invalid IRR cashflows");
    boolean pos=false,neg=false;
    for(double x:flows){{if(!Double.isFinite(x))throw new IllegalArgumentException("Nonfinite cashflow");pos|=x>0;neg|=x<0;}}
    if(!pos||!neg)throw new IllegalArgumentException("Missing cashflow sign");
    java.util.ArrayList<Double> roots=new java.util.ArrayList<>();double prev=0,prevval=0;boolean hasprev=false;
    for(int i=0;i<680;i++){{
      double rate=i<80?(-0.9999+0.0999*i/79.0):i<480?(-0.9+1.9*(i-80)/399.0):Math.exp(Math.log(2)+Math.log(50000)*(i-480)/199.0);
      double val=hyunValue(flows,rate);if(!Double.isFinite(val)){{hasprev=false;continue;}}
      double root=Double.NaN;
      if(val==0)root=rate;
      else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){{
        double lo=prev,hi=rate,fl=prevval;
        for(int j=0;j<120;j++){{double mid=(lo+hi)/2,fm=hyunValue(flows,mid);if(fm==0){{lo=hi=mid;break;}}if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm;}}else hi=mid;}}
        root=(lo+hi)/2;
      }}
      if(Double.isFinite(root)){{boolean dup=false;for(double x:roots)dup|=Math.abs(x-root)<1e-7;if(!dup){{roots.add(root);if(roots.size()>1)throw new IllegalArgumentException("Multiple IRRs");}}}}
      prev=rate;prevval=val;hasprev=true;
    }}
    if(roots.size()!=1)throw new IllegalArgumentException("No unique IRR");return roots.get(0);
  }}
}}
'''
    if lang == 'C#':
        return f'''// {note}
using System;
using System.Collections.Generic;
public static class GeneratedCalculator {{
  private static double HyunValue(double[] flows,double rate) {{
    double factor=1/(1+rate),value=flows[flows.Length-1];
    for(int j=flows.Length-2;j>=0;j--)value=value*factor+flows[j];return value;
  }}
  public static double {fn}(double[] flows) {{
    if(flows==null||flows.Length<2||flows.Length>10000)throw new ArgumentException("Invalid IRR cashflows");
    bool pos=false,neg=false;
    foreach(double x in flows){{if(double.IsNaN(x)||double.IsInfinity(x))throw new ArgumentException("Nonfinite cashflow");pos|=x>0;neg|=x<0;}}
    if(!pos||!neg)throw new ArgumentException("Missing cashflow sign");
    var roots=new List<double>();double prev=0,prevval=0;bool hasprev=false;
    for(int i=0;i<680;i++){{
      double rate=i<80?(-0.9999+0.0999*i/79.0):i<480?(-0.9+1.9*(i-80)/399.0):Math.Exp(Math.Log(2)+Math.Log(50000)*(i-480)/199.0);
      double val=HyunValue(flows,rate);if(double.IsNaN(val)||double.IsInfinity(val)){{hasprev=false;continue;}}
      double root=double.NaN;
      if(val==0)root=rate;
      else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){{
        double lo=prev,hi=rate,fl=prevval;
        for(int j=0;j<120;j++){{double mid=(lo+hi)/2,fm=HyunValue(flows,mid);if(fm==0){{lo=hi=mid;break;}}if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm;}}else hi=mid;}}
        root=(lo+hi)/2;
      }}
      if(!double.IsNaN(root)&&!double.IsInfinity(root)){{bool dup=false;foreach(double x in roots)dup|=Math.Abs(x-root)<1e-7;if(!dup){{roots.Add(root);if(roots.Count>1)throw new ArgumentException("Multiple IRRs");}}}}
      prev=rate;prevval=val;hasprev=true;
    }}
    if(roots.Count!=1)throw new ArgumentException("No unique IRR");return roots[0];
  }}
}}
'''
    if lang == 'Swift':
        return f'''// {note}
import Foundation
func {fn}(_ flows: [Double]) -> Double {{
  if flows.count<2 || flows.count>10000 || !flows.allSatisfy({{$0.isFinite}}) || !flows.contains(where:{{$0>0}}) || !flows.contains(where:{{$0<0}}) {{return Double.nan}}
  func valueAt(_ rate: Double) -> Double {{
    let factor=1/(1+rate);var value=flows[flows.count-1]
    for j in stride(from:flows.count-2,through:0,by:-1) {{value=value*factor+flows[j]}}
    return value
  }}
  var roots=[Double]();var prev=0.0;var prevval=0.0;var hasprev=false
  for i in 0..<680 {{
    let rate: Double=i<80 ? (-0.9999+0.0999*Double(i)/79) : (i<480 ? (-0.9+1.9*Double(i-80)/399) : exp(log(2)+log(50000)*Double(i-480)/199))
    let val=valueAt(rate);if !val.isFinite {{hasprev=false;continue}}
    var root=Double.nan
    if val==0 {{root=rate}}
    else if hasprev && ((prevval<0 && val>0)||(prevval>0 && val<0)) {{
      var lo=prev;var hi=rate;var fl=prevval
      for _ in 0..<120 {{
        let mid=(lo+hi)/2;let fm=valueAt(mid)
        if fm==0 {{lo=mid;hi=mid;break}}
        if (fl<0 && fm<0)||(fl>0 && fm>0) {{lo=mid;fl=fm}} else {{hi=mid}}
      }}
      root=(lo+hi)/2
    }}
    if root.isFinite && !roots.contains(where:{{abs($0-root)<1e-7}}) {{roots.append(root);if roots.count>1 {{return Double.nan}}}}
    prev=rate;prevval=val;hasprev=true
  }}
  return roots.count==1 ? roots[0] : Double.nan
}}
'''
    if lang == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(flows: DoubleArray): Double {{
  require(flows.size in 2..10000 && flows.all {{it.isFinite()}} && flows.any {{it>0}} && flows.any {{it<0}}) {{"Invalid IRR cashflows"}}
  fun valueAt(rate: Double): Double {{
    val factor=1/(1+rate);var value=flows.last()
    for(j in flows.size-2 downTo 0) value=value*factor+flows[j]
    return value
  }}
  val roots=mutableListOf<Double>();var prev=0.0;var prevval=0.0;var hasprev=false
  for(i in 0 until 680) {{
    val rate=if(i<80) (-0.9999+0.0999*i/79.0) else if(i<480) (-0.9+1.9*(i-80)/399.0) else exp(ln(2.0)+ln(50000.0)*(i-480)/199.0)
    val value=valueAt(rate);if(!value.isFinite()){{hasprev=false;continue}}
    var root=Double.NaN
    if(value==0.0)root=rate
    else if(hasprev&&((prevval<0&&value>0)||(prevval>0&&value<0))){{
      var lo=prev;var hi=rate;var fl=prevval
      for(j in 0 until 120){{val mid=(lo+hi)/2;val fm=valueAt(mid);if(fm==0.0){{lo=mid;hi=mid;break}};if((fl<0&&fm<0)||(fl>0&&fm>0)){{lo=mid;fl=fm}}else hi=mid}}
      root=(lo+hi)/2
    }}
    if(root.isFinite() && roots.none {{abs(it-root)<1e-7}}){{roots.add(root);require(roots.size<=1){{"Multiple IRRs"}}}}
    prev=rate;prevval=value;hasprev=true
  }}
  require(roots.size==1){{"No unique IRR"}}
  return roots[0]
}}
'''
    if lang == 'Go':
        return f'''// {note}
package main
import "math"
func {fn}(flows []float64) float64 {{
  if len(flows)<2||len(flows)>10000 {{return math.NaN()}}
  pos,neg:=false,false
  for _,x:=range flows{{if math.IsNaN(x)||math.IsInf(x,0){{return math.NaN()}};pos=pos||x>0;neg=neg||x<0}}
  if !pos||!neg{{return math.NaN()}}
  valueAt:=func(rate float64)float64{{factor:=1/(1+rate);value:=flows[len(flows)-1];for j:=len(flows)-2;j>=0;j--{{value=value*factor+flows[j]}};return value}}
  roots:=make([]float64,0,2);var prev,prevval float64;hasprev:=false
  for i:=0;i<680;i++{{
    var rate float64
    if i<80{{rate=-0.9999+0.0999*float64(i)/79}}else if i<480{{rate=-0.9+1.9*float64(i-80)/399}}else{{rate=math.Exp(math.Log(2)+math.Log(50000)*float64(i-480)/199)}}
    val:=valueAt(rate);if math.IsNaN(val)||math.IsInf(val,0){{hasprev=false;continue}}
    root:=math.NaN()
    if val==0{{root=rate}}else if hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0)){{
      lo,hi,fl:=prev,rate,prevval
      for j:=0;j<120;j++{{mid:=(lo+hi)/2;fm:=valueAt(mid);if fm==0{{lo=mid;hi=mid;break}};if (fl<0&&fm<0)||(fl>0&&fm>0){{lo=mid;fl=fm}}else{{hi=mid}}}}
      root=(lo+hi)/2
    }}
    if !math.IsNaN(root)&&!math.IsInf(root,0){{dup:=false;for _,v:=range roots{{if math.Abs(v-root)<1e-7{{dup=true}}}};if !dup{{roots=append(roots,root);if len(roots)>1{{return math.NaN()}}}}}}
    prev=rate;prevval=val;hasprev=true
  }}
  if len(roots)!=1{{return math.NaN()}};return roots[0]
}}
'''
    if lang == 'Rust':
        return f'''// {note}
pub fn {fn}(flows:&[f64])->f64{{
  if flows.len()<2||flows.len()>10000||!flows.iter().all(|x|x.is_finite())||!flows.iter().any(|x|*x>0.0)||!flows.iter().any(|x|*x<0.0){{return f64::NAN;}}
  fn value_at(flows:&[f64],rate:f64)->f64{{let factor=1.0/(1.0+rate);let mut v=flows[flows.len()-1];for j in (0..flows.len()-1).rev(){{v=v*factor+flows[j];}}v}}
  let mut roots:Vec<f64>=Vec::new();let mut prev=0.0;let mut prevval=0.0;let mut hasprev=false;
  for i in 0..680{{
    let rate=if i<80{{-0.9999+0.0999*(i as f64)/79.0}}else if i<480{{-0.9+1.9*((i-80) as f64)/399.0}}else{{(2.0_f64.ln()+50000.0_f64.ln()*((i-480) as f64)/199.0).exp()}};
    let val=value_at(flows,rate);if !val.is_finite(){{hasprev=false;continue;}}
    let mut root=f64::NAN;
    if val==0.0{{root=rate;}}
    else if hasprev&&((prevval<0.0&&val>0.0)||(prevval>0.0&&val<0.0)){{
      let mut lo=prev;let mut hi=rate;let mut fl=prevval;
      for _ in 0..120{{let mid=(lo+hi)/2.0;let fm=value_at(flows,mid);if fm==0.0{{lo=mid;hi=mid;break;}}if (fl<0.0&&fm<0.0)||(fl>0.0&&fm>0.0){{lo=mid;fl=fm;}}else{{hi=mid;}}}}
      root=(lo+hi)/2.0;
    }}
    if root.is_finite()&&!roots.iter().any(|x|(*x-root).abs()<1e-7){{roots.push(root);if roots.len()>1{{return f64::NAN;}}}}
    prev=rate;prevval=val;hasprev=true;
  }}
  if roots.len()!=1{{return f64::NAN;}}roots[0]
}}
'''
    raise GenerationError(f'IRR adapter unavailable for {lang}')
