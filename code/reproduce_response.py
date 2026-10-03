"""Recalculate four-state patient-level response comparisons from frozen bin counts.

Reproduces Figure 8e / Supplementary Figure 5a statistics, not atlas construction.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats


def calculate(source):
    d = pd.read_csv(source)
    assert not d.duplicated(['patient', 'state']).any()
    assert set(d.state) == {0, 1, 2, 3}
    assert d.patient.nunique() == 81 and len(d) == 324
    assert d.groupby('patient').state.nunique().eq(4).all()
    assert d.groupby('patient').nonresponse.nunique().eq(1).all()
    assert set(d.nonresponse) == {0, 1}
    assert np.isfinite(d.spot_count).all() and (d.spot_count >= 0).all()
    assert np.equal(d.spot_count, np.floor(d.spot_count)).all()
    total = d.groupby('patient').spot_count.transform('sum')
    assert (total > 0).all() and d.spot_count.sum() == 211270
    d['burden'] = d.spot_count / total
    assert np.allclose(d.burden, d.within_subset_spatial_fraction, rtol=0, atol=1e-12)
    rows = []
    for state, group in d.groupby('state', sort=True):
        nr = group.loc[group.nonresponse == 1, 'burden'].to_numpy()
        re = group.loc[group.nonresponse == 0, 'burden'].to_numpy()
        assert len(nr) == 48 and len(re) == 33
        v1, v0 = nr.var(ddof=1)/len(nr), re.var(ddof=1)/len(re)
        se = np.sqrt(v1+v0)
        df = (v1+v0)**2/(v1*v1/(len(nr)-1)+v0*v0/(len(re)-1))
        delta = nr.mean()-re.mean()
        test = stats.ttest_ind(nr, re, equal_var=False, alternative='two-sided')
        h = stats.t.ppf(.975, df)*se
        rows.append(dict(state=int(state), n_responder=len(re), n_nonresponder=len(nr),
            mean_responder=float(re.mean()), mean_nonresponder=float(nr.mean()),
            effect_NR_minus_R=float(delta), CI95_low=float(delta-h), CI95_high=float(delta+h),
            t=float(test.statistic), df=float(df), p=float(test.pvalue)))
    result = pd.DataFrame(rows)
    result['q_BH_states'] = stats.false_discovery_control(result.p.to_numpy(), method='bh')
    return d, result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();source=Path(a.data);out=Path(a.output)
    assert not out.exists(), 'Use a new output directory'
    d, result=calculate(source/'patient_state_source.csv')
    ref=pd.read_csv(source/'reference_response.csv').set_index('state')
    fields=['n_responder','n_nonresponder','effect_NR_minus_R','CI95_low','CI95_high','p','q_BH_states']
    delta=np.abs(result.set_index('state')[fields].to_numpy()-ref.loc[range(4),fields].to_numpy())
    assert np.all(delta < 1e-10), 'Statistics differ from archived reference'
    out.mkdir(parents=True)
    result.to_csv(out/'four_state_response.csv',index=False)
    d[['patient','state','spot_count','nonresponse','burden']].to_csv(out/'patient_burden.csv',index=False)
    report=dict(patients=81,responders=33,nonresponders=48,states=4,parent_bins=211270,
                test='Two-sided Welch t; BH correction across four states',
                start_point='Frozen state-bin counts per patient, not reconstructed expression or clustering',
                max_absolute_reference_difference=float(delta.max()),reference_check='PASS',
                tolerance_absolute=1e-10)
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
