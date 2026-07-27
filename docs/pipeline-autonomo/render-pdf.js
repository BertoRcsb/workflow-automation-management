const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const dir = __dirname;
  const htmlPath = 'file://' + path.join(dir, 'Optimus-Prime-Pipeline-Autonomo.html');
  const out = path.join(dir, 'Optimus-Prime-Pipeline-Autonomo.pdf');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.goto(htmlPath, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: out,
    format: 'A4',
    printBackground: true,
    margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' },
  });
  await browser.close();
  console.log('PDF gerado: ' + out);
})();
