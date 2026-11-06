"""Portable one-asset, no-lookahead backtest source generator for 13 languages.

Inputs: returns, close-time signals, commission_bps, slippage_bps, rf_per_period,
periods_per_year. No financing, borrow, dividends or end liquidation.
Output flat vector length 4*n+14, with 12 metrics, n delayed positions,
n net returns, n+1 equity curve, n+1 buy-and-hold curve.
"""
from __future__ import annotations
SUPPORTED=frozenset({'qf_backtest'})


def generate_backtest(fn,formula,opt):
    from .emitter import GenerationError
    if opt.language=='Python' or opt.structure!='function' or opt.iteration!='auto' or opt.variable_names or opt.variant!='periodic' or opt.imports not in ('auto','standard'):
        raise GenerationError('Backtest generator supports non-Python function/auto/standard imports only')
    lang=opt.language
    note=('HyunCalculator STRAT-002: output flat [net compounded,gross compounded,buyhold compounded,CAGR,vol,Sharpe,Sortino,MDD,active win rate,executed changes,total turnover,total cost,positions(n),net(n),equity(n+1),buyhold(n+1)]. Signals delayed 1 period; no final liquidation.')
    if lang=='C':
        return f'''/* {note} */
#include <math.h>
#include <stddef.h>
/* output buffer requires 4*n+14 doubles. returns 1 on success, 0 on error. */
int {fn}(const double *r,const double *sig,size_t n,double commission,double slippage,double rf,int ppy,double *out,size_t capacity) {{
  if(!r||!sig||!out||n<3||n>100000||capacity<4*n+14||!isfinite(commission)||!isfinite(slippage)||!isfinite(rf)||commission<0||slippage<0||ppy<1||ppy>1000000)return 0;
  for(size_t t=0;t<n;t++)if(!isfinite(r[t])||r[t]<=-1||!isfinite(sig[t])||fabs(sig[t])>1)return 0;
  double netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0;size_t active=0,wins=0,changes=0;
  out[12+2*n]=1;out[13+3*n]=1;
  for(size_t t=0;t<n;t++){{
    double pos=t?sig[t-1]:0,turn=fabs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
    if(net<=-1||!isfinite(net))return 0;
    out[12+t]=pos;out[12+n+t]=net;prev=pos;
    netW*=1+net;grossW*=1+gross;buyW*=1+r[t];
    out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW;
    peak=fmax(peak,netW);mdd=fmin(mdd,netW/peak-1);
    sum+=net;double downside=fmin(net-rf,0);down+=downside*downside;
    turnTotal+=turn;costTotal+=cost;if(turn>1e-12)changes++;
    if(fabs(pos)>1e-12){{active++;if(net>0)wins++;}}
  }}
  double avg=sum/n,ex=avg-rf,sq=0;for(size_t t=0;t<n;t++){{double e=out[12+n+t]-avg;sq+=e*e;}}
  double std=sqrt(sq/(n-1)),dv=sqrt(down/n),annual=sqrt((double)ppy);
  double values[12]={{netW-1,grossW-1,buyW-1,pow(netW,(double)ppy/n)-1,std*annual,std>0?ex/std*annual:NAN,dv>0?ex/dv*annual:NAN,mdd,active?(double)wins/active:NAN,(double)changes,turnTotal,costTotal}};
  for(size_t i=0;i<12;i++){{out[i]=values[i];}}
  return 1;
}}
'''
    if lang=='C++':
        return f'''// {note}
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>
std::vector<double> {fn}(const std::vector<double>& r,const std::vector<double>& sig,double commission,double slippage,double rf,int ppy){{
  const size_t n=r.size();if(n<3||n>100000||sig.size()!=n||!std::isfinite(commission)||!std::isfinite(slippage)||!std::isfinite(rf)||commission<0||slippage<0||ppy<1||ppy>1000000)throw std::invalid_argument("Invalid backtest inputs");
  for(size_t t=0;t<n;t++)if(!std::isfinite(r[t])||r[t]<=-1||!std::isfinite(sig[t])||std::fabs(sig[t])>1)throw std::invalid_argument("Invalid series");
  std::vector<double> out(4*n+14,0);out[12+2*n]=1;out[13+3*n]=1;
  double netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0;size_t active=0,wins=0,changes=0;
  for(size_t t=0;t<n;t++){{double pos=t?sig[t-1]:0,turn=std::fabs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
    if(net<=-1||!std::isfinite(net))throw std::invalid_argument("Invalid net return");
    out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW;
    peak=std::max(peak,netW);mdd=std::min(mdd,netW/peak-1);sum+=net;double d=std::min(net-rf,0.0);down+=d*d;turnTotal+=turn;costTotal+=cost;
    if(turn>1e-12){{changes++;}}
    if(std::fabs(pos)>1e-12){{active++;if(net>0)wins++;}}
  }}
  double avg=sum/n,ex=avg-rf,sq=0;for(size_t t=0;t<n;t++){{double e=out[12+n+t]-avg;sq+=e*e;}}
  double st=std::sqrt(sq/(n-1)),dv=std::sqrt(down/n),annual=std::sqrt(double(ppy));
  double values[12]={{netW-1,grossW-1,buyW-1,std::pow(netW,double(ppy)/n)-1,st*annual,st>0?ex/st*annual:NAN,dv>0?ex/dv*annual:NAN,mdd,active?double(wins)/active:NAN,double(changes),turnTotal,costTotal}};
  for(size_t i=0;i<12;i++){{out[i]=values[i];}}
  return out;
}}
'''
    if lang in ('JavaScript','TypeScript'):
        args='r: number[], sig: number[], commission: number, slippage: number, rf: number, ppy: number' if lang=='TypeScript' else 'r, sig, commission, slippage, rf, ppy'
        ret=': number[]' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({args}){ret}{{
  if(!Array.isArray(r)||!Array.isArray(sig)||r.length<3||r.length>100000||sig.length!==r.length||![commission,slippage,rf].every(Number.isFinite)||commission<0||slippage<0||!Number.isInteger(ppy)||ppy<1||ppy>1000000)throw new RangeError("Invalid backtest inputs");
  const n=r.length;for(let t=0;t<n;t++)if(!Number.isFinite(r[t])||r[t]<=-1||!Number.isFinite(sig[t])||Math.abs(sig[t])>1)throw new RangeError("Invalid series");
  const out=Array(4*n+14).fill(0);out[12+2*n]=1;out[13+3*n]=1;
  let netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0,active=0,wins=0,changes=0;
  for(let t=0;t<n;t++){{const pos=t?sig[t-1]:0,turn=Math.abs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
    if(net<=-1||!Number.isFinite(net))throw new RangeError("Invalid net return");
    out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW;
    peak=Math.max(peak,netW);mdd=Math.min(mdd,netW/peak-1);sum+=net;const d=Math.min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost;
    if(turn>1e-12)changes++;if(Math.abs(pos)>1e-12){{active++;if(net>0)wins++;}}
  }}
  const avg=sum/n,ex=avg-rf;let sq=0;for(let t=0;t<n;t++){{const e=out[12+n+t]-avg;sq+=e*e;}}
  const st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),annual=Math.sqrt(ppy);
  const values=[netW-1,grossW-1,buyW-1,Math.pow(netW,ppy/n)-1,st*annual,st>0?ex/st*annual:NaN,dv>0?ex/dv*annual:NaN,mdd,active?wins/active:NaN,changes,turnTotal,costTotal];
  for(let i=0;i<12;i++)out[i]=values[i];return out;
}}
'''
    if lang=='Java':
        return f'''// {note}
