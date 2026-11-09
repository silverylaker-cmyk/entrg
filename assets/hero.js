// 귀코목 알지 — 대문 탐험 지도
(function () {
  var map = document.getElementById("map");
  if (!map) return;
  var svg = map.querySelector("svg");
  var NS = "http://www.w3.org/2000/svg";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 경로 강조: 버튼에 마우스·포커스가 가면 해당 길만 보이게
  document.querySelectorAll("[data-route]").forEach(function (a) {
    var r = a.getAttribute("data-route");
    function on() { map.setAttribute("data-focus", r); }
    function off() { map.removeAttribute("data-focus"); }
    a.addEventListener("mouseenter", on);
    a.addEventListener("focus", on);
    a.addEventListener("mouseleave", off);
    a.addEventListener("blur", off);
  });

  if (reduce) return;

  // 등장 연출 한 번
  map.classList.add("is-armed");
  requestAnimationFrame(function () {
    requestAnimationFrame(function () { map.classList.add("is-ready"); });
  });

  // 파동: 귀로 모여드는 소리, 입에서 퍼지는 목소리, 콧구멍으로 들어오는 숨
  function arc(cx, cy, r, from, to) {
    var a0 = from * Math.PI / 180, a1 = to * Math.PI / 180;
    var x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    var x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    return "M" + x0.toFixed(1) + " " + y0.toFixed(1) + " A" + r + " " + r + " 0 0 1 " + x1.toFixed(1) + " " + y1.toFixed(1);
  }
  function makeWaves(sel, cls, cx, cy, from, to, n) {
    var g = svg.querySelector(sel);
    var list = [];
    for (var i = 0; i < n; i++) {
      var p = document.createElementNS(NS, "path");
      p.setAttribute("class", "m-wave " + cls);
      g.appendChild(p);
      list.push(p);
    }
    return { cx: cx, cy: cy, from: from, to: to, paths: list };
  }
  var earWaves = makeWaves(".m-waves-ear", "ear", 436, 314, -50, 50, 3);
  var voiceWaves = makeWaves(".m-waves-throat", "throat", 156, 406, 130, 230, 3);
  var breath = makeWaves(".m-breath", "nose", 136, 360, 140, 220, 3);

  function drawWaves(w, t, inward, rMin, rMax) {
    var n = w.paths.length;
    for (var i = 0; i < n; i++) {
      var k = ((t + i / n) % 1);
      var f = inward ? 1 - k : k;
      var r = rMin + (rMax - rMin) * f;
      var o = Math.sin(k * Math.PI) * 0.85;
      w.paths[i].setAttribute("d", arc(w.cx, w.cy, r, w.from, w.to));
      w.paths[i].style.opacity = o.toFixed(2);
    }
  }

  // 여행자: 각 길을 따라 움직이는 점
  var travelers = [].map.call(svg.querySelectorAll(".m-traveler"), function (c) {
    var path = svg.getElementById(c.getAttribute("data-for"));
    return { el: c, path: path, len: path.getTotalLength() };
  });
  var plan = {
    "route-nose": { dur: 4200, gap: 1400, start: 3600 },
    "route-ear": { dur: 1700, gap: 3000, start: 3200 },
    "route-throat": { dur: 2600, gap: 2400, start: 4300 }
  };
  function ease(x) { return x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; }

  var running = true, t0 = null;
  function frame(now) {
    if (!running) return;
    if (t0 === null) t0 = now;
    var t = now - t0;
    travelers.forEach(function (tr) {
      var p = plan[tr.path.id];
      var local = t - p.start;
      if (local < 0) { tr.el.style.opacity = 0; return; }
      var cyc = p.dur + p.gap;
      var u = (local % cyc) / p.dur;
      if (u > 1) { tr.el.style.opacity = 0; return; }
      var pt = tr.path.getPointAtLength(ease(u) * tr.len);
      tr.el.setAttribute("cx", pt.x.toFixed(1));
      tr.el.setAttribute("cy", pt.y.toFixed(1));
      tr.el.style.opacity = u < .08 ? u / .08 : (u > .92 ? (1 - u) / .08 : 1);
    });
    if (t > 2600) {
      drawWaves(earWaves, t / 2200, true, 6, 34);
      drawWaves(voiceWaves, t / 2000, false, 8, 40);
      drawWaves(breath, t / 1800, true, 6, 36);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // 화면 밖이거나 탭이 숨겨지면 멈춤
  function setRunning(v) {
    if (v === running) return;
    running = v;
    if (v) { requestAnimationFrame(function (now) { t0 = now - 6000; frame(now); }); }
  }
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (e) { setRunning(e[0].isIntersecting && !document.hidden); }).observe(map);
  }
  document.addEventListener("visibilitychange", function () { setRunning(!document.hidden); });
})();
