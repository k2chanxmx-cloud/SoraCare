const $ = (id) => document.getElementById(id);
let currentLocation = localStorage.getItem('soracare-location') || 'koto';
let requestSerial = 0;

function setText(id, value){ $(id).textContent = value; }
function riskClass(element, className){ element.className = className || ''; }
function cacheKey(location){ return `soracare-weather-${location}`; }

function saveLocalWeather(location, data){
  try { localStorage.setItem(cacheKey(location), JSON.stringify({savedAt: Date.now(), data})); } catch(_e) {}
}

function readLocalWeather(location){
  try {
    const cached = JSON.parse(localStorage.getItem(cacheKey(location)) || 'null');
    return cached && cached.data ? cached : null;
  } catch(_e) { return null; }
}

function showCachedWeather(location){
  const cached = readLocalWeather(location);
  if(!cached) return false;
  render(cached.data);
  const minutes = Math.max(1, Math.round((Date.now() - cached.savedAt) / 60000));
  setText('updatedAt', `${cached.data.updated_at} 更新・端末保存 ${minutes}分前`);
  $('content').classList.remove('hidden');
  $('loading').classList.add('hidden');
  return true;
}

async function fetchJson(url, timeoutMs = 9000){
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {signal: controller.signal, cache: 'no-store'});
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || '取得に失敗しました');
    return data;
  } finally { clearTimeout(timer); }
}

async function loadWeather(location = currentLocation, force = false){
  const serial = ++requestSerial;
  currentLocation = location;
  localStorage.setItem('soracare-location', location);
  document.querySelectorAll('.location-tab').forEach(b=>b.classList.toggle('active', b.dataset.location===location));
  $('error').classList.add('hidden');

  const hadCache = !force && showCachedWeather(location);
  if(!hadCache){
    $('loading').textContent = '空の様子を確認しています…';
    $('loading').classList.remove('hidden');
  } else {
    $('refreshBtn').classList.add('spinning');
  }

  try{
    const data = await fetchJson(`/api/weather/${location}`, 10000);
    if(serial !== requestSerial || location !== currentLocation) return;
    render(data);
    saveLocalWeather(location, data);
    $('content').classList.remove('hidden');
    loadSummary(location, serial);
  }catch(e){
    if(serial !== requestSerial) return;
    if(!hadCache){
      $('error').textContent = e.name === 'AbortError'
        ? '取得に時間がかかっています。少し待ってから再読み込みしてください。'
        : e.message;
      $('error').classList.remove('hidden');
    }
  }finally{
    if(serial === requestSerial){
      $('loading').classList.add('hidden');
      $('refreshBtn').classList.remove('spinning');
    }
  }
}

async function loadSummary(location, serial){
  const existing = readLocalWeather(location)?.data?.summary;
  if(!existing) setText('summary', '今日の総括を読み込んでいます…');
  try{
    const data = await fetchJson(`/api/summary/${location}`, 15000);
    if(serial === requestSerial && location === currentLocation && data.summary){
      setText('summary', data.summary);
      const cached = readLocalWeather(location);
      if(cached?.data){ cached.data.summary = data.summary; saveLocalWeather(location, cached.data); }
    }
  }catch(_e){ /* 天気本体は表示したまま */ }
}

function render(d){
  setText('locationName', `${d.location.icon} ${d.location.name}`); setText('updatedAt', `${d.updated_at} 更新`);
  setText('weatherIcon', d.current.icon); setText('temperature', `${d.current.temperature}°`); setText('weatherLabel', d.current.weather);
  setText('feelsLike', `体感 ${d.current.apparent}℃`); setText('highLow', `${d.daily.max}° / ${d.daily.min}°`);
  setText('humidity', `${d.current.humidity}%`); setText('rain', `${d.daily.rain_max}%`); setText('wind', `${d.current.wind}m/s`);
  setText('uv', d.daily.uv_max); setText('sunset', d.daily.sunset); setText('pressure', `${d.current.pressure} hPa`);
  setText('pressureStatus', `${d.pressure_status.arrow} ${d.pressure_status.label}（3時間 ${d.pressure_status.delta3h > 0 ? '+' : ''}${d.pressure_status.delta3h}）`);
  riskClass($('pressure'), d.pressure_status.class); setText('heatLevel', d.heat.label); riskClass($('heatLevel'), d.heat.class);
  setText('heatAdvice', d.heat.advice); setText('heatshock', d.heatshock.label); riskClass($('heatshock'), d.heatshock.class);
  setText('summary', d.summary || '今日の総括を読み込んでいます…'); setText('source', `天気・気圧: Open-Meteo / 暑さ: 環境省WBGT基準`);
  $('hourly').innerHTML = d.hours.map(h=>`<div class="hour"><div class="time">${h.time}</div><div class="icon">${h.icon}</div><div class="temp">${h.temperature}℃</div><div class="rain">☔ ${h.rain}%</div><div class="press">${h.pressure}hPa</div></div>`).join('');
}

document.querySelectorAll('.location-tab').forEach(b=>b.addEventListener('click',()=>loadWeather(b.dataset.location)));
$('refreshBtn').addEventListener('click',()=>loadWeather(currentLocation, true));

if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/service-worker.js').catch(()=>{});
}

showCachedWeather(currentLocation);
loadWeather(currentLocation);