public class GeneratedCalculator{{
  public static double[] {fn}(double[] r,double[] sig,double commission,double slippage,double rf,int ppy){{
    if(r==null||sig==null||r.length<3||r.length>100000||sig.length!=r.length||!Double.isFinite(commission)||!Double.isFinite(slippage)||!Double.isFinite(rf)||commission<0||slippage<0||ppy<1||ppy>1000000)throw new IllegalArgumentException("Invalid inputs");
    int n=r.length;for(int t=0;t<n;t++)if(!Double.isFinite(r[t])||r[t]<=-1||!Double.isFinite(sig[t])||Math.abs(sig[t])>1)throw new IllegalArgumentException("Invalid series");
    double[] out=new double[4*n+14];out[12+2*n]=1;out[13+3*n]=1;
    double netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0;int active=0,wins=0,changes=0;
    for(int t=0;t<n;t++){{double pos=t>0?sig[t-1]:0,turn=Math.abs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
      if(net<=-1||!Double.isFinite(net))throw new IllegalArgumentException("Invalid net return");
      out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW;
      peak=Math.max(peak,netW);mdd=Math.min(mdd,netW/peak-1);sum+=net;double d=Math.min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost;
      if(turn>1e-12)changes++;if(Math.abs(pos)>1e-12){{active++;if(net>0)wins++;}}
    }}
    double avg=sum/n,ex=avg-rf,sq=0;for(int t=0;t<n;t++){{double e=out[12+n+t]-avg;sq+=e*e;}}
    double st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),annual=Math.sqrt(ppy);
    double[] values={{netW-1,grossW-1,buyW-1,Math.pow(netW,(double)ppy/n)-1,st*annual,st>0?ex/st*annual:Double.NaN,dv>0?ex/dv*annual:Double.NaN,mdd,active>0?(double)wins/active:Double.NaN,changes,turnTotal,costTotal}};
    System.arraycopy(values,0,out,0,12);return out;
  }}
}}
'''
    if lang=='C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator{{
  public static double[] {fn}(double[] r,double[] sig,double commission,double slippage,double rf,int ppy){{
    if(r==null||sig==null||r.Length<3||r.Length>100000||sig.Length!=r.Length||!double.IsFinite(commission)||!double.IsFinite(slippage)||!double.IsFinite(rf)||commission<0||slippage<0||ppy<1||ppy>1000000)throw new ArgumentException("Invalid inputs");
    int n=r.Length;for(int t=0;t<n;t++)if(!double.IsFinite(r[t])||r[t]<=-1||!double.IsFinite(sig[t])||Math.Abs(sig[t])>1)throw new ArgumentException("Invalid series");
    double[] output=new double[4*n+14];output[12+2*n]=1;output[13+3*n]=1;
    double netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0;int active=0,wins=0,changes=0;
    for(int t=0;t<n;t++){{double pos=t>0?sig[t-1]:0,turn=Math.Abs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
      if(net<=-1||!double.IsFinite(net))throw new ArgumentException("Invalid net return");
      output[12+t]=pos;output[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];output[12+2*n+t+1]=netW;output[13+3*n+t+1]=buyW;
      peak=Math.Max(peak,netW);mdd=Math.Min(mdd,netW/peak-1);sum+=net;double d=Math.Min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost;
      if(turn>1e-12)changes++;if(Math.Abs(pos)>1e-12){{active++;if(net>0)wins++;}}
    }}
    double avg=sum/n,ex=avg-rf,sq=0;for(int t=0;t<n;t++){{double e=output[12+n+t]-avg;sq+=e*e;}}
    double st=Math.Sqrt(sq/(n-1)),dv=Math.Sqrt(down/n),annual=Math.Sqrt(ppy);
    double[] values={{netW-1,grossW-1,buyW-1,Math.Pow(netW,(double)ppy/n)-1,st*annual,st>0?ex/st*annual:double.NaN,dv>0?ex/dv*annual:double.NaN,mdd,active>0?(double)wins/active:double.NaN,changes,turnTotal,costTotal}};
    Array.Copy(values,output,12);return output;
  }}
}}
'''
    if lang=='Swift':
        return f'''// {note}
import Foundation
func {fn}(_ r:[Double],_ sig:[Double],_ commission:Double,_ slippage:Double,_ rf:Double,_ ppy:Int)->[Double]{{
  let n=r.count;if n<3 || n>100000 || sig.count != n || !commission.isFinite || !slippage.isFinite || !rf.isFinite || commission<0 || slippage<0 || ppy<1 || ppy>1000000 {{return []}}
  for t in 0..<n{{if !r[t].isFinite || r[t]<=(-1) || !sig[t].isFinite || abs(sig[t])>1 {{return []}}}}
  var out=[Double](repeating:0,count:4*n+14);out[12+2*n]=1;out[13+3*n]=1
  var netW=1.0,grossW=1.0,buyW=1.0,peak=1.0,mdd=0.0,prev=0.0,turnTotal=0.0,costTotal=0.0,sum=0.0,down=0.0
  var active=0,wins=0,changes=0
  for t in 0..<n{{let pos=t>0 ? sig[t-1] : 0;let turn=abs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost
    if net<=(-1) || !net.isFinite {{return []}}
    out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW
    peak=max(peak,netW);mdd=min(mdd,netW/peak-1);sum+=net;let d=min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost
    if turn>1e-12{{changes+=1}};if abs(pos)>1e-12{{active+=1;if net>0{{wins+=1}}}}
  }}
  let avg=sum/Double(n),ex=avg-rf;var sq=0.0
  for t in 0..<n{{let e=out[12+n+t]-avg;sq+=e*e}}
  let st=sqrt(sq/Double(n-1)),dv=sqrt(down/Double(n)),annual=sqrt(Double(ppy))
  let vals=[netW-1,grossW-1,buyW-1,pow(netW,Double(ppy)/Double(n))-1,st*annual,st>0 ? ex/st*annual : Double.nan,dv>0 ? ex/dv*annual : Double.nan,mdd,active>0 ? Double(wins)/Double(active) : Double.nan,Double(changes),turnTotal,costTotal]
  for i in 0..<12{{out[i]=vals[i]}}
  return out
}}
'''
    if lang=='Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(r:DoubleArray,sig:DoubleArray,commission:Double,slippage:Double,rf:Double,ppy:Int):DoubleArray{{
  val n=r.size;require(n in 3..100000 && sig.size==n && commission.isFinite() && slippage.isFinite() && rf.isFinite() && commission>=0 && slippage>=0 && ppy in 1..1000000)
  for(t in 0 until n)require(r[t].isFinite() && r[t]>(-1) && sig[t].isFinite() && abs(sig[t])<=1)
  val out=DoubleArray(4*n+14);out[12+2*n]=1.0;out[13+3*n]=1.0
  var netW=1.0;var grossW=1.0;var buyW=1.0;var peak=1.0;var mdd=0.0;var prev=0.0;var turnTotal=0.0;var costTotal=0.0;var sum=0.0;var down=0.0
  var active=0;var wins=0;var changes=0
  for(t in 0 until n){{val pos=if(t>0)sig[t-1] else 0.0;val turn=abs(pos-prev);val cost=turn*(commission+slippage)/10000;val gross=pos*r[t];val net=gross-cost
    require(net>(-1) && net.isFinite());out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW
    peak=max(peak,netW);mdd=min(mdd,netW/peak-1);sum+=net;val d=min(net-rf,0.0);down+=d*d;turnTotal+=turn;costTotal+=cost
    if(turn>1e-12)changes++;if(abs(pos)>1e-12){{active++;if(net>0)wins++}}
  }}
  val avg=sum/n;val ex=avg-rf;var sq=0.0;for(t in 0 until n){{val e=out[12+n+t]-avg;sq+=e*e}}
  val st=sqrt(sq/(n-1));val dv=sqrt(down/n);val annual=sqrt(ppy.toDouble())
  val vals=doubleArrayOf(netW-1,grossW-1,buyW-1,netW.pow(ppy.toDouble()/n)-1,st*annual,if(st>0)ex/st*annual else Double.NaN,if(dv>0)ex/dv*annual else Double.NaN,mdd,if(active>0)wins.toDouble()/active else Double.NaN,changes.toDouble(),turnTotal,costTotal)
  for(i in 0 until 12)out[i]=vals[i];return out
}}
'''
    if lang=='Go':
        return f'''// {note}
