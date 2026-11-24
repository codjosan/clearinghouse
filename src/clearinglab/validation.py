"""Acceptance requirements. Reference checks are starter tests, not proof of completion."""
from math import isfinite

REQUIRED_INTERFACE=('evaluate','pretrade','liquidate','reconcile')

def validate_report(report):
    issues=[]
    for name in ('equity','initial_margin','maintenance_margin','excess_equity','worst_loss','gross_notional'):
        value=getattr(report,name,None)
        if not isinstance(value,(int,float)) or not isfinite(value):issues.append(name+': nonfinite')
    if not issues:
        if report.initial_margin<0 or report.maintenance_margin<0:issues.append('negative margin')
        if report.maintenance_margin>report.initial_margin:issues.append('maintenance > initial')
        if abs(report.excess_equity-(report.equity-report.initial_margin))>1e-5:issues.append('excess mismatch')
    return issues

def require_methods(cls):
    return [m for m in REQUIRED_INTERFACE if not callable(getattr(cls,m,None))]
