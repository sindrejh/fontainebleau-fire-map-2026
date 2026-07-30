/* Røyktest for index.html.
 *
 *   python3 -m http.server 8931 &
 *   npm i playwright && node tools/royktest.mjs
 *
 * Alt utenfor localhost blokkeres under kjøringen. Det er med vilje: sida skal
 * virke uten CDN, og eneste eksterne kall som er igjen, er kartflisene.
 * Bakgrunnskartet faller da bort, men ingenting annet får lov til å svikte. */
import { chromium } from 'playwright';

const base = process.env.URL || 'http://127.0.0.1:8931/index.html';
const vert = new URL(base).origin;
const browser = await chromium.launch(
  process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

const feil = [];
// Kartflisene er de eneste eksterne kallene, og de blokkeres med vilje under.
const venta = /ERR_FAILED|ERR_BLOCKED|net::ERR/;
page.on('console', m => { if (m.type() === 'error' && !venta.test(m.text())) feil.push('console: ' + m.text()); });
page.on('pageerror', e => feil.push('pageerror: ' + e.message));
page.on('response', r => { if (r.status() >= 400) feil.push(`HTTP ${r.status()} ${r.url()}`); });
await page.route('**', r => r.request().url().startsWith(vert) ? r.continue() : r.abort());

await page.goto(base, { waitUntil: 'networkidle' });

const t = async (navn, fn) => {
  try { const v = await fn(); console.log(`  ${v ? 'OK  ' : 'FEIL'} ${navn}${v && v !== true ? ' → ' + v : ''}`); return !!v; }
  catch (e) { console.log(`  FEIL ${navn} → ${e.message}`); return false; }
};

console.log('\n— innhold —');
let ok = true;
ok &= await t('90 rader i sektorlista', async () => (await page.locator('.row').count()) === 90 ? '90' : false);
ok &= await t('faktakort fylt', async () => (await page.locator('.facts dd').count()) === 4);
const nbsp = t2 => t2.replace(/[\u00a0\u202f]/g, ' ');
ok &= await t('ingressen har tall', async () => nbsp(await page.locator('#stand').innerText()).includes('19 137'));
ok &= await t('ingen 923-rest', async () => !(await page.locator('body').innerText()).includes('923'));
ok &= await t('metode nevner blokkene', async () => {
  await page.locator('#metode summary').click();
  return (await page.locator('#method').innerText()).includes('Diplodocus');
});

console.log('\n— tallkonsistens i teksten —');
const kropp = nbsp(await page.locator('body').innerText());
for (const n of ['926', '921', '23 613', '22 692', '2 104', '19 137', '76 atskilte'])
  ok &= await t(`«${n}» finnes`, () => kropp.includes(n));

console.log('\n— sektorvalg og blokker —');
ok &= await t('velg Diplodocus', async () => {
  await page.fill('#q', 'diplodocus');
  await page.waitForTimeout(250);
  await page.locator('.row').first().click();
  await page.waitForTimeout(700);
  return (await page.locator('.pname').innerText()) === 'Diplodocus';
});
ok &= await t('detaljene viser 159 av 159', async () =>
  nbsp(await page.locator('.picked').innerText()).includes('159 av 159'));
ok &= await t('gammelt rektangeltall nevnt', async () =>
  (await page.locator('.picked').innerText()).includes('31,2'));
ok &= await t('blokkprikker tegnet i kartet', async () =>
  await page.evaluate(() => document.querySelectorAll('canvas').length > 0));

console.log('\n— søk og sortering —');
ok &= await t('søk uten aksent finner Ségognole', async () => {
  await page.fill('#q', 'segognole');
  await page.waitForTimeout(250);
  return (await page.locator('.row').count()) === 1;
});
ok &= await t('klyngesøk finner Apremont', async () => {
  await page.fill('#q', 'apremont');
  await page.waitForTimeout(250);
  return (await page.locator('.row').count()) >= 8;
});
ok &= await t('tomt søk sier fra', async () => {
  await page.fill('#q', 'zzzz');
  await page.waitForTimeout(250);
  return (await page.locator('.nohit').count()) === 1;
});
ok &= await t('sortering på navn', async () => {
  await page.fill('#q', '');
  await page.selectOption('#sortby', 'navn');
  await page.waitForTimeout(250);
  // Sektorene 91.1 og 95.2 heter tall og sorterer foran bokstavene.
  const f = await page.locator('.row .nm').first().innerText();
  return f === '91.1' ? f : false;
});
ok &= await t('sortering på mest brent', async () => {
  await page.selectOption('#sortby', 'brent');
  await page.waitForTimeout(250);
  return (await page.locator('.clus').count()) > 0;
});

console.log('\n— filtre —');
ok &= await t('filter skjuler rader', async () => {
  const før = await page.locator('.row').count();
  await page.locator('.chip').last().click();
  await page.waitForTimeout(200);
  const etter = await page.locator('.row').count();
  await page.locator('.chip').last().click();
  await page.waitForTimeout(200);
  return etter < før ? `${før} → ${etter}` : false;
});

console.log('\n— tilgjengelighet —');
ok &= await t('kartet har rolle og navn', async () =>
  await page.evaluate(() => { const m = document.getElementById('map');
    return m.getAttribute('role') === 'region' && !!m.getAttribute('aria-label'); }));
ok &= await t('#picked er aria-live', async () =>
  await page.evaluate(() => document.getElementById('picked').getAttribute('aria-live') === 'polite'));
ok &= await t('lang=nb', async () => await page.evaluate(() => document.documentElement.lang === 'nb'));
ok &= await t('radene har aria-label', async () =>
  await page.evaluate(() => !!document.querySelector('.row').getAttribute('aria-label')));

console.log('\n— blokktellingen —');
ok &= await t('nettleseren teller likt som tools/beregn.py', async () => {
  const r = await page.evaluate(() => {
    const BB = BURN_RINGS.map(r => { let a=90,b=-90,c=180,d=-180;
      for (const q of r) { if(q[0]<a)a=q[0]; if(q[0]>b)b=q[0]; if(q[1]<c)c=q[1]; if(q[1]>d)d=q[1]; }
      return [a,b,c,d]; });
    const inne = (lat, lon) => {
      for (let k = 0; k < BURN_RINGS.length; k++) {
        const q = BB[k];
        if (lat<q[0] || lat>q[1] || lon<q[2] || lon>q[3]) continue;
        const r = BURN_RINGS[k]; let v = false;
        for (let i=0, j=r.length-1; i<r.length; j=i++) {
          const yi=r[i][0], xi=r[i][1], yj=r[j][0], xj=r[j][1];
          if ((yi>lat)!==(yj>lat) && lon < (xj-xi)*(lat-yi)/(yj-yi)+xi) v = !v;
        }
        if (v) return true;
      }
      return false;
    };
    let avvik = [], tot = 0, n = 0;
    for (const s of SECTORS) {
      const [la0, lo0, d] = PTS[s.n];
      let a = 0, o = 0, c = 0, m = 0;
      for (let i = 0; i < d.length; i += 2) {
        a += d[i]; o += d[i+1]; m++;
        if (inne(la0 + a/1e5, lo0 + o/1e5)) c++;
      }
      tot += c; n += m;
      if (c !== s.bb || m !== s.blokk) avvik.push(`${s.n}: ${c}/${m} mot ${s.bb}/${s.blokk}`);
    }
    return { avvik, tot, n, meta: [META.blokk_brent, META.blokk_total] };
  });
  if (r.avvik.length) { console.log('    ' + r.avvik.join('\n    ')); return false; }
  return r.n === r.meta[1] && r.tot === r.meta[0] ? `${r.tot} / ${r.n}` : false;
});

console.log('\n— feil i konsollen —');
if (feil.length) { console.log(feil.map(f => '  ' + f).join('\n')); ok = false; }
else console.log('  ingen');

await browser.close();
console.log('\n' + (ok ? 'ALT OK' : 'NOE FEILET'));
process.exit(ok ? 0 : 1);
