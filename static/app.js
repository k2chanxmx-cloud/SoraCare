const $ = (id) => document.getElementById(id);
let currentLocation = localStorage.getItem('soracare-location') || 'koto';

function setText(id, value){ $(id).textContent = value; }
function riskClass(element, className){ element.className = className || ''; }

async function loadWeather(location = currentLocation){
  currentLocation = location; localStorage.setItem('soracare-location', location);
  document.querySelectorAll('.location-tab').forEach(b=>b.classList.toggle('active', b.dataset.location===location));
  $('loading').classList.remove('hidden'); $('content').classList.add('hidden'); $('error').classList.add('hidden');
  try{
    const res = await fetch(`/api/weather/${location}`); const data = await res.json();
    if(!res.ok) throw new Error(data.error || '取得に失敗しました');
    render(data);
    $('content').classList.remove('hidden');
    loadSummary(location);
  }catch(e){ $('error').textContent=e.message; $('error').classList.remove('hidden'); }
  finally{$('loading').classList.add('hidden');}
}

async function loadSummary(location){
  setText('summary', 'AIが今日の総括を作成しています…');
  try{
    const res = await fetch(`/api/summary/${location}`);
    const data = await res.json();
    if(location === currentLocation && data.summary) setText('summary', data.summary);
  }catch(_e){
    // 天気本体は表示済みなので、AI失敗時も画面を止めない
  }
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
  setText('summary', d.summary); setText('source', `気圧データ: ${d.pressure_source}`);
  $('hourly').innerHTML = d.hours.map(h=>`<div class="hour"><div class="time">${h.time}</div><div class="icon">${h.icon}</div><div class="temp">${h.temperature}℃</div><div class="rain">☔ ${h.rain}%</div><div class="press">${h.pressure}hPa</div></div>`).join('');
}

document.querySelectorAll('.location-tab').forEach(b=>b.addEventListener('click',()=>loadWeather(b.dataset.location)));
$('refreshBtn').addEventListener('click',()=>loadWeather());

if('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js');
loadWeather(currentLocation);
