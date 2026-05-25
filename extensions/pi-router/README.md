# Pi Router Extension

Pi extension for Spanish-first Pi usage:

- translate Spanish prompts into concise English work prompts,
- choose an appropriate thinking level,
- keep router metadata inspectable,
- translate final user-facing answers back to Spanish.

## Install during development

Load directly while developing:

```bash
pi -e ./extensions/pi-router/src/index.ts
```

For persistent local use, copy or symlink this package into an auto-discovered Pi extension location such as:

```text
~/.pi/agent/extensions/pi-router/
```

Pi reads the installable entrypoint from `package.json`:

```json
{
  "pi": {
    "extensions": ["./src/index.ts"]
  }
}
```

## Tests

```bash
npm install
npm test
```
