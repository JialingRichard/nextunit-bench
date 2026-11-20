"""Artifact specification, validation and in-sandbox loader (filled at M3).

An artifact is a directory with ``artifact.py`` defining
``predict(input_directory, output_file)``, a ``resources.json`` (a JSON
object), and model files. Output: UTF-8 CSV ``record_id,prediction``.
"""
