// HyunCalculator FIN-006: [payment, interest, principal paid, remaining balance]. Rate is per installment.
export function loan(principal, rate, n, period) {
  if (![principal,rate,n,period].every(Number.isFinite)||principal<0||rate<=-1||!Number.isInteger(n)||n<1||!Number.isInteger(period)||period<1||period>n) throw new RangeError("Invalid loan inputs");
  let payment,interest,paid,balance;
  if(Math.abs(rate)<1e-14){payment=principal/n;interest=0;paid=payment;balance=Math.max(0,principal-payment*period);}
  else {
    payment=principal*rate/(1-Math.pow(1+rate,-n));
    const factor=Math.pow(1+rate,period-1);
    const prev=principal*factor-payment*(factor-1)/rate;
    interest=prev*rate;paid=payment-interest;balance=Math.max(0,prev-paid);
  }
  return [payment,interest,paid,balance];
}
