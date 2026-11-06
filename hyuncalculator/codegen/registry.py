"""Stable catalog of the 33 Financial/Quant operations in v1.1.0.

The registry intentionally distinguishes registered formulas from implemented
code emitters; appearing in the catalog is NOT a claim of export support.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..operations import GROUPS

# The mapping is an implementation contract, not based on UI order.
DOMAINS = {
    'Financial': ('financial', ('fin_fv','fin_pv','fin_pmt','fin_npv','fin_irr','fin_loan',
                              'fin_cagr','fin_effective','fin_annuity')),
    'Statistics': ('statistics', ('qf_normal','qf_cov')),
    'Portfolio': ('portfolio', ('qf_portfolio',)),
    'Allocation': ('allocation', ('qf_gmv','qf_target','qf_bl')),
    'Derivatives': ('derivatives', ('qf_bs','qf_iv','qf_mc')),
    'Bonds': ('bonds', ('qf_bond','qf_ytm')),
    'Risk': ('risk', ('qf_hist_var','qf_normal_var','qf_performance')),
    'Time Series': ('timeseries', ('qf_ewma','qf_garch','qf_moving')),
    'Stochastic Processes': ('stochastic', ('qf_gbm','qf_ou','qf_brownian',
                                         'qf_gbm_paths','qf_ou_paths')),
    'Quant Strategies': ('strategy', ('qf_cost','qf_backtest')),
}
PREFIX = {'Financial':'FIN','Statistics':'STAT','Portfolio':'PORT','Allocation':'ALLOC',
          'Derivatives':'DERIV','Bonds':'BOND','Risk':'RISK','Time Series':'TS',
          'Stochastic Processes':'STOCH','Quant Strategies':'STRAT'}

@dataclass(frozen=True)
class Formula:
    id: str
    domain: str
    function: str
    title_ko: str
    title_en: str
    formula: str
    fields: tuple[tuple[str,str],...]
    exportable: bool
    supported_languages: tuple[str,...]

# Supported profiles only for complete scalar/NPV function semantics. Others
# remain discoverable but cannot silently generate incomplete code.
MULTILANG = frozenset(('fin_fv','fin_pv','fin_pmt','fin_npv',
                        'fin_cagr','fin_effective','fin_annuity',
                        'qf_garch','qf_gbm','qf_ou','qf_cost',
                        'qf_gmv','qf_target','qf_bond','qf_ewma','qf_ytm','qf_hist_var','qf_moving','qf_portfolio','qf_bs','qf_iv','qf_normal_var'))
# The full catalog is exportable as standalone Python. Only a subset has
# audited emitters for the other 13 languages; never conflate the two.
EXPORTABLE = frozenset(name for _label, (_domain, names) in DOMAINS.items() for name in names)


def catalog() -> tuple[Formula,...]:
    by_name = {o.compute.__name__: o for group in ('Financial','Quant') for o in GROUPS[group]}
    result = []
    for domain, (_, names) in DOMAINS.items():
        for i, name in enumerate(names,1):
            operation = by_name[name]
            from ..legacy_ml import EN_OPERATIONS
            en = EN_OPERATIONS[name]
            result.append(Formula(f'{PREFIX[domain]}-{i:03d}',domain,name,
                                  operation.title,en[0],operation.formula,
                                  tuple((f.key, f.example) for f in operation.fields),
                                  name in EXPORTABLE,
                                  (('Python',) if name not in MULTILANG else
                                   ('Python','R','C','C++','JavaScript','TypeScript','Java',
                                    'C#','Swift','Kotlin','Go','Rust','MATLAB','Julia'))))
    assert len(result)==33 and set(by_name)=={r.function for r in result}, 'Registry drift: review v1.1.0 operation changes'
    return tuple(result)


def get_formula(formula_id: str) -> Formula | None:
    return next((f for f in catalog() if f.id==formula_id), None)
