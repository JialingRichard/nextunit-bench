"""Shared figure style of the paper (IEEE two-column).

Every figure script does `import style; style.apply()` and uses style.COLORS / SINGLE / save().
Fonts are requested by name and taken from the system; no font file is shipped. The paper used
Nimbus Roman (URW base35, installed with Ghostscript on most Linux systems); without it matplotlib
falls back to the next available serif font in the list.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

SINGLE = 3.5    # IEEE single-column width, inches
DOUBLE = 7.16   # IEEE double-column width, inches

# Okabe-Ito palette, one fixed colour per method so every figure agrees.
COLORS = {
    'Astra': '#0072B2',      # blue
    'Kimi': '#56B4E9',       # sky blue
    'DeepSeek': '#009E73',   # green
    'Luna': '#E69F00',       # orange
    'Qwen': '#D55E00',       # vermilion
    'Gemma': '#CC79A7',      # purple
    'AutoML': '#7F7F7F',     # grey
    'Baseline': '#BDBDBD',   # light grey
    'Paper': '#000000',      # black: published / reported values
    'TSFM': '#8C564B',       # brown: time-series foundation models
}


def apply():
    mpl.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Nimbus Roman', 'Liberation Serif', 'Times New Roman', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 8,
        'axes.titlesize': 8,
        'axes.labelsize': 8,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
        'axes.linewidth': 0.6,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'lines.linewidth': 1.0,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
    })


def save(fig, path):
    """Save as vector PDF, without a creation date so that reruns give identical files."""
    fig.savefig(path, metadata={'CreationDate': None})
    plt.close(fig)
