// 귀코목 알지 — 대문: 검색, 예시 문구, 오늘의 상식
(function () {
  "use strict";
  var REGION = { ear: "귀", nose: "코", throat: "목" };
  var TYPE = { d: "질환", s: "증상", f: "상식", h: "부위" };
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ---------- 검색 ---------- */
  var form = document.getElementById("search");
  if (form) {
    var input = form.querySelector("input");
    var box = document.getElementById("search-results");
    var status = document.getElementById("search-status");
    var data = null, loading = null, links = [], active = -1;

    var norm = function (s) { return String(s || "").toLowerCase().replace(/[\s·,.()\/\-?!~'"]/g, ""); };
    // "어지러워요" → "어지러" 처럼 흔한 말끝을 떼어 낸다
    var stem = function (q) { return q.replace(/(이에요|예요|해요|워요|와요|어요|아요|나요|네요|대요|요|다)$/, ""); };
    var grams = function (s) { var g = {}, n = 0; for (var i = 0; i < s.length - 1; i++) { if (!g[s.substr(i, 2)]) { g[s.substr(i, 2)] = 1; n++; } } g._n = n; return g; };

    function prep(j) {
      return j.items.map(function (it) {
        var all = [it.name].concat(it.alt || [], it.sym || [], [it.desc || ""]);
        if (it.links) it.links.forEach(function (l) { all.push(l.name); });
        it._n = norm(it.name); it._a = norm((it.alt || []).join("|"));
        it._s = norm((it.sym || []).join("|")); it._b = norm(it.desc);
        it._g = grams(norm(all.join("")));
        return it;
      });
    }
    function load() {
      if (data) return Promise.resolve(data);
      if (loading) return loading;
      var inline = document.getElementById("search-data");
      if (inline) { data = prep(JSON.parse(inline.textContent)); return Promise.resolve(data); }
      loading = fetch(form.getAttribute("data-index")).then(function (r) { return r.json(); })
        .then(function (j) { data = prep(j); return data; })
        .catch(function () { loading = null; return null; });
      return loading;
    }
    function score(it, q, qs, qg) {
      var s = 0;
      if (it._n === q) s = 100;
      else if (it._n.indexOf(q) === 0) s = 90;
      else if (it._n.indexOf(q) > -1 || (qs.length > 1 && it._n.indexOf(qs) > -1)) s = 80;
      else if (qs && it._a.indexOf(qs) > -1) s = 70;
      else if (qs && it._s.indexOf(qs) > -1) s = 55;
      else if (qs.length > 1 && it._b.indexOf(qs) > -1) s = 35;
      else if (qg._n) {
        var hit = 0;
        for (var k in qg) if (k !== "_n" && it._g[k]) hit++;
        var r = hit / qg._n;
        if (r >= 0.5 && (hit >= 2 || r === 1)) s = 25 * r;
      }
      if (s && it.t === "d") s += 3;
      if (s && it.t === "h" && q.length > 1) s -= 20;
      return s;
    }
    function mark(text, raw) {
      var j = raw ? text.toLowerCase().indexOf(raw.toLowerCase()) : -1;
      if (j < 0) return esc(text);
      return esc(text.slice(0, j)) + "<mark>" + esc(text.slice(j, j + raw.length)) + "</mark>" + esc(text.slice(j + raw.length));
    }
    function row(url, name, meta, desc, region, raw) {
      return '<a class="sr-item c-' + region + '" href="' + esc(url) + '"><span class="sr-name">' + mark(name, raw) +
        "</span>" + (meta ? '<span class="sr-meta">' + esc(meta) + "</span>" : "") +
        (desc ? '<span class="sr-desc">' + esc(desc) + "</span>" : "") + "</a>";
    }
    function render(list, raw) {
      var html = "", n = 0, seen = {};
      list.forEach(function (x) {
        var it = x.it;
        if (n >= 8) return;
        if (it.t === "s") {
          var sub = it.links.filter(function (l) { return !seen[l.url]; }).slice(0, 3);
          if (!sub.length) return;
          html += '<p class="sr-q c-' + it.r + '">증상 · ' + esc(it.name) + "</p>";
          sub.forEach(function (l) { seen[l.url] = 1; n++; html += row(l.url, l.name, "", l.desc, it.r, ""); });
        } else {
          if (seen[it.url]) return;
          seen[it.url] = 1; n++;
          var meta = it.t === "d" ? REGION[it.r] + " · 질환" : TYPE[it.t];
          var desc = it.t === "f" ? it.desc.split(". ")[0] + "." : it.desc;
          html += row(it.url, it.name, meta, desc, it.r, raw);
        }
      });
      if (!n) {
        html = '<p class="sr-empty">찾는 결과가 없습니다. 다른 말로 찾아보거나 <a href="/ear/">귀</a> · <a href="/nose/">코</a> · <a href="/throat/">목</a>에서 찾아보세요.</p>';
      }
      box.innerHTML = html;
      box.hidden = false;
      input.setAttribute("aria-expanded", "true");
      links = [].slice.call(box.querySelectorAll("a.sr-item"));
      active = -1;
      status.textContent = n ? "결과 " + n + "개" : "결과 없음";
    }
    function close() {
      box.hidden = true; input.setAttribute("aria-expanded", "false"); active = -1;
    }
    function run() {
      var raw = input.value.trim();
      if (!raw) { close(); return; }
      load().then(function (d) {
        if (!d || input.value.trim() !== raw) return;
        var q = norm(raw), qs = stem(q), qg = grams(qs.length > 1 ? qs : q);
        var list = d.map(function (it) { return { it: it, s: score(it, q, qs, qg) }; })
          .filter(function (x) { return x.s > 0; })
          .sort(function (a, b) { return b.s - a.s; });
        // 확실한 결과가 있으면 글자 조각만 겹치는 약한 결과는 뺀다
        if (list.length && list[0].s >= 35) list = list.filter(function (x) { return x.s >= 30; });
        render(list, raw);
      });
    }
    function setActive(i) {
      if (!links.length) return;
      if (active > -1) links[active].classList.remove("is-active");
      active = (i + links.length) % links.length;
      links[active].classList.add("is-active");
      links[active].scrollIntoView({ block: "nearest" });
    }

    input.setAttribute("role", "combobox");
    input.setAttribute("aria-expanded", "false");
    input.addEventListener("focus", load, { once: true });
    input.addEventListener("input", run);
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); if (box.hidden) run(); else setActive(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive(active - 1); }
      else if (e.key === "Escape") { close(); }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var target = links[active > -1 ? active : 0];
      if (target) { window.location.href = target.href; return; }
      run();
    });
    document.addEventListener("click", function (e) { if (!form.contains(e.target)) close(); });

    // 주소에 ?q= 가 있으면 바로 찾기
    var m = /[?&]q=([^&]+)/.exec(window.location.search);
    if (m) { input.value = decodeURIComponent(m[1].replace(/\+/g, " ")); run(); }

    // 입력 전에는 예시 문구를 한 글자씩 보여 준다
    var examples = (input.getAttribute("data-examples") || "").split("|").filter(Boolean);
    var basePh = input.getAttribute("placeholder");
    if (examples.length && !reduce) {
      var ei = 0, ci = 0, del = false, timer = null;
      var tick = function () {
        if (document.activeElement === input || input.value) { input.setAttribute("placeholder", basePh); timer = null; return; }
        var w = examples[ei];
        ci += del ? -1 : 1;
        input.setAttribute("placeholder", w.slice(0, ci) + (del ? "" : "│"));
        var wait = del ? 45 : 110;
        if (!del && ci === w.length) { del = true; wait = 1600; }
        else if (del && ci === 0) { del = false; ei = (ei + 1) % examples.length; wait = 400; }
        timer = setTimeout(tick, wait);
      };
      var start = function () { if (!timer && !input.value) timer = setTimeout(tick, 900); };
      input.addEventListener("blur", start);
      start();
    }
  }

  /* ---------- 오늘의 상식 ---------- */
  var card = document.getElementById("today-card");
  var fd = document.getElementById("facts-data");
  if (card && fd) {
    var facts = JSON.parse(fd.textContent);
    var count = document.getElementById("today-count");
    var next = document.getElementById("today-next");
    var now = new Date();
    var doy = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 864e5);
    var idx = doy % facts.length;
    var show = function (i, animate) {
      var f = facts[i];
      card.className = "today-card c-" + f.r;
      card.setAttribute("data-index", i);
      card.innerHTML = '<div><p class="today-region">' + esc(f.rn) + '</p><p class="today-figure">' + esc(f.fig) +
        "</p></div><div><h3>" + esc(f.title) + '</h3><p class="today-body">' + esc(f.body) +
        '</p><p class="fact-rel">더 알아보기 ' + f.rel.map(function (l) { return '<a href="' + esc(l[1]) + '">' + esc(l[0]) + "</a>"; }).join(" · ") + "</p></div>";
      if (animate) { void card.offsetWidth; card.classList.add("swap"); }
      count.textContent = (i + 1) + " / " + facts.length;
    };
    if (String(idx) !== card.getAttribute("data-index")) show(idx, false);
    next.hidden = false;
    next.addEventListener("click", function () { idx = (idx + 1) % facts.length; show(idx, true); });
  }
})();