package main
import "math"
func {fn}(r,sig []float64,commission,slippage,rf float64,ppy int)[]float64{{
  n:=len(r);if n<3||n>100000||len(sig)!=n||math.IsNaN(commission)||math.IsInf(commission,0)||math.IsNaN(slippage)||math.IsInf(slippage,0)||math.IsNaN(rf)||math.IsInf(rf,0)||commission<0||slippage<0||ppy<1||ppy>1000000{{return nil}}
  for t:=0;t<n;t++{{if math.IsNaN(r[t])||math.IsInf(r[t],0)||r[t]<=-1||math.IsNaN(sig[t])||math.IsInf(sig[t],0)||math.Abs(sig[t])>1{{return nil}}}}
  out:=make([]float64,4*n+14);out[12+2*n]=1;out[13+3*n]=1
  netW,grossW,buyW,peak,mdd,prev,turnTotal,costTotal,sum,down:=1.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0
  active,wins,changes:=0,0,0
  for t:=0;t<n;t++{{pos:=0.0;if t>0{{pos=sig[t-1]}};turn:=math.Abs(pos-prev);cost:=turn*(commission+slippage)/10000;gross:=pos*r[t];net:=gross-cost
    if net<=-1||math.IsNaN(net)||math.IsInf(net,0){{return nil}}
    out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW
    peak=math.Max(peak,netW);mdd=math.Min(mdd,netW/peak-1);sum+=net;d:=math.Min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost
    if turn>1e-12{{changes++}};if math.Abs(pos)>1e-12{{active++;if net>0{{wins++}}}}
  }}
  avg:=sum/float64(n);ex:=avg-rf;sq:=0.0;for t:=0;t<n;t++{{e:=out[12+n+t]-avg;sq+=e*e}}
  st:=math.Sqrt(sq/float64(n-1));dv:=math.Sqrt(down/float64(n));annual:=math.Sqrt(float64(ppy));sh,so,wr:=math.NaN(),math.NaN(),math.NaN()
  if st>0{{sh=ex/st*annual}};if dv>0{{so=ex/dv*annual}};if active>0{{wr=float64(wins)/float64(active)}}
  vals:=[]float64{{netW-1,grossW-1,buyW-1,math.Pow(netW,float64(ppy)/float64(n))-1,st*annual,sh,so,mdd,wr,float64(changes),turnTotal,costTotal}}
  copy(out[:12],vals);return out
}}
'''
    if lang=='Rust':
        return f'''// {note}
