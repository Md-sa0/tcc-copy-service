import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
process.chdir(import.meta.dirname);
const browser = await chromium.launch();
const base = process.env.E2E_BASE_URL || 'http://localhost:8082';
const report = { environment: 'Chromium local, API simulada; CPU 4x apenas na amostra indicada', loads: [], layouts: [], errors: [] };
await mkdir('../artifacts/responsiveness', { recursive: true });
try {
  for (const cpu of [1, 1, 1, 4]) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
    await page.addInitScript(() => {
      window.reviewLongTasks = [];
      new PerformanceObserver(list => window.reviewLongTasks.push(...list.getEntries().map(e => e.duration))).observe({ type: 'longtask', buffered: true });
    });
    const start = performance.now();
    await page.goto(base);
    await page.getByText('API conectada', { exact: true }).waitFor();
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const readyMs = performance.now() - start;
    const metrics = await page.evaluate(() => ({ paints: performance.getEntriesByType('paint').map(e => ({ name: e.name, ms: e.startTime })), jsBytes: performance.getEntriesByType('resource').filter(e => e.name.endsWith('.js')).reduce((a,e)=>a+e.decodedBodySize,0), longTasks: window.reviewLongTasks }));
    report.loads.push({ cpu, readyMs, ...metrics });
    await context.close();
  }
  const page = await browser.newPage();
  page.on('pageerror', e => report.errors.push(e.message));
  const screens = [
    ['Estúdio de criação', 'Gerar textos para um produto'],
    ['Catálogo de produtos', 'Catálogo de produtos'],
    ['Como funciona', 'Como usar o CopyLab'],
    ['Métricas de engenharia', 'Resultados das requisições'],
  ];
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(base);
    await page.getByText('API conectada', { exact: true }).waitFor();
    for (const [button, title] of screens) {
      const start = performance.now();
      await page.getByRole('button', { name: button, exact: true }).click();
      await page.getByRole('heading', { name: title, exact: true }).waitFor();
      if (button === 'Métricas de engenharia') await page.locator('tbody tr').first().waitFor();
      if (button === 'Catálogo de produtos') await page.locator('.catalog-card').first().waitFor();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const actionMs = performance.now() - start;
      const layout = await page.evaluate(() => ({ viewport: innerWidth, content: document.documentElement.scrollWidth, overflowElements: [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && getComputedStyle(e).position !== 'absolute').slice(0,8).map(e=>e.className) }));
      report.layouts.push({ width, screen: button, actionMs, ...layout });
      await page.screenshot({ path: `../artifacts/responsiveness/${width}-${screens.findIndex(s=>s[0]===button)}.png`, fullPage: true });
    }
  }
  await writeFile(`../artifacts/responsiveness/${process.env.REVIEW_LABEL || 'baseline'}.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  assert.equal(report.errors.length,0);
  assert.ok(report.layouts.every(r=>r.content<=r.viewport), 'Horizontal page overflow');
} finally { await browser.close(); }
