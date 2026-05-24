# Roger Laptop Interface

Roger is a voice-first laptop interface backed by pi-agent. The MVP is driven by the OpenSpec change in `openspec/changes/add-roger-voice-laptop-interface/`.

## Development

Create/sync the development environment with uv:

```bash
uv sync
```

Run the current test suite with:

```bash
uv run python -m unittest discover -s tests
```

Run the CLI health check with:

```bash
uv run roger health
```
