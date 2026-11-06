// HyunCalculator STAT-002: sample covariance (ddof=1), correlation. Input rows=observations, columns=assets; output flat row-major [cov(n*n), corr(n*n)], NaN correlation for zero variance.
export function cov(data) {
  if(!Array.isArray(data)||data.length<3||data.length>100000)throw new RangeError("Invalid row count");
  const rows=data.length,cols=data[0]?.length;
  if(!Number.isInteger(cols)||cols<2||cols>128)throw new RangeError("Invalid columns");
  const avg=Array(cols).fill(0),result=Array(2*cols*cols).fill(0);
  for(let i=0;i<rows;i++){if(!Array.isArray(data[i])||data[i].length!==cols||!data[i].every(Number.isFinite))throw new RangeError("Invalid row");for(let j=0;j<cols;j++)avg[j]+=data[i][j]/rows;}
  for(let j=0;j<cols;j++)for(let k=0;k<cols;k++){let sum=0;for(let i=0;i<rows;i++)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1);}
  for(let j=0;j<cols;j++)for(let k=0;k<cols;k++){const d=Math.sqrt(result[j*cols+j])*Math.sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=d>0?result[j*cols+k]/d:NaN;}
  return result;
}
