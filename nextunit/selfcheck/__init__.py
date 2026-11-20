"""One-command self-check (filled at M5).

Layers: (1) SHA-256 of raw and prepared files and hidden labels, and the
MIMII_DUE metadata check (directory order and modification times independent
of the label); (2) splits against the frozen definition; (3) constant
predictor, exact scores; (4) random-forest reference.
"""
