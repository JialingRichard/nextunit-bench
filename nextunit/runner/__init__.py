"""Minimal agent runner (filled at M6).

OpenCode with an OpenAI-compatible endpoint (credentials from environment
variables only); compute proxy exposed as the MCP tool ``run_command``;
two-hour effective budget (compute queueing excluded); smoke check, sealing,
evaluation; checkpoints and resume; one fold or all 58.

Reserved, not in v1.0: read-only skills mounted at ``/skills``, extra tool
libraries in the runtime, and a paragraph in the initial prompt.
"""
