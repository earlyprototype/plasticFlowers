import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import next from 'next';
import { chromium } from 'playwright-core';

const fixture = (name) => fileURLToPath(new URL('../fixtures/' + name, import.meta.url));

test('opens export files offline, preserves a valid view on error, and clears the canvas', async (t) => {
  const app = next({ dev: false, hostname: '127.0.0.1', port: 0 });
  await app.prepare();
  const server = createServer(app.getRequestHandler());
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  t.after(async () => {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
    await app.close();
  });

  const browser = await chromium.launch({ channel: process.env.CHROMIUM_CHANNEL || 'chrome' });
  t.after(() => browser.close());
  const context = await browser.newContext({ reducedMotion: 'reduce', serviceWorkers: 'block' });
  const page = await context.newPage();
  const requests = [];
  const errors = [];
  let openingFiles = false;
  page.on('pageerror', (e) => errors.push(e.message));
  await context.routeWebSocket('**/*', (socket) => {
    requests.push(socket.url());
    socket.close();
  });
  await context.route('**/*', (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const asset = url.pathname === '/viewer' || url.pathname.startsWith('/_next/static/') ||
      url.pathname === '/favicon.ico';
    if (!openingFiles && url.origin === origin && request.method() === 'GET' && asset) {
      return route.continue();
    }
    requests.push(request.method() + ' ' + url.href);
    return route.abort();
  });

  const response = await page.goto(origin + '/viewer', { waitUntil: 'networkidle' });
  assert.equal(response.status(), 200);
  const input = page.getByLabel('Open JSON export');
  await input.waitFor();
  openingFiles = true;
  await context.setOffline(true);
  await input.setInputFiles(fixture('rooftop-garden.json'));
  const transcript = page.getByRole('region', { name: 'Transcript' });
  const text = 'The rooftop beds hold basil. The downspout fills the rain barrel.\nBarrel water feeds the basil roots.';
  await transcript.getByText(text).waitFor();

  // Inspect the core bound to the real canvas, including the derived bridge.
  const viewport = page.locator('.graph-canvas__viewport');
  await page.waitForFunction(() => document.querySelector('.graph-canvas__viewport')?._cyreg?.cy.edges().length === 3);
  async function inspectGraph() {
    return viewport.evaluate((el) => {
      const cy = el._cyreg.cy;
      const bridge = cy.edges('.inter-flower');
      return {
        flowers: cy.nodes('.flower').map((f) => f.data('label')).sort(),
        bridge: bridge.map((e) => [e.source().data('label'), e.data('description'), e.target().data('label')]),
        grabbable: cy.nodes().some((n) => n.grabbable()),
      };
    });
  }
  const expected = {
    flowers: ['Rain collection (2)', 'Rooftop garden (2)'],
    bridge: [['Rain barrel', 'waters roots', 'Basil roots']],
    grabbable: false,
  };
  assert.deepEqual(await inspectGraph(), expected);
  const midpoint = await viewport.evaluate((el) => el._cyreg.cy.edges('.inter-flower').renderedMidpoint());
  await viewport.hover({ position: midpoint });
  await page.waitForFunction(() => {
    const bridge = document.querySelector('.graph-canvas__viewport')._cyreg.cy.edges('.inter-flower');
    return bridge.hasClass('hovered') && bridge.style('label') === 'waters roots';
  });

  async function checkRejected(content, error) {
    await input.setInputFiles({ name: 'broken.json', mimeType: 'application/json', buffer: Buffer.from(content) });
    await page.getByRole('alert').filter({ hasText: error }).waitFor();
    assert.deepEqual(await inspectGraph(), expected);
    assert.equal(await transcript.locator('p').textContent(), text);
  }
  await checkRejected('{', /valid JSON/i);
  await checkRejected('{}', /session/i);

  const garden = JSON.parse(await readFile(fixture('rooftop-garden.json'), 'utf8'));
  for (const [change, error] of [
    [({ graph }) => graph.flowers[0].member_ids.push('missing-member'), /garden.*member.*missing-member/i],
    [({ graph }) => graph.flowers[0].member_ids.push('barrel'), /garden.*member.*barrel/i],
    [({ graph }) => { graph.flowers[0].member_ids = ['roof']; }, /garden.*missing.*roots/i],
    [({ graph }) => graph.flowers[0].member_ids.push('roots'), /garden.*duplicate.*roots/i],
    [({ graph }) => { graph.flowers[0].stem_node_id = 'missing-stem'; }, /garden.*stem.*missing-stem/i],
    [({ graph }) => { graph.flowers[0].stem_node_id = 'barrel'; }, /garden.*stem.*barrel/i],
    [({ graph }) => { graph.relationships[2].description = ''; }, /graph\.relationships\.2\.description.*2.*80/i],
    [({ graph }) => { graph.flowers[0].label = ''; }, /graph\.flowers\.0\.label.*2.*64/i],
    [({ graph }) => graph.bridges.push({
      source_flower_id: 'absent-flower', target_flower_id: 'garden',
      connecting_relationships: [graph.relationships[2]],
    }), /bridge.*missing flower.*absent-flower/i],
    [({ graph }) => graph.bridges.push({
      source_flower_id: 'water', target_flower_id: 'garden',
      connecting_relationships: [{ ...graph.relationships[2], description: 'drains roots' }],
    }), /irrigates.*description/i],
    [({ session }) => { session.created_at = '2026-02-30T10:00:00Z'; }, /session\.created_at.*timestamp/i],
    [({ graph }) => { graph.nodes[0].last_active = '2026-02-30T10:00:00Z'; }, /graph\.nodes\.0\.last_active.*timestamp/i],
    [({ session }) => { session.language_variant = ['en-GB']; }, /session\.language_variant.*string/i],
  ]) {
    const invalid = structuredClone(garden);
    // Make partial replacement of either the graph or the transcript observable.
    invalid.graph.flowers[1].label = 'Replacement flower';
    invalid.session.transcript = 'Replacement transcript';
    change(invalid);
    await checkRejected(JSON.stringify(invalid), error);
  }

  await input.setInputFiles(fixture('empty.json'));
  await page.getByRole('heading', { name: 'Empty notebook' }).waitFor();
  assert.equal(await viewport.evaluate((el) => el._cyreg.cy.elements().length), 0);
  assert.equal(await transcript.getByText('No transcript in this export.').count(), 1);
  assert.equal(await page.getByRole('main').getByRole('alert').count(), 0);
  assert.deepEqual(await page.evaluate(async () => [
    localStorage.length, sessionStorage.length, (await indexedDB.databases()).length,
  ]), [0, 0, 0]);
  assert.deepEqual(requests, []);
  assert.deepEqual(errors, []);
});
