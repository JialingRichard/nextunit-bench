"""Regenerate the paper's figures from the files in paper/data/.

    python paper/make_figures.py            # Figs. 2-6 and the appendix figure -> paper/figures/out/
    python paper/make_figures.py --fig1     # also compile Fig. 1 (TikZ) if tectonic or pdflatex is installed

Needs numpy, pandas and matplotlib. Each script also writes the series it plots to figures/out/figN_series.csv.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FIG = Path(__file__).resolve().parent / 'figures'
SCRIPTS = ['fig2_scores.py', 'fig3_protocols.py', 'fig4_transplant.py', 'fig5_execution.py', 'fig6_levers.py',
           'figA_alt_baselines.py']


def fig1():
    out = FIG / 'out'
    out.mkdir(exist_ok=True)
    if shutil.which('tectonic'):
        cmd = ['tectonic', '-X', 'compile', '--outdir', str(out), str(FIG / 'fig1_protocol.tex')]
    elif shutil.which('pdflatex'):
        cmd = ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(out), str(FIG / 'fig1_protocol.tex')]
    else:
        print('fig1: neither tectonic nor pdflatex found; skipped (source: figures/fig1_protocol.tex)')
        return 0
    return subprocess.run(cmd, capture_output=True).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fig1', action='store_true', help='also compile the TikZ diagram of Fig. 1')
    args = ap.parse_args()
    failed = []
    for s in SCRIPTS:
        r = subprocess.run([sys.executable, str(FIG / s)], cwd=FIG, capture_output=True, text=True)
        print(f'{s}: {"ok" if r.returncode == 0 else "FAILED"}')
        if r.returncode:
            print(r.stderr[-2000:]); failed.append(s)
    if args.fig1 and fig1():
        failed.append('fig1_protocol.tex')
    print('outputs in', FIG / 'out')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
