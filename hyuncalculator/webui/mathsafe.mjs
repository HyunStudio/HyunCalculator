// Small arithmetic parser for the offline mobile scientific calculator. No eval.
export function evaluate(expression,degrees=false){
 const source=expression.replaceAll('×','*').replaceAll('÷','/').replaceAll('π','pi').replaceAll('−','-');
 if(source.length>2000)throw Error('수식이 너무 깁니다.');
 const tokens=[];const pattern=/\s*(?:(\d*\.?\d+(?:[eE][+-]?\d+)?)|([A-Za-z_]+)|(\*\*|[+\-*/^(),!%]))/gy;
 let pos=0;while(pos<source.length){pattern.lastIndex=pos;const m=pattern.exec(source);if(!m){if(!source.slice(pos).trim())break;throw Error('지원하지 않는 문자가 있습니다.');}tokens.push(m[1]!==undefined?Number(m[1]):m[2]||m[3]);pos=pattern.lastIndex;}
 let at=0,depth=0;
 const factorial=x=>{if(!Number.isInteger(x)||x<0||x>170)throw Error('팩토리얼은 0~170의 정수만 입력하세요.');let r=1;for(let i=2;i<=x;i++)r*=i;return r;};
 const angle=x=>degrees?x*Math.PI/180:x;
 const inverse=x=>degrees?x*180/Math.PI:x;
 const functions={sin:x=>Math.sin(angle(x)),cos:x=>Math.cos(angle(x)),tan:x=>Math.tan(angle(x)),asin:x=>inverse(Math.asin(x)),acos:x=>inverse(Math.acos(x)),atan:x=>inverse(Math.atan(x)),sqrt:Math.sqrt,abs:Math.abs,ln:Math.log,log:Math.log10,log2:Math.log2,exp:Math.exp,pow:Math.pow,root:(x,n)=>x<0&&n%2===1?-Math.pow(-x,1/n):Math.pow(x,1/n),factorial,comb:(n,k)=>{if(!Number.isInteger(n)||!Number.isInteger(k)||k<0||n<k||n>170)throw Error('Invalid combination');return factorial(n)/factorial(k)/factorial(n-k);},perm:(n,k)=>factorial(n)/factorial(n-k)};
 function parse(min=0){
  if(++depth>100)throw Error('수식 중첩이 너무 깊습니다.');
  let token=tokens[at++],left;
  if(typeof token==='number')left=token;
  else if(token==='+'||token==='-')left=(token==='-'?-1:1)*parse(25);
  else if(token==='('){left=parse();if(tokens[at++]!==')')throw Error('괄호를 확인하세요.');}
  else if(token==='pi'||token==='e')left=token==='pi'?Math.PI:Math.E;
  else if(Object.hasOwn(functions,token)){
   if(tokens[at++]!=='(')throw Error('함수 뒤에 괄호를 넣어 주세요.');const args=[parse()];while(tokens[at]===','){at++;args.push(parse());}if(tokens[at++]!==')')throw Error('함수 괄호를 확인하세요.');left=functions[token](...args);
  }else throw Error('올바른 수식을 입력하세요.');
  while(at<tokens.length){const op=tokens[at];if(op==='!'){at++;left=factorial(left);continue;}if(op==='%'){at++;left/=100;continue;}
   const prec=({'+':10,'-':10,'*':20,'/':20,'^':30,'**':30})[op];if(prec===undefined||prec<min)break;at++;const right=parse(prec+(op==='^'||op==='**'?0:1));left=op==='+'?left+right:op==='-'?left-right:op==='*'?left*right:op==='/'?left/right:Math.pow(left,right);
  }depth--;return left;
 }
 const result=parse();if(at!==tokens.length||!Number.isFinite(result))throw Error('실수 범위에서 계산할 수 없는 수식입니다.');return result;
}
