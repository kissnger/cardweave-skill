/**
 * Cardweave 手动截图脚本
 * 当 generate.py --screenshot 因 Playwright 安装问题失败时使用。
 *
 * 用法：
 *   cd cardweave-skill/
 *   npm install -g playwright
 *   npx playwright install chromium
 *   NODE_PATH=$(npm root -g) node scripts/screenshot.mjs
 *
 * 输出：{日期}/screenshots/{序号}_{分类}_{页码}.png 共 9 张
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// 从 template.json 读取日期
const tmpl = JSON.parse(fs.readFileSync('templates/template.json', 'utf-8'));
const dateStr = tmpl._meta.date;

const baseDir = path.resolve(dateStr);
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

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 540, height: 960 },
    deviceScaleFactor: 2,
  });

  for (const s of series) {
    for (const p of pages) {
      const htmlPath = path.join(baseDir, s.dir, `${p.file}.html`);
      if (!fs.existsSync(htmlPath)) {
        console.log(`⚠️  跳过（不存在）: ${htmlPath}`);
        continue;
      }
      const pngPath = path.join(outDir, `${s.prefix}_${p.label}.png`);
      const page = await ctx.newPage();
      await page.goto(`file://${path.resolve(htmlPath)}`, {
        waitUntil: 'networkidle',
        timeout: 15000,
      });
      await page.waitForTimeout(500);
      await page.screenshot({ path: pngPath, fullPage: true });
      await page.close();
      const size = fs.statSync(pngPath).size;
      console.log(`✅ ${s.prefix}_${p.label}.png  (${(size / 1024).toFixed(0)}KB)`);
    }
  }

  await browser.close();
  console.log(`\n🎉 全部截图完成 → ${outDir}`);
})().catch(err => {
  console.error('❌ 截图失败:', err.message);
  process.exit(1);
});
