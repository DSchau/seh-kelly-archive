const G = window.SEH;
const PH = id => `data/garments/${id}/`;

const $ = s => document.querySelector(s);
const uniq = f => [...new Set(G.map(f).filter(Boolean))].sort();

for (const c of uniq(g => g.category)) $('#cat').insertAdjacentHTML('beforeend', `<option>${c}</option>`);
const mats = [...new Set(G.flatMap(g => g.materials))].sort();
for (const m of mats) $('#mat').insertAdjacentHTML('beforeend', `<option>${m}</option>`);
const years = [...new Set(G.map(g => g.release_date ? g.release_date.slice(0,4) : (g.first_seen||'').slice(0,4))).values()].sort();
for (const y of years) $('#year').insertAdjacentHTML('beforeend', `<option>${y}</option>`);

function yearOf(g){ return g.release_date ? g.release_date.slice(0,4) : (g.first_seen||'').slice(0,4); }

function render(){
  const q = $('#q').value.trim().toLowerCase();
  const cat = $('#cat').value, mat = $('#mat').value, yr = $('#year').value, st = $('#status').value;
  const list = G.filter(g => {
    if (cat && g.category !== cat) return false;
    if (st && g.status !== st) return false;
    if (yr && yearOf(g) !== yr) return false;
    if (mat && !g.materials.includes(mat)) return false;
    if (q && !(g.name + ' ' + (g.fabric||'') + ' ' + (g.colour||'') + ' ' + (g.description||'')).toLowerCase().includes(q)) return false;
    return true;
  });
  $('#count').textContent = `${list.length} of ${G.length} garments - ${list.reduce((a,g)=>a+g.photos.length,0)} photos`;
  $('#grid').innerHTML = list.map(g => {
    const thumb = g.photos.length ? `<img loading="lazy" src="${PH(g.id)}${g.photos[0].file}" alt="">` : `<div class="nophoto">no photo survived</div>`;
    return `<div class="card" data-id="${g.id}">${thumb}<div class="info"><div class="name">${g.name}</div>
      <div class="sub2">${g.category||''} - ${g.season||yearOf(g)||''}<span class="badge">${g.photos.length} photos</span>${g.status==='in production'?'<span class="badge">current</span>':''}</div></div></div>`;
  }).join('');
  document.querySelectorAll('.card').forEach(c => c.onclick = () => { location.hash = '/garment/' + c.dataset.id; });
}

function showGarment(id){
  const g = G.find(x => x.id === id);
  if (!g) { location.hash = ''; return; }
  $('#photos').innerHTML = g.photos.map(p => `<img loading="lazy" src="${PH(g.id)}${p.file}" title="${p.author?p.author+', ':''}${p.date||''}">`).join('') || '<p>No photos survived for this one.</p>';
  const row = (k,v) => v ? `<dt>${k}</dt><dd>${v}</dd>` : '';
  $('#meta').innerHTML = `<h2>${g.name}</h2><dl>
    ${row('Category', g.category)}${row('Fabric', g.fabric)}${row('Colour', g.colour)}
    ${row('Materials', g.materials.join(', '))}${row('Release', (g.release_date||'') + (g.release_estimate?' (first sighted in thread)':''))}
    ${row('Season', g.season)}${row('Price', g.price_gbp ? '£'+g.price_gbp : '')}${row('Sizes', (g.sizes||[]).join(', '))}
    ${row('Status', g.status)}${row('Thread mentions', g.mention_count || '')}
    ${row('First seen', g.first_seen)}${row('Last seen', g.last_seen)}
  </dl>
  ${g.description ? `<p class="desc">${g.description}</p>` : ''}
  <p>${g.product_url ? `<a href="${g.product_url}">${g.product_url}</a>` : ''}</p>
  <p><a href="https://www.styleforum.net/threads/s-e-h-kelly.277070/">Styleforum thread</a></p>`;
  document.title = `${g.name} - S.E.H Kelly archive`;
  $('header').classList.add('hidden');
  $('#grid').classList.add('hidden');
  $('#detail-page').classList.remove('hidden');
  window.scrollTo(0, 0);
}

function showGallery(){
  document.title = 'S.E.H Kelly archive';
  $('#detail-page').classList.add('hidden');
  $('header').classList.remove('hidden');
  $('#grid').classList.remove('hidden');
}

function route(){
  const m = location.hash.match(/^#\/garment\/(.+)$/);
  if (m) showGarment(decodeURIComponent(m[1])); else showGallery();
}

$('#back').onclick = () => { if (history.length > 1) history.back(); else location.hash = ''; };
window.addEventListener('hashchange', route);
for (const id of ['#q','#cat','#mat','#year','#status']) $(id).oninput = render;
render();
route();
