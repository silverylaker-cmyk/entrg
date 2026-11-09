// 귀코목 알지 — 대문 3D 지도 로더
// 조건이 맞을 때만 three.js 장면을 불러온다. 맞지 않으면 SVG 지도(hero.js)가 그대로 남는다.
//  - WebGL을 쓸 수 없으면: 불러오지 않음
//  - '동작 줄이기'가 켜져 있으면: 불러오지 않고 "3D 지도 보기" 버튼만 보여 줌
//  - 데이터 절약 모드면: 불러오지 않음
const map = document.getElementById('map');
const KEY = 'entrg-3d';
const SCENE = '/assets/hero3d-scene.js?v=20261109a';

function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}
function optedIn() {
  try { return localStorage.getItem(KEY) === 'on'; } catch (e) { return false; }
}

async function start(forceMotion) {
  try {
    const mod = await import(SCENE);
    mod.mount(map, { forceMotion });
  } catch (e) {
    map.classList.remove('is-3d');
    console.warn('3D 지도를 불러오지 못해 기본 지도를 표시합니다.', e);
  }
}

if (map && hasWebGL() && !(navigator.connection && navigator.connection.saveData)) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const btn = document.getElementById('map-3d-on');
  if (!reduce || optedIn()) {
    start(reduce);
  } else if (btn) {
    btn.hidden = false;
    btn.addEventListener('click', () => {
      try { localStorage.setItem(KEY, 'on'); } catch (e) {}
      btn.hidden = true;
      start(true);
    });
  }
}
