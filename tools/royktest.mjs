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

let ok = true;
const t = async (navn, fn) => {
  let v, e;
  try { v = await fn(); } catch (err) { e = err.message; }
  console.log(`  ${v ? 'OK  ' : 'FEIL'} ${navn}${v && v !== true ? ' → ' + v : e ? ' → ' + e : ''}`);
  if (!v) ok = false;
  return !!v;
};
const nbsp = s => s.replace(/[  ]/g, ' ');

async function nySide(opts = {}) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const feil = [];
  // Kartflisene er de eneste eksterne kallene, og de blokkeres med vilje under.
  const venta = /ERR_FAILED|ERR_BLOCKED|net::ERR/;
  page.on('console', m => { if (m.type() === 'error' && !venta.test(m.text())) feil.push('console: ' + m.text()); });
  page.on('pageerror', e => feil.push('pageerror: ' + e.message));
  page.on('response', r => { if (r.status() >= 400) feil.push(`HTTP ${r.status()} ${r.url()}`); });
  await page.route('**', r => r.request().url().startsWith(vert) ? r.continue() : r.abort());
  if (opts.tid) await page.clock.setFixedTime(new Date(opts.tid));
  await page.goto(base + (opts.q || ''), { waitUntil: 'networkidle' });
  return { page, feil };
}

/* Det som skal stemme på begge språk. Tallene skrives ulikt — 19 137 mot
   19,137 — så hver forventning bærer sin egen skrivemåte. */
const SPRAAK = {
  nb: {
    h1: 'Hva brannen faktisk tok.', nav: 'KART',
    tall: ['926', '921', '23 613', '22 692', '2 104', '19 137', '76 atskilte'],
    panel: '153 av 475', gammelt: '56,3', pct: '32,2 %',
    metode: 'Hva tallene bygger på', knapp: 'EN',
    tom: 'Ingen sektorer passer søket.', logg: 'Målet lagt om: faktiske blokker',
    alleKnapp: 'Åpne alle områder', alleLukk: 'Lukk alle områder',
    klSum: '1 877 av 5 935 blokker', klTally: 'Alle 90 sektorene fordelt på 19 områder.',
    klRen: 'Ingen av 2 339 blokker brent',
    ess: 'Ligger i Essonne.', nemours: 'Forêt communale de Nemours',
    ikkeher: 'gjelder ikke her',
  },
  en: {
    h1: 'What the fire actually took.', nav: 'MAP',
    tall: ['926', '921', '23,613', '22,692', '2,104', '19,137', '76 separate'],
    panel: '153 of 475', gammelt: '56.3', pct: '32.2%',
    metode: 'What the figures rest on', knapp: 'NO',
    tom: 'No sectors match that search.', logg: 'The measure changes: actual boulders',
    alleKnapp: 'Expand all areas', alleLukk: 'Collapse all areas',
    klSum: '1,877 of 5,935 boulders', klTally: 'All 90 sectors across 19 areas.',
    klRen: 'None of 2,339 boulders burned',
    ess: 'Lies in the Essonne.', nemours: 'Forêt communale de Nemours',
    ikkeher: 'does not apply here',
  },
};

/* Åpne alle / lukk alle, med knappeteksten som skifter. */
async function t2sjekk(page, F) {
  const b = page.locator('#alle');
  if ((await b.innerText()) !== F.alleKnapp) throw new Error('feil knappetekst: ' + await b.innerText());
  await b.click(); await page.waitForTimeout(350);
  if ((await page.locator('.row:visible').count()) !== 90) throw new Error('åpne alle ga ikke 90 rader');
  if ((await b.innerText()) !== F.alleLukk) throw new Error('knappen skiftet ikke til lukk');
  await b.click(); await page.waitForTimeout(350);
  if ((await page.locator('.row:visible').count()) !== 0) throw new Error('lukk alle skjulte ikke radene');
}

