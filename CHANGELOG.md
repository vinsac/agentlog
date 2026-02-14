# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-14

### Added
- Core logging API: `log`, `log_vars`, `log_state`, `log_error`, `log_check`, `log_http`
- Function decorator: `@log_func` (sync and async)
- Distributed tracing: `trace`, `trace_end`, `get_trace_id`, `span`
- Decision logging: `log_decision`
- Data flow tracing: `log_flow`
- State diffing: `log_diff`
- Query logging: `log_query`
- Performance snapshots: `log_perf`
- Token-aware ringbuffer: `get_context`, `summary`, `set_buffer_size`
- JSONL file sink: `to_file`, `close_file`
- Log levels: `AGENTLOG_LEVEL` env var (debug, info, warn, error)
- Configuration: `enable`, `disable`, `configure`
- AI-first value descriptor engine with compact keys (`t`, `v`, `n`, `k`, `sh`, `dt`)
- Shape-aware descriptions for numpy, torch, and pandas objects
- PEP 561 type stubs (`py.typed`)