pub fn {fn}(r:&[f64],sig:&[f64],commission:f64,slippage:f64,rf:f64,ppy:usize)->Vec<f64>{{
  let n=r.len();if n<3||n>100000||sig.len()!=n||!commission.is_finite()||!slippage.is_finite()||!rf.is_finite()||commission<0.0||slippage<0.0||ppy<1||ppy>1000000{{return vec![];}}
  for t in 0..n{{if !r[t].is_finite()||r[t]<=-1.0||!sig[t].is_finite()||sig[t].abs()>1.0{{return vec![];}}}}
  let mut out=vec![0.0;4*n+14];out[12+2*n]=1.0;out[13+3*n]=1.0;
  let (mut net_w,mut gross_w,mut buy_w,mut peak,mut mdd,mut prev,mut turnover,mut cost_total,mut sum,mut down):(f64,f64,f64,f64,f64,f64,f64,f64,f64,f64)=(1.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0);
  let (mut active,mut wins,mut changes)=(0usize,0usize,0usize);
  for t in 0..n{{let pos=if t>0{{sig[t-1]}}else{{0.0}};let turn=(pos-prev).abs();let cost=turn*(commission+slippage)/10000.0;let gross=pos*r[t];let net=gross-cost;
    if net<=-1.0||!net.is_finite(){{return vec![];}}
    out[12+t]=pos;out[12+n+t]=net;prev=pos;net_w*=1.0+net;gross_w*=1.0+gross;buy_w*=1.0+r[t];out[12+2*n+t+1]=net_w;out[13+3*n+t+1]=buy_w;
    peak=peak.max(net_w);mdd=mdd.min(net_w/peak-1.0);sum+=net;let d=(net-rf).min(0.0);down+=d*d;turnover+=turn;cost_total+=cost;
    if turn>1e-12{{changes+=1;}}if pos.abs()>1e-12{{active+=1;if net>0.0{{wins+=1;}}}}
  }}
  let avg=sum/(n as f64);let ex=avg-rf;let mut sq=0.0;for t in 0..n{{let e=out[12+n+t]-avg;sq+=e*e;}}
  let st=(sq/((n-1) as f64)).sqrt();let dv=(down/(n as f64)).sqrt();let annual=(ppy as f64).sqrt();
  let vals=[net_w-1.0,gross_w-1.0,buy_w-1.0,net_w.powf((ppy as f64)/(n as f64))-1.0,st*annual,if st>0.0{{ex/st*annual}}else{{f64::NAN}},if dv>0.0{{ex/dv*annual}}else{{f64::NAN}},mdd,if active>0{{(wins as f64)/(active as f64)}}else{{f64::NAN}},changes as f64,turnover,cost_total];
  out[..12].copy_from_slice(&vals);out
}}
'''
    if lang=='R':
        return f'''# {note}
{fn} <- function(r,sig,commission,slippage,rf,ppy){{
  n<-length(r)
  if(n<3||n>100000||length(sig)!=n||any(!is.finite(r))||any(!is.finite(sig))||any(r<=-1)||any(abs(sig)>1)||any(!is.finite(c(commission,slippage,rf,ppy)))||commission<0||slippage<0||ppy<1||ppy>1000000||ppy!=trunc(ppy))stop("Invalid backtest inputs")
  pos<-c(0,sig[1:(n-1)]);turn<-abs(c(pos[1],diff(pos)));cost<-turn*(commission+slippage)/10000;gross<-pos*r;net<-gross-cost
  if(any(net<=-1)||any(!is.finite(net)))stop("Invalid net returns")
  equity<-cumprod(c(1,1+net));buyhold<-cumprod(c(1,1+r));peak<-cummax(equity);active<-abs(pos)>1e-12;ex<-net-rf;st<-sd(ex);dv<-sqrt(mean(pmin(ex,0)^2))
  metrics<-c(tail(equity,1)-1,prod(1+gross)-1,tail(buyhold,1)-1,tail(equity,1)^(ppy/n)-1,st*sqrt(ppy),if(st>0)mean(ex)/st*sqrt(ppy) else NaN,if(dv>0)mean(ex)/dv*sqrt(ppy) else NaN,min(equity/peak-1),if(any(active))mean(net[active]>0) else NaN,sum(turn>1e-12),sum(turn),sum(cost))
  return(c(metrics,pos,net,equity,buyhold))
}}
'''
    if lang=='MATLAB':
        return f'''% {note}
