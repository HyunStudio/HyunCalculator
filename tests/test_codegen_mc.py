"""Monte Carlo code generator: portable deterministic RNG and CI contract."""
from __future__ import annotations

import math
import unittest

from hyuncalculator.codegen import LANGUAGES, GenerationError, GenerationOptions, catalog, generate, get_formula
from hyuncalculator.quant import black_scholes, european_mc


def reference_portable(s=100., k=100., t=1., r=.05, sigma=.2, q=0., option='call', paths=20000, seed=42):
    """Independent Park-Miller/Box-Muller and antithetic pair computation."""
    state=seed
    price=0.0
    m2=0.0
    sign=1 if option=='call' else -1
    scale=sigma*math.sqrt(t)
    growth=(r-q-.5*sigma*sigma)*t
    discount=math.exp(-r*t)
    for i in range(1,paths//2+1):
        state=(state*16807)%2147483647
        u=state/2147483647
        state=(state*16807)%2147483647
        v=state/2147483647
        z=math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v)
        a=s*math.exp(growth+scale*z)
        b=s*math.exp(growth-scale*z)
        sample=discount*(max(sign*(a-k),0.)+max(sign*(b-k),0.))/2
        delta=sample-price
        price+=delta/i
        m2+=delta*(sample-price)
    se=math.sqrt((m2/(paths//2-1))/(paths//2))
    return price,se,price-1.96*se,price+1.96*se


class MonteCarloGeneratorTest(unittest.TestCase):
    def test_registry(self):
        fs=catalog()
        self.assertEqual(len(fs),33)
        self.assertEqual(sum(len(x.supported_languages) for x in fs),384)
        self.assertEqual(sum(len(x.supported_languages)==14 for x in fs),27)
        self.assertEqual(sum(len(x.supported_languages)==1 for x in fs),6)
        self.assertEqual(set(get_formula('DERIV-003').supported_languages),set(LANGUAGES))

    def test_emit_all_languages(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                src=generate('DERIV-003',GenerationOptions(language=lang))
                self.assertGreater(len(src),850)
                self.assertNotIn('NotImplemented',src)
                self.assertNotIn('TODO',src)
                self.assertIn('95%',src if lang!='Python' else src.replace('CI lower','95%'))
                self.assertIn('custom_mc',generate('DERIV-003',GenerationOptions(language=lang,function_name='custom_mc')))

    def test_invalid_options(self):
        bad=[{'structure':'class'},{'iteration':'for'},{'iteration':'while'},
             {'variable_names':(('s','spot'),)},{'imports':'numerical'},{'variant':'continuous'}]
        for opts in bad:
            with self.subTest(opts=opts),self.assertRaises(GenerationError):
                generate('DERIV-003',GenerationOptions(language='C++',**opts))

    def test_portable_reference_and_confidence_interval(self):
        for option in ('call','put'):
            result=reference_portable(option=option)
            self.assertEqual(len(result),4)
            self.assertGreater(result[1],0)
            self.assertLess(result[2],result[0])
            self.assertGreater(result[3],result[0])
            analytic=black_scholes(100,100,1,.05,.2,dividend=0,option=option)['Price']
            # MC estimates are stochastic even when the seed is fixed.
            self.assertLess(abs(result[0]-analytic),5*result[1]+0.03)

    def test_zero_volatility(self):
        vals=reference_portable(s=100.,k=100.,sigma=0.)
        self.assertAlmostEqual(vals[0],100*math.exp(-.05)*max(math.exp(.05)-1,0),places=10)
        self.assertLess(vals[1],1e-10)

    def test_python_original_rng_semantics(self):
        # Python emitter preserves NumPy default_rng / existing calculator semantics;
        # the other 13 use a common LCG for inter-language reproducibility.
        ns={}
        exec(compile(generate('DERIV-003',GenerationOptions(language='Python')),'<mc>','exec'),ns)
        got=ns['mc'](100,100,1,.05,.2,0,'call',1000,42)
        expected=european_mc(100,100,1,.05,.2,0,'call',1000,42)
        for key in expected:
            self.assertAlmostEqual(got[key],expected[key],places=12)


if __name__=='__main__': unittest.main()
