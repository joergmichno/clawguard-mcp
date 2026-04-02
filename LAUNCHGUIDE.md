# ClawGuard MCP Server — Launch Guide

## What It Does
ClawGuard MCP scans AI agent inputs for prompt injection threats in real-time. 225 detection patterns, 15 languages, OWASP LLM + Agentic Top 10 mapped.

## Setup
### Prerequisites
- Python 3.10+
- Free API key from [prompttools.co/api/v1/](https://prompttools.co/api/v1/)

### Install & Run
```bash
uvx clawguard-mcp
# Or: pip install clawguard-mcp && clawguard-mcp
```

### Configuration
Set `CLAWGUARD_API_KEY` environment variable.

## Available Tools
| Tool | Description |
|------|-------------|
| `scan_text` | Scan text for prompt injection threats |
| `scan_url` | Fetch + scan URL content |
| `batch_scan` | Scan multiple texts at once |
| `get_scan_stats` | Usage statistics |

## Tags
security, prompt-injection, ai-safety, mcp-server, eu-ai-act, owasp, compliance

## Links
- [GitHub](https://github.com/joergmichno/clawguard-mcp) | [Scanner](https://github.com/joergmichno/clawguard) | [Free Scan](https://prompttools.co/shield) | [PyPI](https://pypi.org/project/clawguard-mcp/)
