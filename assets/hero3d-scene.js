// 귀코목 알지 — 대문 3D 탐험 지도 (three.js)
// 지오메트리는 페이지 안 SVG 지도(#map svg)에서 읽는다. 지도 모양을 고칠 때는 index.html의 SVG만 고치면 된다.
import * as THREE from 'three';
import { Line2 } from 'three/addons/lines/Line2.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { LineGeometry } from 'three/addons/lines/LineGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ---------- 부위 설정 ---------- */
const ORDER = ['ear', 'nose', 'throat'];
const CONF = {
  ear: {
    name: '귀', route: '소리와 균형의 길', deep: '#3452c0', z: 46, entry: [434, 314], pin: [478, 300],
    stops: [[418, 313, '외이도', 418, 336, 'c'], [386, 312, '고막과 중이', 384, 338, 'e'], [352, 300, '달팽이관', 340, 305, 'e'], [366, 270, '반고리관', 380, 258, 's']],
    hit: [[392, 250], [452, 252], [498, 296], [476, 384], [400, 384], [372, 336], [336, 322], [336, 276]],
    picks: ['이석증', '돌발성 난청', '이명'],
    fact: '사람이 들을 수 있는 소리 · 20–20,000 Hz'
  },
  nose: {
    name: '코', route: '숨과 냄새의 길', deep: '#0e7a5e', z: 28, entry: [134, 360], pin: [94, 312],
    stops: [[222, 338, '비강', 222, 364, 'c'], [240, 302, '부비동', 240, 280, 'c'], [343, 352, '비인두', 356, 372, 's']],
    hit: [[108, 342], [126, 300], [168, 270], [262, 272], [298, 316], [312, 346], [256, 356], [176, 358], [142, 376], [112, 366]],
    picks: ['만성 부비동염(축농증)', '알레르기 비염', '비중격만곡증'],
    fact: '하루에 코로 드나드는 공기 · 약 10,000 L'
  },
  throat: {
    name: '목', route: '목소리와 잠의 길', deep: '#a65d08', z: 18, entry: [158, 406], pin: [248, 574],
    stops: [[324, 432, '편도', 300, 440, 'e'], [314, 540, '성대', 328, 548, 's']],
    hit: [[146, 388], [210, 392], [300, 396], [348, 382], [352, 470], [334, 560], [322, 640], [268, 640], [272, 508], [196, 494], [158, 446]],
    picks: ['폐쇄성 수면무호흡', '인후두 역류', '급성 편도염'],
    fact: '말할 때 성대의 진동 · 초당 100–250회'
  }
};

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const easeOut = t => 1 - Math.pow(1 - t, 3);
const wx = x => x - 336, wy = y => -(y - 350);