for (const [lang, F] of Object.entries(SPRAAK)) {
  console.log(`\n══ ${lang} ══`);
  const { page, feil } = await nySide({ q: '?lang=' + lang });

  console.log('— innhold —');
  await t('html lang', async () => (await page.evaluate(() => document.documentElement.lang)) === lang);
  await t('overskrift', async () => (await page.locator('h1').innerText()).replace(/\n/g, ' ') === F.h1);
  await t('menyen er oversatt', async () => (await page.locator('#nav a').first().innerText()) === F.nav);
  await t('90 rader i sektorlista', async () => (await page.locator('.row').count()) === 90 ? '90' : false);
  await t('faktakort fylt', async () => (await page.locator('.facts dd').count()) === 4);
  await t('ingen 923-rest', async () => !(await page.locator('body').innerText()).includes('923'));
  await t('metodeteksten nevner Diplodocus', async () => {
    await page.locator('#metode summary').click();
    return (await page.locator('#method').innerText()).includes('Diplodocus');
  });

  console.log('— tallkonsistens i teksten —');
  const kropp = nbsp(await page.locator('body').innerText());
  for (const n of F.tall) await t(`«${n}» finnes`, () => kropp.includes(n));

  console.log('— endringsloggen —');
  await t('elleve oppføringer', async () => (await page.locator('.tl li').count()) === 11 ? '11' : false);
  await t('nyeste står øverst', async () =>
    (await page.locator('.tl li').first().innerText()).includes(F.logg));
  await t('oppføringene lenker til kilder', async () =>
    (await page.locator('.tl .k').count()) >= 5);
  await t('datoene er maskinlesbare', async () =>
    (await page.locator('.tl time[datetime]').count()) === 11);
  await t('varselet er skjult før forbudsdatoen', async () =>
    !(await page.locator('#warn').isVisible()));

  console.log('— sammenslåtte områder —');
  await t('19 områder', async () => (await page.locator('.clus').count()) === 19 ? '19' : false);
  await t('ingen rader synlige ved start', async () =>
    (await page.locator('.row:visible').count()) === 0);
  await t('tellelinja teller områder', async () =>
    nbsp(await page.locator('#tally').innerText()) === F.klTally);
  await t('mest brent område øverst', async () =>
    (await page.locator('.clus .g').first().innerText()).startsWith('MONT AIGU'));
  await t('sammendraget viser blokktallet', async () =>
    nbsp(await page.locator('.clus', { hasText: 'TROIS PIGNONS' }).first().innerText()).includes(F.klSum));
  await t('uberørt område sier at ingenting er brent', async () =>
    nbsp(await page.locator('.clus', { hasText: 'APREMONT' }).first().innerText()).includes(F.klRen));
  await t('klikk på overskrifta åpner området', async () => {
    const tp = page.locator('.clus', { hasText: 'TROIS PIGNONS' }).first();
    await tp.click(); await page.waitForTimeout(250);
    const n = await page.locator('.row:visible').count();
    const a = await tp.getAttribute('aria-expanded');
    await tp.click(); await page.waitForTimeout(250);
    return n === 28 && a === 'true' && (await page.locator('.row:visible').count()) === 0 ? '28' : false;
  });
  await t('åpne og lukk alle', async () => {
    await t2sjekk(page, F);
    return true;
  });
  await t('valg fra søk holder området åpent etterpå', async () => {
    await page.fill('#q', 'diplodocus'); await page.waitForTimeout(250);
    await page.locator('.row').first().click(); await page.waitForTimeout(800);
    await page.fill('#q', ''); await page.waitForTimeout(350);
    return (await page.locator('.row[aria-current="true"]:visible').count()) === 1 &&
           (await page.locator('.row:visible').count()) === 28;
  });
  await t('områdeoverskriftene er knapper med aria-controls', async () =>
    await page.evaluate(() => [...document.querySelectorAll('.clus')].every(
      c => c.tagName === 'BUTTON' && c.hasAttribute('aria-expanded') &&
           document.getElementById(c.getAttribute('aria-controls')))));

  console.log('— sektorvalg og blokker —');
  await t('velg J.A. Martin', async () => {
    await page.fill('#q', 'J.A. Martin');
    await page.waitForTimeout(250);
    await page.locator('.row').first().click();
    await page.waitForTimeout(900);
    return (await page.locator('.pname').innerText()) === 'J.A. Martin';
  });
  await t('detaljene viser blokktallet', async () =>
    nbsp(await page.locator('.picked').innerText()).includes(F.panel));
  await t('gammelt rektangeltall nevnt', async () =>
    (await page.locator('.picked').innerText()).includes(F.gammelt));
  await t('prosenten skrives riktig for språket', async () =>
    nbsp(await page.locator('.row .pct').first().innerText()) === F.pct);
  await t('blokkprikker tegnet i kartet', async () =>
    await page.evaluate(() => document.querySelectorAll('canvas').length > 0));
  /* Essonne har sitt eget forbud, som kommer og går raskere enn sida oppdateres.
     Merknaden er hele grunnen til at sektorene er skilt ut, så den må vises. */
  await t('Essonne-sektor bærer merknaden', async () => {
    await page.fill('#q', 'Haute Pierre'); await page.waitForTimeout(250);
    await page.locator('.row').first().click(); await page.waitForTimeout(900);
    return (await page.locator('.picked').innerText()).includes(F.ess);
  });
  await t('sektor i Seine-et-Marne bærer den ikke', async () => {
    await page.fill('#q', 'Rocher Gréau'); await page.waitForTimeout(250);
    await page.locator('.row').first().click(); await page.waitForTimeout(900);
    return !(await page.locator('.picked').innerText()).includes(F.ess);
  });
  /* Mont d'Olivet ligger utenfor de tre statsskogene, men innenfor forbudet.
     Sier sida «forbudet gjelder ikke her», er det direkte feil. */
  await t('Mont d’Olivet sies å være innenfor forbudet', async () => {
    await page.fill('#q', 'Olivet'); await page.waitForTimeout(250);
    await page.locator('.row').first().click(); await page.waitForTimeout(900);
    const s = await page.locator('.picked').innerText();
    return s.includes(F.nemours) && !s.includes(F.ikkeher);
  });

  console.log('— søk og sortering —');
  await t('søk uten aksent finner Ségognole', async () => {
    await page.fill('#q', 'segognole'); await page.waitForTimeout(250);
    return (await page.locator('.row').count()) === 1;
  });
  await t('klyngesøk finner Apremont', async () => {
    await page.fill('#q', 'apremont'); await page.waitForTimeout(250);
    return (await page.locator('.row').count()) >= 8;
  });
  await t('tomt søk sier fra', async () => {
    await page.fill('#q', 'zzzz'); await page.waitForTimeout(250);
    return (await page.locator('.nohit').innerText()) === F.tom;
  });
  await t('sortering på navn', async () => {
    await page.fill('#q', ''); await page.selectOption('#sortby', 'navn');
    await page.waitForTimeout(250);
    // Sektorene 91.1 og 95.2 heter tall og sorterer foran bokstavene.
    const f = await page.locator('.row .nm').first().innerText();
    return f === '91.1' ? f : false;
  });
  await t('sortering på mest brent grupperer i klynger', async () => {
    await page.selectOption('#sortby', 'brent'); await page.waitForTimeout(250);
    return (await page.locator('.clus').count()) > 0;
  });

  console.log('— filtre —');
  await t('filter skjuler rader', async () => {
    const før = await page.locator('.row').count();
    await page.locator('.chip').last().click(); await page.waitForTimeout(200);
    const etter = await page.locator('.row').count();
    await page.locator('.chip').last().click(); await page.waitForTimeout(200);
    return etter < før ? `${før} → ${etter}` : false;
  });

  console.log('— tilgjengelighet —');
  await t('kartet har rolle og navn', async () =>
    await page.evaluate(() => { const m = document.getElementById('map');
      return m.getAttribute('role') === 'region' && !!m.getAttribute('aria-label'); }));
  await t('#picked er aria-live', async () =>
    await page.evaluate(() => document.getElementById('picked').getAttribute('aria-live') === 'polite'));
  await t('radene har aria-label', async () =>
    await page.evaluate(() => !!document.querySelector('.row').getAttribute('aria-label')));
  await t('språkknappen har navn', async () =>
    await page.evaluate(() => !!document.getElementById('lang').getAttribute('aria-label')));

  console.log('— feil i konsollen —');
  if (feil.length) { console.log(feil.map(f => '  ' + f).join('\n')); ok = false; }
  else console.log('  ingen');
  await page.close();
}

