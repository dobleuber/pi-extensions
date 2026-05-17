# Roger Laptop Interface

Roger is a voice-first laptop interface backed by pi-agent. The MVP is driven by the OpenSpec change in `openspec/changes/add-roger-voice-laptop-interface/`.

## Development

Run the current test suite with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Run the CLI health check with:

```bash
PYTHONPATH=src python3 -m roger.cli health
```
