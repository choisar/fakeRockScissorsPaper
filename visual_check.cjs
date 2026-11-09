// Optional developer check: Playwright plus a Chromium-family browser.
const { chromium } = require('playwright');
const http = require('node:http');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');

async function main() {
  const args = process.argv.slice(2);
  const folder = path.resolve(args.shift() || 'outputs/validated-main');
  let executablePath, channel, artifactFolder = path.join(folder, 'browser-check');
  while (args.length) {
    const option = args.shift(), value = args.shift();
    if (!value) throw Error(`Missing value for ${option}`);
    if (option === '--browser') executablePath = path.resolve(value);
    else if (option === '--channel') channel = value;
    else if (option === '--artifacts') artifactFolder = path.resolve(value);
    else throw Error(`Unknown option: ${option}`);
  }
  if (executablePath && channel) throw Error('Choose --browser or --channel');
  if (!executablePath && !channel) {
    executablePath = [process.env.CHROME_BIN, '/usr/bin/chromium', '/usr/bin/chromium-browser',
      '/usr/bin/google-chrome', chromium.executablePath()].find(p => p && fs.existsSync(p));
    if (!executablePath) channel = 'msedge';
  }
  if (fs.existsSync(artifactFolder)) throw Error(`Choose a new --artifacts folder: ${artifactFolder}`);
  const data = JSON.parse(fs.readFileSync(path.join(folder, 'results.json'), 'utf8'));
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : { channel }) });
  // Loopback serving also works where managed browsers disallow file:// URLs.
  const html = fs.readFileSync(path.join(folder, 'report.html'));
  const server = http.createServer((request, response) => {
    if (request.url !== '/report.html') { response.writeHead(404).end(); return; }
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    response.end(html);
  });
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject); server.listen(0, '127.0.0.1', resolve);
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    const url = `http://127.0.0.1:${server.address().port}/report.html`;
    await page.goto(url);
    const observed = data.mode === 'throw-analysis';
    let selected;
    if (observed) {
      for (const c of data.conditions) {
        await page.selectOption('#population', `${c.players}/${c.colluders}`);
        await page.selectOption('#strategy', c.strategy);
        await page.locator('#quota').fill(String(c.catchers));
        assert.ok(await page.locator('#branches tr').count());
        assert.equal(await page.locator('#effects circle').count(), data.conditions.filter(r => r.players === c.players && r.colluders === c.colluders).length);
        assert.match(await page.locator('#contribution-sum').textContent(), /전체 관측 차이/);
        await page.locator('#branches button').first().click();
        assert.match(await page.locator('#game-meta').textContent(), /게임/);
        while (await page.locator('#next').isEnabled()) await page.locator('#next').click();
        assert.match(await page.locator('#transition').textContent(), /선정 종료/);
      }
      await page.evaluate(() => { current.stats.ci95 = null; current.stats.p_value_holm = null; render(); });
      assert.match(await page.locator('#ci').textContent(), /추론 불가/);
      assert.match(await page.locator('#significance').textContent(), /계산 불가/);
      await page.evaluate(() => { current.stats.p_value_holm = 0; render(); });
      assert.match(await page.locator('#significance').textContent(), /< 1e-300/);
      await page.reload();
    } else {
    assert.equal(await page.locator('#condition option').count(), data.conditions.length);
    for (let i = 0; i < data.conditions.length; i++) {
      const c = data.conditions[i];
      await page.selectOption('#condition', String(i));
      assert.ok(await page.locator('#exact').textContent());
      assert.equal(await page.locator('#individuals tr').count(), c.players);
      if (c.first_branches.some(b => b.terminal))
        assert.match(await page.locator('#branches').textContent(), /선정 종료/);
      if (c.stats.ci95 === null) assert.match(await page.locator('#ci').textContent(), /추론 불가/);
    }
    selected = Math.max(0, data.conditions.findIndex(c => c.players === 6 && c.colluders === 3 && c.catchers === 2));
    await page.locator(`button[data-index="${selected}"]`).click();
    assert.equal(await page.locator('#condition').inputValue(), String(selected));
    // Exercise unavailable inference and floating-point underflow in memory only.
    await page.evaluate(() => {
      const s = data.conditions[Number(document.getElementById('condition').value)].stats;
      s.ci95 = null; s.p_value_holm = null; s.inference_reason = 'zero_sample_variance'; render();
    });
    assert.match(await page.locator('#ci').textContent(), /표본 변동이 없어 정규 근사 추론 불가/);
    assert.match(await page.locator('#significance').textContent(), /계산 불가/);
    await page.evaluate(() => {
      data.conditions[Number(document.getElementById('condition').value)].stats.p_value_holm = 0; render();
    });
    assert.match(await page.locator('#significance').textContent(), /< 1e-300/);
    await page.reload();
    await page.selectOption('#condition', String(selected));
    }
    fs.mkdirSync(artifactFolder, { recursive: true });
    await page.screenshot({ path: path.join(artifactFolder, 'desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    if (observed) {
      for (const c of data.conditions) {
        await page.selectOption('#population', `${c.players}/${c.colluders}`);
        await page.selectOption('#strategy', c.strategy);
        await page.locator('#quota').fill(String(c.catchers));
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      }
      await page.selectOption('#strategy', 'shared_random');
      await page.locator('#quota').fill('2');
    } else {
      for (let i = 0; i < data.conditions.length; i++) {
        await page.selectOption('#condition', String(i));
        assert.equal(await page.locator('#individuals tr').count(), data.conditions[i].players);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      }
      await page.selectOption('#condition', String(selected));
    }
    await page.screenshot({ path: path.join(artifactFolder, 'mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    const evidence = { report: path.relative(__dirname, path.join(folder, 'report.html')), browser: browser.version(),
      conditions: data.conditions.length, desktop: [1440, 1000], mobile: [390, 844], pageErrors: errors,
      horizontalOverflow: false, syntheticDisplayChecks: ['null inference', 'underflow p-value'], terminalBranches: true, mode: data.mode || 'legacy', observedReplayAndBranches: observed };
    fs.writeFileSync(path.join(artifactFolder, 'verification.json'), JSON.stringify(evidence, null, 2) + '\n', { flag: 'wx' });
    console.log(JSON.stringify(evidence, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
