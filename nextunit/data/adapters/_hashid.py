"""Record IDs of the paper's 2026-09-24 conversions: 'r_' + 16 hex digits of SHA-256('20260924:<value>')."""
import hashlib

SEED = 20260924


def rid(value: str) -> str:
    return 'r_' + hashlib.sha256(f'{SEED}:{value}'.encode()).hexdigest()[:16]
