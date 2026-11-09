// Optional developer check: requires Playwright and an installed Edge browser.
const { chromium } = require('playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
(async()=>{
 const browser = await chromium.launch({headless:true,channel:'msedge'});
 const page = await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[]; page.on('pageerror', e=>errors.push(String(e)));
 await page.goto(pathToFileURL(path.join(__dirname,'outputs/main/report.html')).href);
 if(await page.locator('#condition option').count()!==10) throw Error('conditions missing');
 for(let i=0;i<10;i++){
  await page.selectOption('#condition',String(i));
  if(!await page.locator('#exact').textContent())throw Error('missing exact value');
  if(await page.locator('#individuals tr').count()!== (i<4?4:6))throw Error('individual rows');
 }
 await page.locator('button[data-index="7"]').click();
 if(await page.locator('#condition').inputValue()!=='7')throw Error('condition navigation');
 await page.screenshot({path:path.join(__dirname,'outputs/desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:path.join(__dirname,'outputs/mobile.png'),fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow)throw Error('mobile page overflow');
 if(errors.length)throw Error(errors.join('\n'));
 fs.writeFileSync(path.join(__dirname,'outputs/browser-verification.json'),JSON.stringify({conditions:10,desktop:[1440,1000],mobile:[390,844],pageErrors:errors,horizontalOverflow:overflow},null,2));
 console.log('10 conditions, navigation, desktop/mobile rendering passed');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
