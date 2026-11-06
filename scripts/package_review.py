#!/usr/bin/env python3
"""Package full and compact reviewed snapshots without changing frozen inputs."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'MIFlu_Reviewed_Project'


def include_file(path):
    rel = path.relative_to(ROOT)
    return not (set(rel.parts) & {'.git', '__pycache__', '.pytest_cache'}
                or path.suffix in {'.pyc', '.pyo'}
                or path.name.startswith('~$'))


def compact(path):
    rel = path.relative_to(ROOT)
    top = rel.parts[0]
    if len(rel.parts) == 1:
        return path.suffix in {'.md', '.txt', '.cff', '.pdf'} or path.name == 'LICENSE'
    if top == 'source_snapshots':
        return True
    if top == 'handoffs':
        return 'RAW_EVIDENCE' not in rel.parts
    if top in {'audit', 'presentation', '02_数字表格', '06_原始数据集',
               'scripts', 'tests', 'tests_archive', '05_程序代码'}:
        return True
    if top == '01_最终报告':
        if len(rel.parts) == 2:
            return (path.stem.startswith(('report_internal_', 'progress_report_',
                                          'ieee_manuscript_', 'record_for_journal_'))
                    or path.suffix == '.md')
        if rel.parts[1] == 'figures':
            return True
        if rel.parts[1] == '_build2':
            return (path.suffix == '.py'
                    and 'context' not in rel.parts)
    return False


def package(out):
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and include_file(p))
    frozen = json.loads((ROOT / 'audit/INPUT_SHA256.json').read_text())
    for rel, digest in frozen.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel
    rows = []
    for kind in ('Full_Project', 'Review_Deliverables'):
        selected = files if kind == 'Full_Project' else [p for p in files if compact(p)]
        dest = out / f'MIFlu_Reviewed_{kind}_20261105.zip'
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as archive:
            for p in selected:
                archive.write(p, PREFIX + '/' + p.relative_to(ROOT).as_posix())
            if kind == 'Review_Deliverables':
                archive.writestr(PREFIX + '/COMPACT_BUNDLE.md',
                    '# Compact bundle\n\n'
                    'This contains the current eight DOCX/PDF report pairs, all audits, '
                    'deck and notes, figures, frozen CSVs, source datasets, '
                    'tests_archive and relevant rebuild code. Raw predictions, '
                    'most historical notes and hpc_experiments are excluded. '
                    'Use the full project for the --raw-smoke command. '
                    'The CSV-only audit command is python scripts/verify_snapshot.py. '
                    'The seven new CPU audit tests can run independently of '
                    'the archived model suite.\n')
        with zipfile.ZipFile(dest) as archive:
            bad = archive.testzip()
            assert bad is None, bad
            members = archive.namelist()
            assert all(PREFIX + '/01_最终报告/' + name + suffix in members
                       for name in ['report_internal_en', 'report_internal_zh',
                                    'progress_report_en', 'progress_report_zh',
                                    'ieee_manuscript_en', 'ieee_manuscript_zh',
                                    'record_for_journal_en','record_for_journal_zh']
                       for suffix in ['.docx', '.pdf'])
            assert PREFIX + '/tests_archive/test_miflu_ablations.py' in members
            assert PREFIX + '/presentation/Week12_Progress_Presentation.pptx' in members
            assert archive.read(PREFIX+'/presentation/source/Week12_User_Corrected.pptx') == (ROOT/'presentation/source/Week12_User_Corrected.pptx').read_bytes()
            assert PREFIX+'/source_snapshots/v6/report_internal_en.docx' in members
            assert PREFIX+'/RESULT_UPDATE_POLICY.md' in members
        row = dict(filename=dest.name, bytes=dest.stat().st_size,
                   sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                   entries=len(members), crc_checked=True,
                   input_bytes=sum(p.stat().st_size for p in selected),
                   source_files_by_top=dict(Counter(p.relative_to(ROOT).parts[0]
                                                     for p in selected)))
        rows.append(row)
        print(json.dumps(row), flush=True)
    (out / 'DELIVERY_MANIFEST.json').write_text(
        json.dumps({'archives': rows, 'source_csv_hashes_preserved': True,
                    'review_date': '2026-11-05 HKT',
                    'snapshot_experimental_status': '2026-11-03',
                    'revision': 8, 'internal_questions_per_language': 25, 'paper_backed_questions_per_language':25,
                    'owner_master_sha256': hashlib.sha256((ROOT/'presentation/source/Week12_User_Corrected.pptx').read_bytes()).hexdigest(),
                    'current_pptx_sha256': hashlib.sha256((ROOT/'presentation/Week12_Progress_Presentation.pptx').read_bytes()).hexdigest(),
                    'scientific_snapshot':'historical audited results unchanged',
                    'execution_snapshot':'117 packaged national cells; 141 owner report at 5 Nov 00:15 HKT; core 160 complete; no live HPC read'}, indent=2) + '\n',
        encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT.parent / 'outputs')
    package(parser.parse_args().out.resolve())
