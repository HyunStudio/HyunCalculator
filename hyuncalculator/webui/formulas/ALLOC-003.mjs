// Black-Litterman: [prior(n), posterior(n), predictive_cov(n*n row-major)]; market sums to 1, cov SPD, omega strictly positive; 2<=n<=128, 1<=m<=128.
function bl(cov,market,delta,tau,p,q,omega) {
  const finite=(x)=>Number.isFinite(x);
  const n=cov.length,m=p.length;
  if(n<2||n>128||m<1||m>128||market.length!==n||q.length!==m||omega.length!==m||
     !finite(delta)||!finite(tau)||delta<=0||tau<=0||
     !market.every(finite)||Math.abs(market.reduce((a,b)=>a+b,0)-1)>1.00001e-5||
     !q.every(finite)||!omega.every(x=>finite(x)&&x>0)||
     !cov.every(row=>row.length===n&&row.every(finite))||!p.every(row=>row.length===n&&row.every(finite)))throw new RangeError('Invalid dimensions/inputs');
  const chol=(a)=>{
    const size=a.length,l=Array.from({length:size},()=>Array(size).fill(0));
    for(let i=0;i<size;i++){
      for(let j=0;j<size;j++)if(!finite(a[i][j])||Math.abs(a[i][j]-a[j][i])>1e-9+1e-5*Math.abs(a[j][i]))throw new RangeError('Asymmetric matrix');
      for(let j=0;j<=i;j++){let v=a[i][j];for(let k=0;k<j;k++)v-=l[i][k]*l[j][k];
        if(i===j){if(!(v>1e-12))throw new RangeError('Not SPD');l[i][j]=Math.sqrt(v);}
        else l[i][j]=v/l[j][j];
      }
    }return l;
  };
  const solve=(a,rhs)=>{
    const l=chol(a),v=rhs.slice(),size=v.length;
    for(let i=0;i<size;i++){for(let j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}
    for(let i=size-1;i>=0;i--){for(let j=i+1;j<size;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}return v;
  };
  chol(cov);
  const prior=cov.map(row=>delta*row.reduce((s,v,j)=>s+v*market[j],0));
  const b=Array.from({length:n},(_,i)=>Array.from({length:m},(_,k)=>tau*cov[i].reduce((s,v,j)=>s+v*p[k][j],0)));
  const a=Array.from({length:m},(_,k)=>Array.from({length:m},(_,h)=>p[k].reduce((s,v,j)=>s+v*b[j][h],0)+(k===h?omega[k]:0)));
  const residual=q.map((v,k)=>v-p[k].reduce((s,x,j)=>s+x*prior[j],0));
  const shift=solve(a,residual);
  const posterior=prior.map((v,i)=>v+b[i].reduce((s,x,k)=>s+x*shift[k],0));
  const predictive=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>{
    const z=solve(a,b[j]);return (1+tau)*cov[i][j]-b[i].reduce((s,x,k)=>s+x*z[k],0);
  }));
  return [...prior,...posterior,...predictive.flat()];
}