export function mount(map, { forceMotion = false } = {}) {
  const svg = map.querySelector('svg');
  const tok = n => getComputedStyle(map).getPropertyValue(n).trim();
  const R = {};
  ORDER.forEach(r => { R[r] = Object.assign({ glow: tok(`--${r}-glow`) }, CONF[r]); });

  /* ---------- SVG 지도에서 모양 읽기 ---------- */
  const heads = [...svg.querySelectorAll('path.m-head')].map(p => p.getAttribute('d'));
  const inner = [...svg.querySelectorAll('path.m-inner')].map(p => p.getAttribute('d'));
  const GEO = {
    head: heads[0], earOutline: heads[1],
    contours: [...svg.querySelectorAll('.m-contour path')].map(p => p.getAttribute('d')),
    clip: svg.querySelector('#head-clip path').getAttribute('d'),
    routes: Object.fromEntries(ORDER.map(r => [r, svg.querySelector(`#route-${r}`).getAttribute('d')])),
    eardrum: inner[0], cochlea: inner[1], canals: inner[2],
    tube: svg.querySelector('path.m-tube').getAttribute('d')
  };
  const published = new Map();
  map.ownerDocument.querySelectorAll('.line .stop.open a').forEach(a => published.set(a.textContent.trim(), a.getAttribute('href')));

  const NS = 'http://www.w3.org/2000/svg';
  const sampler = document.createElementNS(NS, 'svg');
  sampler.setAttribute('width', '1'); sampler.setAttribute('height', '1');
  sampler.setAttribute('aria-hidden', 'true');
  sampler.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden';
  document.body.appendChild(sampler);
  function sample(d, step = 2.5) {
    return d.trim().split(/(?=M)/).map(sub => {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', sub); sampler.appendChild(p);
      const L = p.getTotalLength(), n = Math.max(2, Math.ceil(L / step)), pts = [];
      for (let i = 0; i <= n; i++) { const q = p.getPointAtLength(L * i / n); pts.push([q.x, q.y]); }
      p.remove();
      return pts;
    });
  }
  function inside(x, y, poly) {
    let c = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xi, yi] = poly[i], [xj, yj] = poly[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
    }
    return c;
  }

  /* ---------- DOM 덧층 ---------- */
  const glBox = document.createElement('div');
  glBox.className = 'map-gl';
  glBox.innerHTML = '<canvas aria-hidden="true"></canvas><div class="map-labels"></div>';
  map.appendChild(glBox);
  const canvas = glBox.querySelector('canvas'), labelsEl = glBox.querySelector('.map-labels');
  ORDER.forEach(r => {
    const a = document.createElement('a');
    a.className = 'map-pin'; a.dataset.r = r; a.href = `/${r}/`;
    a.setAttribute('aria-label', `${R[r].name} 탐험로로 들어가기`);
    a.innerHTML = `<b aria-hidden="true">${R[r].name}</b>`;
    labelsEl.appendChild(a); R[r].pinEl = a;
  });
  const card = document.createElement('div');
  card.className = 'map-card'; card.setAttribute('aria-hidden', 'true');
  card.innerHTML = '<p class="mc-route"></p><p class="mc-title"></p><ul></ul><p class="mc-fact"></p><p class="mc-cta"></p>';
  map.appendChild(card);
  let wipe = document.querySelector('.page-wipe');
  if (!wipe) { wipe = document.createElement('div'); wipe.className = 'page-wipe'; wipe.setAttribute('aria-hidden', 'true'); document.body.appendChild(wipe); }
  const hint = document.getElementById('map-hint');
  if (hint) hint.hidden = false;
  const picks = [...document.querySelectorAll('.routes-pick a[data-route]')];

  /* ---------- 렌더러 ---------- */
  const coarse = matchMedia('(pointer: coarse)').matches;
  const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
  let motionOn = forceMotion || !reduceMQ.matches;
  reduceMQ.addEventListener('change', () => { if (!forceMotion) motionOn = !reduceMQ.matches; });
  const lowEnd = (navigator.hardwareConcurrency || 8) <= 4;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  const DPR = Math.min(devicePixelRatio || 1, coarse ? 1.75 : 2);
  renderer.setPixelRatio(DPR);
  const STAGE = new THREE.Color(tok('--paper'));
  // 렌더 타깃을 지울 때는 출력 색공간 값이 그대로 쓰이므로 한 번 더 변환해 둔다
  renderer.setClearColor(new THREE.Color().setRGB(STAGE.r, STAGE.g, STAGE.b, THREE.SRGBColorSpace), 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 10, 5000);
  scene.add(camera);
  const root = new THREE.Group(); scene.add(root);

  const rt = new THREE.WebGLRenderTarget(2, 2, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.addPass(new RenderPass(scene, camera));
  let bloom = null;
  if (!lowEnd) { bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0.9, 0.55, 0.8); composer.addPass(bloom); }
  composer.addPass(new OutputPass());

  /* ---------- 재질 도우미 ---------- */
  const lineMats = [];
  const fadeables = [];
  function lineMat(color, width, { k = 1, opacity = 1, additive = false } = {}) {
    const m = new LineMaterial({ color, linewidth: width, transparent: true, opacity, depthTest: false, depthWrite: false });
    if (additive) m.blending = THREE.AdditiveBlending;
    m.color.multiplyScalar(k);
    lineMats.push(m);
    return m;
  }
  function polyLine(pts, z, mat) {
    const pos = [];
    for (const [x, y] of pts) pos.push(wx(x), wy(y), z);
    const g = new LineGeometry(); g.setPositions(pos);
    const l = new Line2(g, mat); l.computeLineDistances();
    l.userData.segs = pts.length - 1;
    l.renderOrder = 2;
    return l;
  }
  function track(mat, base) { fadeables.push({ mat, base }); return mat; }

  /* ---------- 바탕: 격자, 실루엣, 등고선 ---------- */
  const headPoly = sample(GEO.clip, 4)[0];
  {
    const g = new THREE.BufferGeometry(), p = [];
    for (let v = -320; v <= 320; v += 80) p.push(v, -330, 0, v, 330, 0, -330, v, 0, 330, v, 0);
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    const m = track(new THREE.LineBasicMaterial({ color: new THREE.Color(tok('--line')), transparent: true, opacity: .4, depthTest: false }), .4);
    const grid = new THREE.LineSegments(g, m); grid.position.z = -80; grid.renderOrder = 0; root.add(grid);
  }
  const fillShape = new THREE.Shape(headPoly.map(([x, y]) => new THREE.Vector2(wx(x), wy(y))));
  const fillMat = new THREE.MeshBasicMaterial({ color: new THREE.Color('#0f2033'), transparent: true, opacity: .92, depthTest: false });
  const fill = new THREE.Mesh(new THREE.ShapeGeometry(fillShape), fillMat); fill.renderOrder = 1; root.add(fill);

  const relief = new THREE.Group(); root.add(relief);
  const contours = [];
  GEO.contours.forEach((d, i) => {
    const pts = sample(d, 3)[0];
    const runs = [];
    let run = [];
    for (const p of pts) { if (inside(p[0], p[1], headPoly)) run.push(p); else { if (run.length > 4) runs.push(run); run = []; } }
    if (run.length > 4) runs.push(run);
    const t = i / Math.max(1, GEO.contours.length - 1);
    const col = new THREE.Color('#24425f').lerp(new THREE.Color('#3d6683'), t);
    const m = lineMat(col.getStyle(), 1 + t * .5, { opacity: 0 });
    const objs = runs.map(r => { const l = polyLine(r, 0, m); relief.add(l); return l; });
    contours.push({ mat: m, z: 4 + i * 7.5, i, objs });
  });

  /* ---------- 얼굴 윤곽 ---------- */
  const headMat = lineMat('#cfdde8', 2.6, { opacity: 1 });
  const headLine = polyLine(sample(GEO.head, 2)[0], 0, headMat); root.add(headLine);
  const faceMat = lineMat('#cfdde8', 1.8, { opacity: 0 });
  const face = new THREE.Group(); root.add(face); face.position.z = 26;
  ['M178 244 C190 237 206 236 222 241', 'M190 268 C198 261 210 261 219 267', 'M192 269 C200 274 210 274 218 268']
    .forEach(d => face.add(polyLine(sample(d, 2)[0], 0, faceMat)));

  /* ---------- 부위 그룹 ---------- */
  const groups = {};
  const anchors = [];
  ORDER.forEach(r => { const g = new THREE.Group(); g.position.z = R[r].z; root.add(g); groups[r] = g; R[r].mats = []; });
  function regMat(r, mat, base, route = false) { R[r].mats.push({ mat, base, route }); return mat; }

  const earOutlineMat = lineMat('#cfdde8', 2.4, { opacity: 1 });
  sample(GEO.earOutline, 2).forEach(p => groups.ear.add(polyLine(p, 0, earOutlineMat)));

  const routes = {};
  ORDER.forEach(r => {
    const pts = sample(GEO.routes[r], 2)[0];
    R[r].routePts = pts;
    const halo = regMat(r, lineMat(R[r].glow, 9, { k: .9, opacity: .16, additive: true }), .16, true);
    const core = regMat(r, lineMat(R[r].glow, 3.2, { k: 1.8, opacity: 1 }), 1, true);
    const a = polyLine(pts, 0, halo), b = polyLine(pts, 0, core);
    groups[r].add(a, b);
    routes[r] = [a, b];
  });

  // 귀 속 구조
  const earInnerMat = regMat('ear', lineMat(R.ear.glow, 1.7, { k: 1.25, opacity: 0 }), .95);
  groups.ear.add(polyLine(sample(GEO.eardrum, 1)[0], -6, earInnerMat));
  const cochlea = new THREE.Group();
  const cPts = sample(GEO.cochlea, 1)[0];
  const cc = cPts.reduce((a, p) => [a[0] + p[0] / cPts.length, a[1] + p[1] / cPts.length], [0, 0]);
  cochlea.position.set(wx(cc[0]), wy(cc[1]), -10);
  cochlea.add(polyLine(cPts.map(([x, y]) => [x - cc[0] + 336, y - cc[1] + 350]), 0, earInnerMat));
  groups.ear.add(cochlea);
  const canalMat = regMat('ear', lineMat(R.ear.glow, 1.7, { k: 1.25, opacity: 0 }), .95);
  sample(GEO.canals, 1).forEach(p => groups.ear.add(polyLine(p, -10, canalMat)));

  // 코: 부비동과 이관
  const sinusLineMat = regMat('nose', lineMat(R.nose.glow, 1.3, { opacity: 0 }), .75);
  const sinusFills = [];
  [[202, 208, 16, 24, -12], [240, 302, 30, 19, 0]].forEach(([cx, cy, rx, ry, rot]) => {
    const pts = [], a = rot * Math.PI / 180;
    for (let i = 0; i <= 64; i++) {
      const t = i / 64 * Math.PI * 2, x = Math.cos(t) * rx, y = Math.sin(t) * ry;
      pts.push([cx + x * Math.cos(a) - y * Math.sin(a), cy + x * Math.sin(a) + y * Math.cos(a)]);
    }
    groups.nose.add(polyLine(pts, -14, sinusLineMat));
    const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(R.nose.glow).multiplyScalar(.9), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthTest: false });
    const mesh = new THREE.Mesh(new THREE.CircleGeometry(1, 48), m);
    mesh.scale.set(rx, ry, 1); mesh.rotation.z = -a; mesh.position.set(wx(cx), wy(cy), -14); mesh.renderOrder = 2;
    groups.nose.add(mesh); sinusFills.push(m);
  });
  const tubeMat = regMat('nose', lineMat('#7f93a6', 1.2, { opacity: 0 }), .6);
  groups.nose.add(polyLine(sample(GEO.tube, 2)[0], 6, tubeMat));

  // 목: 성대 진동선
  const cordMat = regMat('throat', lineMat(R.throat.glow, 2.2, { k: 1.8, opacity: 0 }), 1);
  const cordN = 24;
  const cordGeo = new LineGeometry();
  const cordPos = new Float32Array((cordN + 1) * 3);
  cordGeo.setPositions(cordPos);
  const cord = new Line2(cordGeo, cordMat); cord.renderOrder = 3; groups.throat.add(cord);

  // 정류장 표시, 라벨, 핀 위치
  ORDER.forEach(r => {
    R[r].labels = [];
    const ringM = regMat(r, new THREE.MeshBasicMaterial({ color: new THREE.Color(R[r].glow).multiplyScalar(1.4), transparent: true, opacity: 0, depthTest: false }), 1);
    const dotM = regMat(r, new THREE.MeshBasicMaterial({ color: STAGE, transparent: true, opacity: 0, depthTest: false }), 1);
    R[r].stops.forEach(([x, y, name, tx, ty, al]) => {
      const ring = new THREE.Mesh(new THREE.CircleGeometry(5.6, 24), ringM);
      const dot = new THREE.Mesh(new THREE.CircleGeometry(3.4, 24), dotM);
      ring.position.set(wx(x), wy(y), 2); dot.position.set(wx(x), wy(y), 2.1);
      ring.renderOrder = 5; dot.renderOrder = 6;
      groups[r].add(ring, dot);
      const anchor = new THREE.Object3D(); anchor.position.set(wx(tx), wy(ty), 2); groups[r].add(anchor);
      const el = document.createElement('span'); el.className = 'map-lab'; el.textContent = name;
      el.setAttribute('aria-hidden', 'true');
      labelsEl.appendChild(el);
      R[r].labels.push(el);
      anchors.push({ obj: anchor, el, al });
    });
    const pa = new THREE.Object3D(); pa.position.set(wx(R[r].pin[0]), wy(R[r].pin[1]), R[r].z); root.add(pa);
    anchors.push({ obj: pa, el: R[r].pinEl, al: 'pin' });
  });

  /* ---------- 입자 흐름 ---------- */
  const flowVS = `
attribute float aSize; attribute float aAlpha;
uniform float uScale;
varying float vAlpha;
void main(){
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = aSize * uScale / -mv.z;
  vAlpha = aAlpha;
}`;
  const flowFS = `
uniform vec3 uColor; uniform float uOpacity;
varying float vAlpha;
void main(){
  float d = length(gl_PointCoord - 0.5);
  float a = smoothstep(0.5, 0.0, d);
  a = a * a;
  gl_FragColor = vec4(uColor, a * vAlpha * uOpacity);
}`;
  function makeFlow(r, count, { speed, spread, size }) {
    const src = R[r].routePts;
    const cum = [0];
    for (let i = 1; i < src.length; i++) cum.push(cum[i - 1] + Math.hypot(src[i][0] - src[i - 1][0], src[i][1] - src[i - 1][1]));
    const L = cum[cum.length - 1], N = 240, lut = [];
    for (let i = 0, j = 0; i <= N; i++) {
      const s = L * i / N;
      while (j < cum.length - 2 && cum[j + 1] < s) j++;
      const f = (s - cum[j]) / (cum[j + 1] - cum[j] || 1);
      lut.push([src[j][0] + (src[j + 1][0] - src[j][0]) * f, src[j][1] + (src[j + 1][1] - src[j][1]) * f]);
    }
    const nrm = lut.map((p, i) => {
      const a = lut[Math.max(0, i - 1)], b = lut[Math.min(N, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      return [-dy / l, dx / l];
    });
    const pos = new Float32Array(count * 3), sz = new Float32Array(count), al = new Float32Array(count);
    const seed = Array.from({ length: count }, () => ({ o: Math.random(), s: .7 + Math.random() * .6, j: Math.random() * 2 - 1, z: Math.random() * 2 - 1, w: Math.random() * 6.28, k: Math.random() }));
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(sz, 1));
    g.setAttribute('aAlpha', new THREE.BufferAttribute(al, 1));
    const m = new THREE.ShaderMaterial({
      vertexShader: flowVS, fragmentShader: flowFS, transparent: true, depthTest: false, depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: { uColor: { value: new THREE.Color(R[r].glow).multiplyScalar(2.2) }, uOpacity: { value: 0 }, uScale: { value: 1150 * DPR } }
    });
    const pts = new THREE.Points(g, m); pts.renderOrder = 7; pts.frustumCulled = false;
    groups[r].add(pts);
    let phase = 0;
    return {
      m,
      update(dt, inten, rate = 1) {
        phase += dt * speed * rate * (0.6 + inten * 0.9);
        const active = 0.35 + 0.65 * inten;
        for (let i = 0; i < count; i++) {
          const sd = seed[i];
          const u = (((sd.o + phase * sd.s) % 1) + 1) % 1;
          const fi = u * N, i0 = Math.min(N - 1, Math.floor(fi)), f = fi - i0, i1 = i0 + 1;
          const x = lut[i0][0] + (lut[i1][0] - lut[i0][0]) * f, y = lut[i0][1] + (lut[i1][1] - lut[i0][1]) * f;
          const wob = Math.sin(sd.w + phase * 9 * sd.s) * .35;
          const off = (sd.j + wob) * spread * (0.55 + 0.45 * Math.sin(u * Math.PI));
          pos[i * 3] = wx(x + nrm[i0][0] * off);
          pos[i * 3 + 1] = wy(y + nrm[i0][1] * off);
          pos[i * 3 + 2] = sd.z * spread * .8;
          const edge = smooth(0, .06, u) * (1 - smooth(.9, 1, u));
          al[i] = (sd.k < active ? 1 : 0) * edge * (.45 + .55 * sd.s);
          sz[i] = size * (.6 + sd.s * .7) * (0.85 + inten * .5);
        }
        g.attributes.position.needsUpdate = true; g.attributes.aAlpha.needsUpdate = true; g.attributes.aSize.needsUpdate = true;
      }
    };
  }
  const pScale = coarse ? .6 : 1;
  const flows = {
    nose: makeFlow('nose', Math.round(320 * pScale), { speed: .09, spread: 9, size: 7 }),
    ear: makeFlow('ear', Math.round(90 * pScale), { speed: .35, spread: 5, size: 6.5 }),
    throat: makeFlow('throat', Math.round(170 * pScale), { speed: .16, spread: 8, size: 6.5 })
  };

  /* ---------- 파동 ---------- */
  function makeWaves(r, cx, cy, a0, a1, n, inward, rMin, rMax, period) {
    const arc = [];
    for (let i = 0; i <= 28; i++) { const a = (a0 + (a1 - a0) * i / 28) * Math.PI / 180; arc.push([336 + Math.cos(a), 350 + Math.sin(a)]); }
    const list = [];
    for (let i = 0; i < n; i++) {
      const m = lineMat(R[r].glow, 2.4, { k: 1.6, opacity: 0 });
      const l = polyLine(arc, 0, m);
      l.position.set(wx(cx), wy(cy), 0); l.renderOrder = 4;
      groups[r].add(l); list.push({ l, m });
    }
    let ph = Math.random();
    return {
      update(dt, gain, rate = 1) {
        ph += dt / period * rate;
        list.forEach((w, i) => {
          const k = (ph + i / n) % 1, f = inward ? 1 - k : k;
          const rr = rMin + (rMax - rMin) * f;
          w.l.scale.set(rr, rr, 1);
          w.m.opacity = Math.sin(k * Math.PI) * .95 * gain;
        });
      }
    };
  }
  const waves = {
    ear: makeWaves('ear', 436, 314, -55, 55, 5, true, 8, 70, 2.2),
    throat: makeWaves('throat', 154, 406, 128, 232, 4, false, 10, 72, 1.9),
    nose: makeWaves('nose', 132, 360, 140, 220, 3, true, 6, 46, 2.6)
  };

  /* ---------- 히트존 ---------- */
  const hitMeshes = [];
  ORDER.forEach(r => {
    const shape = new THREE.Shape(R[r].hit.map(([x, y]) => new THREE.Vector2(wx(x), wy(y))));
    const mesh = new THREE.Mesh(new THREE.ShapeGeometry(shape), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, depthTest: false }));
    mesh.position.z = R[r].z; mesh.userData.r = r; root.add(mesh); hitMeshes.push(mesh);
  });

  /* ---------- 워프 터널(카메라 기준) ---------- */
  const warp = new THREE.Group(); camera.add(warp);
  const NST = coarse ? 170 : 300;
  const stPos = new Float32Array(NST * 6);
  const streak = Array.from({ length: NST }, () => ({ a: Math.random() * 6.28, r: 14 + Math.random() * 170, z: -60 - Math.random() * 1000, s: .6 + Math.random() * .8 }));
  const stGeo = new THREE.BufferGeometry(); stGeo.setAttribute('position', new THREE.BufferAttribute(stPos, 3));
  const stMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthTest: false });
  const streaks = new THREE.LineSegments(stGeo, stMat); streaks.frustumCulled = false; streaks.renderOrder = 20; warp.add(streaks);
  const ringArc = []; for (let i = 0; i <= 72; i++) { const a = i / 72 * Math.PI * 2; ringArc.push([336 + Math.cos(a), 350 + Math.sin(a)]); }
  const rings = Array.from({ length: 7 }, (_, i) => {
    const m = lineMat('#ffffff', 2.4, { opacity: 0, additive: true });
    const l = polyLine(ringArc, 0, m); l.renderOrder = 21; l.frustumCulled = false; warp.add(l);
    return { l, m, z: -150 - i * 140 };
  });
  warp.visible = false;
  const warpColor = new THREE.Color();
  function updateWarp(dt, inten) {
    warp.visible = inten > .01;
    if (!warp.visible) return;
    stMat.color.copy(warpColor).multiplyScalar(2.4); stMat.opacity = inten;
    for (let i = 0; i < NST; i++) {
      const s = streak[i];
      s.z += dt * 900 * s.s * (0.5 + inten * 2.2);
      if (s.z > -25) { s.z = -1060; s.a = Math.random() * 6.28; s.r = 14 + Math.random() * 170; }
      const x = Math.cos(s.a) * s.r, y = Math.sin(s.a) * s.r, len = 20 + inten * 220 * s.s;
      stPos.set([x, y, s.z, x, y, s.z - len], i * 6);
    }
    stGeo.attributes.position.needsUpdate = true;
    rings.forEach(g => {
      g.z += dt * 950 * (0.5 + inten * 2);
      if (g.z > -30) g.z -= 980;
      g.l.position.set(0, 0, g.z); g.l.scale.set(120, 120, 1);
      g.m.color.copy(warpColor).multiplyScalar(1.8);
      g.m.opacity = inten * smooth(-1000, -500, g.z) * (1 - smooth(-120, -30, g.z));
    });
  }

  /* ---------- 크기 맞춤 ---------- */
  const HOME = new THREE.Vector3(), HOME_LOOK = new THREE.Vector3(0, 0, 0);
  let W = 1, H = 1, trans = null;
  function resize() {
    const r = glBox.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
    renderer.setSize(W, H, false);
    composer.setSize(W, H);
    if (bloom) bloom.resolution.set(W / 2, H / 2);
    lineMats.forEach(m => m.resolution.set(W, H));
    camera.aspect = W / H;
    const t = Math.tan(THREE.MathUtils.degToRad(15));
    HOME.set(-4, 0, Math.max(300 / t, 290 / (t * camera.aspect)) * 1.02);
    if (!trans) resetCamera();
    camera.updateProjectionMatrix();
  }
  function resetCamera() {
    camera.position.copy(HOME); camera.fov = 30; camera.lookAt(HOME_LOOK); camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(glBox);

  /* ---------- 상호작용 ---------- */
  let hover = null, lastInteract = -1e9, busy = false;
  const pointer = new THREE.Vector2(), par = { x: 0, y: 0, tx: 0, ty: 0 };
  const ray = new THREE.Raycaster();
  const state = Object.fromEntries(ORDER.map(r => [r, { fade: 1, lift: 0, inten: 0, lab: 0 }]));
  let T = 0, last = performance.now();

  function setHover(r, via) {
    if (hover === r && via !== 'tap') return;
    hover = r;
    picks.forEach(el => el.classList.toggle('is-on', el.dataset.route === r));
    ORDER.forEach(k => R[k].pinEl.classList.toggle('is-on', k === r));
    map.classList.toggle('is-hot', !!r);
    if (r) fillCard(r, via); else card.classList.remove('on');
  }
  function fillCard(r, via) {
    card.style.setProperty('--rc', R[r].glow);
    card.querySelector('.mc-route').textContent = R[r].route;
    card.querySelector('.mc-title').textContent = R[r].name;
    card.querySelector('ul').innerHTML = R[r].picks.map(n => {
      const pub = published.has(n);
      return `<li class="${pub ? 'pub' : ''}">${n}${pub ? ' <em>읽기</em>' : ''}</li>`;
    }).join('');
    card.querySelector('.mc-fact').textContent = R[r].fact;
    card.querySelector('.mc-cta').textContent = via === 'tap' ? '한 번 더 누르면 들어갑니다' : '눌러서 들어가기 →';
    card.classList.add('on');
  }
  function pick(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    pointer.set((clientX - r.left) / r.width * 2 - 1, -(clientY - r.top) / r.height * 2 + 1);
    ray.setFromCamera(pointer, camera);
    const hit = ray.intersectObjects(hitMeshes, false)[0];
    return hit ? hit.object.userData.r : null;
  }
  const plainClick = e => !(e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button > 0);

  window.addEventListener('pointermove', e => {
    if (e.pointerType === 'touch') return;
    par.tx = (e.clientX / innerWidth) * 2 - 1;
    par.ty = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });
  canvas.addEventListener('pointermove', e => {
    if (busy || e.pointerType === 'touch') return;
    lastInteract = T;
    setHover(pick(e.clientX, e.clientY), 'mouse');
  });
  canvas.addEventListener('pointerleave', e => { if (!busy && e.pointerType !== 'touch') setHover(null); });
  canvas.addEventListener('click', e => {
    if (busy) return;
    const r = pick(e.clientX, e.clientY);
    lastInteract = T;
    if (!r) { setHover(null); return; }
    if (coarse && hover !== r) { setHover(r, 'tap'); return; }
    enter(r, e.clientX, e.clientY, `/${r}/`);
  });
  const hoverables = [...picks.map(el => [el, el.dataset.route]), ...ORDER.map(r => [R[r].pinEl, r])];
  hoverables.forEach(([el, r]) => {
    el.addEventListener('pointerenter', e => { if (!busy && e.pointerType !== 'touch') { lastInteract = T; setHover(r, 'mouse'); } });
    el.addEventListener('pointerleave', e => { if (!busy && e.pointerType !== 'touch') setHover(null); });
    el.addEventListener('focus', () => { if (!busy) { lastInteract = T; setHover(r, 'key'); } });
    el.addEventListener('blur', () => { if (!busy) setHover(null); });
    el.addEventListener('click', e => {
      if (!plainClick(e)) return;
      e.preventDefault();
      const b = el.getBoundingClientRect();
      enter(r, b.left + b.width / 2, b.top + b.height / 2, el.getAttribute('href'));
    });
  });

  /* ---------- 클릭 전환 ---------- */
  const timers = [];
  function enter(r, x, y, href) {
    if (busy) return;
    busy = true;
    setHover(r, 'mouse');
    card.classList.remove('on');
    wipe.style.setProperty('--x', x + 'px');
    wipe.style.setProperty('--y', y + 'px');
    wipe.style.setProperty('--wc', R[r].deep);
    wipe.classList.remove('go');
    const go = () => {
      try { sessionStorage.setItem('entrg-arrive', r); } catch (e) {}
      location.href = href;
    };
    if (!motionOn) {
      wipe.classList.add('go');
      timers.push(setTimeout(go, 480));
      return;
    }
    const [ex, ey] = R[r].entry;
    const e = new THREE.Vector3(wx(ex), wy(ey), R[r].z + state[r].lift);
    root.localToWorld(e);
    warpColor.set(R[r].glow);
    trans = { r, t0: performance.now(), entry: e, end: e.clone().add(new THREE.Vector3(0, 0, 34)), from: camera.position.clone() };
    timers.push(setTimeout(() => wipe.classList.add('go'), 560));
    timers.push(setTimeout(go, 1040));
  }
  // 허브에서 뒤로 왔을 때(bfcache) 장면을 원래대로
  window.addEventListener('pageshow', e => {
    if (!e.persisted) return;
    timers.splice(0).forEach(clearTimeout);
    trans = null; busy = false;
    wipe.classList.remove('go');
    setHover(null);
    resetCamera();
    updateWarp(0, 0);
    T = motionOn ? 0.6 : T;
    lastInteract = -1e9;
    last = performance.now();
  });

  /* ---------- 프레임 ---------- */
  const tmp = new THREE.Vector3();
  const pinEls = ORDER.map(r => R[r].pinEl);
  let relFade = 1, running = true, raf = 0, firstFrame = true;
  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = clamp((now - last) / 1000, 0, .05); last = now;
    if (motionOn) T += dt;
    const I = motionOn ? T : 99;
    const k = motionOn ? 1 - Math.exp(-dt * 7) : 1;
    const TP = trans ? clamp((now - trans.t0) / 850) : 0;

    // 등장
    contours.forEach(c => {
      const p = easeOut(smooth(.1 + c.i * .07, 1.0 + c.i * .07, I));
      c.objs.forEach(o => { o.position.z = c.z * p; });
      const sweep = motionOn ? .62 + .38 * Math.max(0, Math.sin(T * 1.3 - c.i * .55)) : .85;
      c.mat.opacity = p * sweep * relFade;
    });
    headLine.geometry.instanceCount = Math.floor(headLine.userData.segs * easeOut(smooth(0, 1.5, I)));
    const tAll = trans ? 1 - smooth(0, .5, TP) : 1;
    faceMat.opacity = smooth(1.1, 1.8, I) * .8 * tAll;
    const routeP = { ear: smooth(1.4, 2.2, I), nose: smooth(1.7, 2.9, I), throat: smooth(2.0, 3.0, I) };
    ORDER.forEach(r => routes[r].forEach(l => { l.geometry.instanceCount = Math.floor(l.userData.segs * routeP[r]); }));
    const detail = smooth(1.3, 2.2, I), live = smooth(2.3, 3.2, I);
    if (I > 2.1) R.ear.pinEl.classList.add('show');
    if (I > 2.4) R.nose.pinEl.classList.add('show');
    if (I > 2.7) R.throat.pinEl.classList.add('show');

    // 초점: 사용자 > 자동 투어
    const touring = motionOn && !hover && !busy && T > 3.6 && T - lastInteract > 5;
    const tour = touring ? ORDER[Math.floor((T - 3.6) / 3.2) % 3] : null;
    const act = trans ? trans.r : (hover || tour);
    const strong = !!(trans || hover);
    ORDER.forEach(r => {
      const s = state[r], on = act === r;
      const tf = act ? (on ? 1 : (strong ? .12 : .42)) : 1;
      const tl = on ? (strong ? 44 : 20) : 0;
      const ti = on ? (strong ? 1 : .7) : 0;
      s.fade += (tf - s.fade) * k; s.lift += (tl - s.lift) * k; s.inten += (ti - s.inten) * k;
      s.lab += ((on ? 1 : 0) - s.lab) * k;
      groups[r].position.z = R[r].z + s.lift;
      const tFade = trans && trans.r !== r ? 1 - smooth(0, .45, TP) : 1;
      R[r].mats.forEach(({ mat, base, route }) => { mat.opacity = base * s.fade * tFade * (route ? 1 : detail); });
      R[r].labels.forEach(el => el.classList.toggle('on', s.lab > .5 && I > 3 && !trans));
    });
    const relTarget = act ? (strong ? .55 : .85) : 1;
    relFade += (relTarget - relFade) * k;
    fadeables.forEach(({ mat, base }) => { mat.opacity = base * relFade; });
    headMat.opacity = tAll; earOutlineMat.opacity = tAll; fillMat.opacity = .92 * relFade * tAll;

    // 부위별 움직임
    const breath = .5 + .5 * Math.sin(T * Math.PI * 2 / 4.2);
    const sE = state.ear, sN = state.nose, sT = state.throat;
    const fEar = sE.fade * live, fNose = sN.fade * live, fThr = sT.fade * live;
    flows.nose.m.uniforms.uOpacity.value = fNose;
    flows.ear.m.uniforms.uOpacity.value = fEar;
    flows.throat.m.uniforms.uOpacity.value = fThr;
    if (motionOn) {
      flows.nose.update(dt, sN.inten, .55 + breath * 1.1);
      flows.ear.update(dt, sE.inten);
      flows.throat.update(dt, sT.inten);
      waves.ear.update(dt, fEar * (.45 + .55 * sE.inten), 1 + sE.inten * .8);
      waves.throat.update(dt, fThr * (.4 + .6 * sT.inten), 1 + sT.inten * .7);
      waves.nose.update(dt, fNose * (.35 + .65 * sN.inten) * (.3 + .7 * breath), 1 + sN.inten * .5);
      cochlea.rotation.z -= dt * (.5 + sE.inten * 3.2);
    } else if (firstFrame) {
      ORDER.forEach(r => flows[r].update(0, 0));
      ORDER.forEach(r => waves[r].update(0, 0));
    }
    canalMat.opacity *= .65 + .35 * Math.sin(T * 3.1) * sE.inten + .35 * sE.inten;
    sinusFills.forEach((m, i) => { m.opacity = sN.fade * detail * (.05 + .32 * sN.inten) * (.35 + .65 * (motionOn ? breath : 1)) * (i ? 1 : .8); });
    const amp = motionOn ? (.6 + 3.6 * sT.inten) : 0;
    for (let i = 0; i <= cordN; i++) {
      const u = i / cordN;
      cordPos[i * 3] = wx(298 + u * 32);
      cordPos[i * 3 + 1] = wy(540 + Math.sin(u * Math.PI) * amp * Math.sin(T * 42 + u * .6));
      cordPos[i * 3 + 2] = 3;
    }
    const ib = cordGeo.attributes.instanceStart.data;
    for (let i = 0; i < cordN; i++) ib.array.set(cordPos.subarray(i * 3, i * 3 + 6), i * 6);
    ib.needsUpdate = true;

    // 시차 기울기
    if (!trans) {
      const tx = motionOn ? (coarse ? Math.sin(T * .35) * .6 : par.tx) : 0;
      const ty = motionOn ? (coarse ? Math.sin(T * .27) * .3 : par.ty) : 0;
      const pk = motionOn ? 1 - Math.exp(-dt * 3) : 1;
      par.x += (tx - par.x) * pk; par.y += (ty - par.y) * pk;
      root.rotation.y = par.x * .14;
      root.rotation.x = par.y * .08;
      relief.scale.z = motionOn ? 1 + .06 * Math.sin(T * Math.PI * 2 / 5.5) : 1;
    }

    // 클릭 전환: 카메라 돌진 + 워프
    let warpI = 0;
    if (trans) {
      const e = TP * TP * TP;
      camera.position.lerpVectors(trans.from, trans.end, e);
      tmp.lerpVectors(HOME_LOOK, trans.entry, Math.min(1, easeOut(TP) * 1.15));
      camera.lookAt(tmp);
      camera.fov = 30 + 52 * e; camera.updateProjectionMatrix();
      root.rotation.y *= .9; root.rotation.x *= .9;
      warpI = smooth(.12, .75, TP);
      if (bloom) bloom.strength = .9 + warpI * 1.1;
    } else if (bloom) bloom.strength = .9;
    updateWarp(dt, warpI);

    // HTML 라벨·핀 위치
    anchors.forEach(a => {
      a.obj.getWorldPosition(tmp); tmp.project(camera);
      const x = (tmp.x + 1) / 2 * W, y = (1 - tmp.y) / 2 * H;
      if (a.al === 'pin') { a.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`; return; }
      const ox = a.al === 'e' ? '-100%' : a.al === 'c' ? '-50%' : '0%';
      a.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(${ox}, -75%)`;
    });
    pinEls.forEach(p => { p.style.opacity = trans ? '0' : ''; });

    composer.render(dt);
    if (firstFrame) {
      firstFrame = false;
      map.classList.add('is-3d');
      if (!motionOn) map.classList.add('is-still');
    }
  }
  function setRunning(v) {
    if (v === running) return;
    running = v;
    if (v) { last = performance.now(); raf = requestAnimationFrame(frame); } else cancelAnimationFrame(raf);
  }
  resize();
  raf = requestAnimationFrame(frame);
  if ('IntersectionObserver' in window) new IntersectionObserver(es => setRunning(es[0].isIntersecting && !document.hidden)).observe(map);
  document.addEventListener('visibilitychange', () => setRunning(!document.hidden));
}
