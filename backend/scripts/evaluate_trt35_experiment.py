"""Compare captured OCR with an AI visual draft, not human-approved Golden."""
import argparse
import json
from pathlib import Path


def evaluate(cells, draft, threshold):
    expected = {(r[0], b): raw for r in draft['rows'] for b, raw in zip(draft['boom_lengths_m'], r[1:])}
    counts = dict(correct_available=0, wrong_numeric=0, false_available=0,
                  correct_not_available=0, false_not_available=0, unresolved=0)
    import re
    for cell in cells:
        key = (cell['radius_m'], cell['boom_length_m'])
        raw = cell['source_text'] or ''
        truth = expected[key]
        if (cell['confidence'] or 0) < threshold or not re.fullmatch(r'(?:[0-9]+\.[0-9]{2}|-)', raw):
            counts['unresolved'] += 1
        elif raw == '-':
            counts['correct_not_available' if truth == '-' else 'false_not_available'] += 1
        elif truth == '-':
            counts['false_available'] += 1
        elif float(raw) != float(truth):
            counts['wrong_numeric'] += 1
        else:
            counts['correct_available'] += 1
    return counts


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('captures', nargs='+', type=Path)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    draft = json.loads((Path(__file__).resolve().parents[1] / 'evaluation/datasets/trt35_page11_100_visual_draft.json').read_text())
    report = {'reference_status': draft['verification_status'], 'profile': 'ONBOARDING_REQUIRED',
              'association_validation': 'NOT_INDEPENDENTLY_VERIFIED', 'runs': {}}
    for capture in args.captures:
        for name, run in json.loads(capture.read_text()).items():
            result = run['result']
            if result['file_hash_sha256'] != draft['source_sha256'] or len(result['cells']) != 135:
                raise ValueError('wrong source revision or incomplete cell capture')
            report['runs'][name] = {'seconds':run['seconds'], 'thresholds': {str(t): evaluate(result['cells'], draft, t) for t in [.70,.75,.80,.85,.90,.95]}}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for name,run in report['runs'].items():
        print(name, run['thresholds']['0.85'])


if __name__ == '__main__':
    main()
