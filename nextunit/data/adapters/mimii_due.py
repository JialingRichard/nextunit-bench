"""MIMII DUE, sections 00-02 of the five development packages (raw: MIMII_DUE/<machine>/{train,test}/*.wav, the
official Zenodo 4740355 archives dev_data_<machine>.zip extracted side by side).

Release fix (KNOWN_ISSUES C1): wav files are copied, not linked, in record-ID order, and every file gets the
same modification time, so neither inode order nor timestamps carry the label."""
import json
import os
import re
import shutil
from pathlib import Path

import pandas as pd

from ._hashid import rid

RAW_DIRS = ('MIMII_DUE',)
FIXED_MTIME = 1767225600   # 2026-01-01T00:00:00Z
MACHINES = ['fan', 'gearbox', 'pump', 'slider', 'valve']
NAMES = dict(zip(MACHINES, ['风机', '齿轮箱', '泵', '滑轨', '阀门']))
DOMAIN_FACTS = {
    'fan': [('风量变化', -9, -9), ('同厂商两台不同尺寸产品', -12, -12), ('混入不同工厂背景噪声', -9, -9)],
    'gearbox': [('驱动电压变化', -15, -15), ('曲柄臂长变化', -15, -15), ('提升负重变化', -15, -15)],
    'pump': [('潜水泵流体黏度变化', -9, -9), ('背景信噪比变化', -12, -18), ('目标域多台泵同时运行', -9, -9)],
    'slider': [('滚珠丝杠运动速度变化', -12, -12), ('滚珠丝杠运动程序变化', -12, -12), ('传动带材料变化', -10, -10)],
    'valve': [('开闭时序变化', -9, -12), ('源域没有泵运行', -9, -12), ('目标域两个阀同时运行', -12, -10)],
}
PATTERN = re.compile(r'section_(\d+)_(source|target)_(train|test)_(normal|anomaly)_.*\.wav$')


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(raw: Path, out: Path) -> None:
    source = raw / 'MIMII_DUE'
    groups = {}
    for machine in MACHINES:
        for path in sorted((source / machine).rglob('*.wav')):
            match = PATTERN.fullmatch(path.name)
            assert match, path.name
            section, domain, partition, state = match.groups()
            if int(section) > 2:
                continue  # evaluation-package training data: no published test in this release
            groups.setdefault((machine, section, partition, domain if partition == 'test' else 'mixed'), []).append(
                (path, domain, int(state == 'anomaly')))
    assert {key[0] for key in groups} == set(MACHINES)
    for (machine, section, partition, score_domain), files in sorted(groups.items()):
        unit = out / f'{partition}_{machine}_{section}_{score_domain}'
        (unit / 'inputs/signal').mkdir(parents=True)
        rows, labels = [], []
        for path, domain, label in sorted(files, key=lambda item: rid(str(item[0].relative_to(source)))):
            record = rid(str(path.relative_to(source)))
            relative = f'signal/{record}.wav'
            shutil.copyfile(path, unit / 'inputs' / relative)
            description, source_snr, target_snr = DOMAIN_FACTS[machine][int(section)]
            rows.append({'record_id': record, 'signal_file': relative, 'machine_type': NAMES[machine],
                         'product_group': rid(f'{machine}:{section}'), 'domain': domain,
                         'domain_difference': description, 'background_snr_db': source_snr if domain == 'source' else target_snr,
                         'operating_attributes': '_'.join(path.stem.split('_')[6:]) if partition == 'train' else ''})
            labels.append((record, label))
        assert {label for _, label in labels} == ({0} if partition == 'train' else {0, 1})
        _json(unit / 'inputs/records.json', rows)
        pd.DataFrame(labels, columns=['record_id', 'target']).to_csv(unit / 'labels.csv', index=False)
    for path in sorted(out.rglob('*')):
        os.utime(path, (FIXED_MTIME, FIXED_MTIME), follow_symlinks=False)
