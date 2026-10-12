"""Export the pinned C-Eval computer-network subject for OpenCompass."""

import csv
from pathlib import Path

from datasets import load_dataset


DATASET = 'ceval/ceval-exam'
REVISION = '617524a00b307ff6f9933702f724131fe12ca7ce'
SUBJECT = 'computer_network'
COLUMNS = ['id', 'question', 'A', 'B', 'C', 'D', 'answer', 'explanation']
EXPECTED_COUNTS = {'dev': 5, 'val': 19, 'test': 171}
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'day19_ceval_opencompass'


def main() -> None:
    for split, expected in EXPECTED_COUNTS.items():
        rows = load_dataset(DATASET, SUBJECT, split=split, revision=REVISION)
        if len(rows) != expected:
            raise ValueError(f'{split}: expected {expected} rows, got {len(rows)}')
        destination = OUT / split / f'{SUBJECT}_{split}.csv'
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, '') for key in COLUMNS})
        print(f'{split}: {len(rows)} rows -> {destination}')


if __name__ == '__main__':
    main()