function result={fn}(r,sig,commission,slippage,rf,ppy)
  r=r(:);sig=sig(:);n=numel(r);
  if n<3||n>100000||numel(sig)~=n||any(~isfinite(r))||any(~isfinite(sig))||any(r<=-1)||any(abs(sig)>1)||any(~isfinite([commission,slippage,rf,ppy]))||commission<0||slippage<0||ppy<1||ppy>1000000||ppy~=fix(ppy)
    error('Invalid backtest inputs');
  end
  pos=[0;sig(1:end-1)];turn=abs([pos(1);diff(pos)]);cost=turn*(commission+slippage)/10000;gross=pos.*r;net=gross-cost;
  if any(net<=-1)||any(~isfinite(net)),error('Invalid net returns');end
  equity=cumprod([1;1+net]);buyhold=cumprod([1;1+r]);peak=cummax(equity);active=abs(pos)>1e-12;ex=net-rf;st=std(ex,0);dv=sqrt(mean(min(ex,0).^2));sh=NaN;so=NaN;wr=NaN;
  if st>0,sh=mean(ex)/st*sqrt(ppy);end
  if dv>0,so=mean(ex)/dv*sqrt(ppy);end
  if any(active),wr=mean(net(active)>0);end
  metrics=[equity(end)-1,prod(1+gross)-1,buyhold(end)-1,equity(end)^(ppy/n)-1,st*sqrt(ppy),sh,so,min(equity./peak-1),wr,sum(turn>1e-12),sum(turn),sum(cost)];
  result=[metrics,pos.',net.',equity.',buyhold.'];
