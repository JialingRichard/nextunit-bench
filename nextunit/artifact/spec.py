"""The artifact specification (docs/artifact_spec.md is the prose version)."""
from __future__ import annotations

ENTRY = 'artifact.py'            # must define predict(input_directory, output_file)
RESOURCES = 'resources.json'     # must hold a JSON object; not read by the evaluator
OUTPUT_COLUMNS = ('record_id', 'prediction')
# Files a development workspace holds that are not part of the delivery.
WORKSPACE_INPUTS = frozenset({'development', 'task.md', 'info.md'})
