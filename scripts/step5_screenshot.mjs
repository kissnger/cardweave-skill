const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const baseDir = '/Users/kai/workspace/02_hermes_workspace/004_task_card_design_20260517_1702/cardweave-skill/2026-05-22';
  const outDir = path.join(baseDir, 'screenshots');
  fs.mkdirSync(outDir, { recursive: true });

  const series = [
    { dir: 'trend', prefix: '01_商业趋势' },
    { dir: 'tool',  prefix: '02_工具推荐' },
    { dir: 'brief', prefix: '03_每日简讯' },
  ];

  const pages = [
    { file: 'cover', label: 'P1_封面' },
    { file: 'p2',    label: 'P2_详情' },
    { file: 'p3',    label: 'P3_金句' },
  ];

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 540, height: 960 },
    deviceScaleFactor: 2,
  });

  for (const s of series) {
    for (const p of pages) {
      const htmlPath = path.join(baseDir, s.dir, `${p.file}.html`);
      const pngPath = path.join(outDir, `${s.prefix}_${p.label}.png`);
      const page = await context.newPage();
      await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
      await page.screenshot({ path: pngPath, fullPage: true });
      await page.close();
      console.log(`✅ ${s.prefix}_${p.label}.png`);
    }
  }

  await browser.close();
  console.log('\n🎉 全部截图完成');
})();
