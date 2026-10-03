"""Validate all request IDs and describe differences from archived model output."""
import argparse
import json
from pathlib import Path
from infer import parse_counts


def read(path):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    assert len({r['request_id'] for r in rows})==len(rows), 'Duplicate request ID'
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True);p.add_argument('--predictions',required=True)
    p.add_argument('--output',required=True);a=p.parse_args();data=Path(a.data)
    req=read(data/'requests.jsonl');pred=read(a.predictions)
    old={r['request_id']:r for r in read(data/'reference/archived_predictions.jsonl')}
    assert [r['request_id'] for r in req]==[r['request_id'] for r in pred]
    assert set(old)=={r['request_id'] for r in pred}
    counts={s:0 for s in ['valid','truncated','invalid']};equal=0;deltas=[]
    for r in pred:
        assert r['status'] in counts;counts[r['status']]+=1
        parsed=parse_counts(r['raw_text'])
        if r['status']=='valid':
            assert r['finish_reason']=='stop' and parsed==r['predicted_expression']
            prev=old[r['request_id']]
            if prev['finish_reason']=='stop' and prev['strict_json']:
                base=prev['predicted_expression'];equal+=int(parsed==base)
                keys=set(parsed)|set(base)
                deltas.append({'request_id':r['request_id'],
                    'union_emitted_genes':len(keys),
                    'sum_absolute_count_difference':sum(abs(parsed.get(k,0)-base.get(k,0)) for k in keys)})
        else:
            assert r['predicted_expression'] is None
    report=dict(requests=len(req),status_counts=counts,exact_archived_dictionary_matches=equal,
        archived_comparison=deltas,all_ids_accounted_for=True,
        note='Archived outputs are model predictions, not ground truth. Missing keys interpreted only over the union of emitted genes for this diagnostic.',
        format_test='PASS' if counts['valid']==len(req) else 'FAIL')
    with Path(a.output).open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='archived_comparison'}))
    if report['format_test']!='PASS':raise SystemExit(2)


if __name__=='__main__':main()
