import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);

async function read(path) {
  return readFile(new URL(path, root), 'utf8');
}

describe('pi-router extension structure', () => {
  it('declares an installable Pi extension entrypoint', async () => {
    const pkg = JSON.parse(await read('package.json'));

    assert.equal(pkg.name, 'pi-router');
    assert.deepEqual(pkg.pi.extensions, ['./index.ts']);
    assert.equal(pkg.scripts.test, 'node --test tests/*.test.mjs');
  });

  it('exports a default Pi extension factory', async () => {
    const source = await read('index.ts');

    assert.match(source, /export default function/);
    assert.match(source, /ExtensionAPI/);
    assert.match(source, /pi\.on\("input"/);
  });
});