console.log('\n══ språkbytte ══');
{
  const { page, feil } = await nySide({ q: '?lang=nb' });
  await t('bytter til engelsk', async () => {
    await page.locator('#lang').click(); await page.waitForTimeout(500);
    return (await page.evaluate(() => document.documentElement.lang)) === 'en';
  });
  await t('URL-en følger med', async () =>
    (await page.evaluate(() => location.search)).includes('lang=en'));
  await t('kartlagene er oversatt', async () =>
    (await page.locator('.leaflet-control-layers-overlays label').first().innerText()).includes('Closed'));
  await t('valgt sektor overlever bytte', async () => {
    await page.fill('#q', 'diplodocus'); await page.waitForTimeout(250);
    await page.locator('.row').first().click(); await page.waitForTimeout(800);
    await page.locator('#lang').click(); await page.waitForTimeout(500);
    return (await page.locator('.pname').innerText()) === 'Diplodocus' &&
           nbsp(await page.locator('.picked').innerText()).includes('159 av 159');
  });
  await t('valget huskes uten ?lang i adressa', async () => {
    await page.goto(base, { waitUntil: 'networkidle' });
    return (await page.evaluate(() => document.documentElement.lang)) === 'nb';
  });
  if (feil.length) { console.log(feil.map(f => '  ' + f).join('\n')); ok = false; }
  await page.close();
}

console.log('\n══ utløpt ferdselsforbud ══');
for (const [lang, bit] of [['nb', 'Den datoen er passert'], ['en', 'That date has passed']]) {
  const { page } = await nySide({ q: '?lang=' + lang, tid: '2026-08-10T09:00:00' });
  await t(`varselet vises på ${lang}`, async () =>
    (await page.locator('#warn').isVisible()) &&
    (await page.locator('#warn').innerText()).includes(bit));
  await page.close();
}

console.log('\n══ blokktellingen ══');
{
  const { page } = await nySide();
  await t('nettleseren teller likt som tools/beregn.py', async () => {
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
  await t('alle oppføringer i loggen har begge språk', async () =>
    await page.evaluate(() => HISTORIKK.every(h => h.t && h.b && h.t_en && h.b_en)));
  await t('alle kategorier og kilder har begge språk', async () =>
    await page.evaluate(() => Object.values(CAT).every(c => c.t_en && c.d_en) &&
                              Object.values(SOURCES).every(s => s.t_en && s.d_en)));
  await page.close();
}

await browser.close();
console.log('\n' + (ok ? 'ALT OK' : 'NOE FEILET'));
process.exit(ok ? 0 : 1);
