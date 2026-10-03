"""Emit completion only after inference and statistical checks pass."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--results',required=True);a=p.parse_args()
r=Path(a.results)
i=json.loads((r/'inference_check.json').read_text())
s=json.loads((r/'response_statistics/verification.json').read_text())
e=json.loads((r/'expression/summary.json').read_text())
if i['format_test']!='PASS' or s['reference_check']!='PASS' or not e['export_completed']:
    raise RuntimeError('A required step did not complete successfully')
with (r/'run_summary.json').open('x') as f:
    json.dump(dict(execution='completed',inference_format=i['format_test'],
        patient_statistics=s['reference_check'],inference_requests=i['requests'],patients=s['patients'],
        exact_archived_dictionary_matches=i['exact_archived_dictionary_matches'],
        archived_count_identity=('identical' if i['exact_archived_dictionary_matches']==i['requests'] else 'different'),
        target_genes=e['target_genes'],
        scope='Small-image inference and frozen-state patient response statistics; not full-paper reproduction.'),f,indent=2)
print('Completed inference demonstration, expression export and patient statistics. See run_summary.json for separate checks.')