end
'''
    if lang=='Julia':
        return f'''# {note}
using Statistics
function {fn}(r,sig,commission,slippage,rf,ppy)
  n=length(r)
  if n<3||n>100000||length(sig)!=n||!all(isfinite,r)||!all(isfinite,sig)||any(x->x<=-1,r)||any(x->abs(x)>1,sig)||!all(isfinite,(commission,slippage,rf,ppy))||commission<0||slippage<0||ppy<1||ppy>1000000||ppy!=trunc(ppy)
    throw(ArgumentError("Invalid backtest inputs"))
  end
  pos=vcat(0.0,sig[1:end-1]);turn=abs.(vcat(pos[1],diff(pos)));cost=turn.*((commission+slippage)/10000);gross=pos.*r;net=gross.-cost
  if any(x->x<=-1,net)||!all(isfinite,net);throw(ArgumentError("Invalid net return"));end
  eq=cumprod(vcat(1.0,1.0 .+net));bh=cumprod(vcat(1.0,1.0 .+r));peak=accumulate(max,eq);active=abs.(pos).>1e-12;ex=net.-rf;st=std(ex);dv=sqrt(mean(min(x,0)^2 for x in ex))
  metrics=[eq[end]-1,prod(1.0 .+gross)-1,bh[end]-1,eq[end]^(ppy/n)-1,st*sqrt(ppy),st>0 ? mean(ex)/st*sqrt(ppy) : NaN,dv>0 ? mean(ex)/dv*sqrt(ppy) : NaN,minimum(eq./peak.-1),any(active) ? mean(net[active].>0) : NaN,sum(turn.>1e-12),sum(turn),sum(cost)]
  return vcat(metrics,pos,net,eq,bh)
end
'''
    raise ValueError('Unknown language '+lang)
