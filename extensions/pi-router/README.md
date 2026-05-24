# pi-router

Pi extension for Spanish-to-English prompt routing, thinking-level selection, and Spanish final-answer presentation.

This package is intended to be installed or linked into Pi's extension discovery path, for example:

```bash
mkdir -p ~/.pi/agent/extensions
ln -s "$PWD/extensions/pi-router" ~/.pi/agent/extensions/pi-router
```

The extension entry point is `index.ts` and is declared in `package.json` under `pi.extensions`.
