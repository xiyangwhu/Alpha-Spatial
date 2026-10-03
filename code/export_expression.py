"""Export generated counts within an explicit analysis target set."""
import argparse
import csv
import json
from pathlib import Path
from infer import parse_counts


def load_genes(path):
    value = json.loads(Path(path).read_text())
    genes = value.get('genes') if isinstance(value, dict) else value
    if not isinstance(genes, list) or not genes:
        raise ValueError('Supply a nonempty target-gene list')
    if any(not isinstance(g, str) or not g.strip() for g in genes):
        raise ValueError('Invalid target-gene name')
    if len(set(genes)) != len(genes):
        raise ValueError('Duplicate target gene')
    return genes


def project(record, genes):
    status = record['status']
    if status not in ('valid', 'truncated', 'invalid'):
        raise ValueError('Unrecognized output status')
    if status != 'valid':
        if record.get('predicted_expression') is not None:
            raise ValueError('Failed output must have null expression')
        return [None] * len(genes), {}
    counts = parse_counts(record['raw_text'])
    if record['finish_reason'] != 'stop' or counts is None:
        raise ValueError('Valid status does not match generated output')
    if counts != record['predicted_expression']:
        raise ValueError('Parsed counts differ from raw output')
    targets = set(genes)
    return [counts.get(g, 0) for g in genes], {
        g: value for g, value in counts.items() if g not in targets}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--predictions', required=True)
    p.add_argument('--genes', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    genes = load_genes(args.genes)
    out = Path(args.output)
    if out.exists():
        raise FileExistsError('Use a new output directory')
    rows = [json.loads(s) for s in Path(args.predictions).read_text().splitlines() if s.strip()]
    ids = [r['request_id'] for r in rows]
    if not rows or len(set(ids)) != len(ids):
        raise ValueError('Empty input or duplicate request IDs')
    projected = [project(r, genes) for r in rows]
    out.mkdir(parents=True)
    with (out / 'expression.csv').open('x', newline='') as f:
        w = csv.writer(f)
        w.writerow(['request_id', 'status', *genes])
        for r, (values, _) in zip(rows, projected):
            w.writerow([r['request_id'], r['status'], *['NA' if x is None else x for x in values]])
    with (out / 'out_of_target.csv').open('x', newline='') as f:
        w = csv.writer(f)
        w.writerow(['request_id', 'gene', 'predicted_count'])
        for r, (_, extras) in zip(rows, projected):
            for g, value in extras.items():
                w.writerow([r['request_id'], g, value])
    summary = dict(requests=len(rows), target_genes=len(genes),
                   valid_rows=sum(r['status'] == 'valid' for r in rows),
                   missing_rows=sum(r['status'] != 'valid' for r in rows),
                   out_of_target_entries=sum(len(x[1]) for x in projected),
                   valid_omitted_target_value=0, failed_response_value='NA',
                   normalization='none', export_completed=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
