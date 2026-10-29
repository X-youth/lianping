/* 开屏：翻开一本书
 *
 * 可调参数集中在 BOOK 对象：
 *   scrollDistance  翻书所需滚动距离（视口高度的倍数）
 *   maxOpenAngle    封面最大打开角度（度）
 *   expandStart     开始「书页放大 + 减弱透视」的进度点
 *   shadowStrength  书页阴影强度
 *   easing          滚动跟随的平滑度（0.05 很缓，0.3 很快）
 *   closeDuration   合书动画总时长（毫秒）
 *   closeExpandRatio 「缩小回书本」阶段所占时长比例
 */

(function () {
  "use strict";

  var BOOK = {
    scrollDistance: 1.7,
    maxOpenAngle: 168,
    expandStart: 0.72,
    shadowStrength: 0.42,
    easing: 0.12,
    closeDuration: 2400,
    closeExpandRatio: 0.36,
    openGuard: 600
  };

  var root = document.getElementById("book-intro");
  if (!root) return;

  var stage = root.querySelector(".bi-stage");
  var book = root.querySelector(".bi-book");
  var cover = root.querySelector(".bi-cover");
  var veil = root.querySelector(".bi-veil");
  var hint = root.querySelector(".bi-hint");
  var skipBtn = root.querySelector(".bi-skip");
  var reopen = root.querySelector(".bi-reopen");
  var reopenBtn = root.querySelector(".bi-reopen button");
  var endBtn = document.getElementById("close-book");
  var html = document.documentElement;

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var state = "intro"; /* intro | open | closing | closed */
  var progress = 0;
  var target = 0;
  var acc = 0;
  var distance = 1;
  var maxScale = 1;
  var running = false;
  var closing = false;
  var raf = 0;
  var lastFrame = 0;
  var openGuard = 0;

  function clamp(v, a, b) {
    return v < a ? a : v > b ? b : v;
  }

  function smoothstep(a, b, v) {
    var t = clamp((v - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  }

  function measure() {
    distance = Math.max(window.innerHeight * BOOK.scrollDistance, 200);
    var w = book.offsetWidth || 320;
    var h = book.offsetHeight || 430;
    maxScale = Math.max(window.innerWidth / w, window.innerHeight / h) * 1.03;
  }

  function render() {
    var p = progress;
    var openT = smoothstep(BOOK.expandStart, 1, p);

    cover.style.transform = "rotateY(" + (-BOOK.maxOpenAngle * p).toFixed(2) + "deg)";

    book.style.transform =
      "rotateX(" + (5 - 5 * openT).toFixed(2) + "deg)" +
      " rotateY(" + (-7 + 7 * openT).toFixed(2) + "deg)" +
      " scale(" + (1 + (maxScale - 1) * openT).toFixed(4) + ")";

    stage.style.perspective = (1600 + 2600 * openT).toFixed(0) + "px";

    veil.style.opacity = (1 - smoothstep(0.55, 0.9, p)).toFixed(3);

    root.style.setProperty(
      "--bi-page-shadow",
      (
        BOOK.shadowStrength *
        (0.22 + 0.78 * p) *
        (1 - smoothstep(0.82, 1, p))
      ).toFixed(3)
    );

    var fade = p > 0.12 ? 0 : 1 - smoothstep(0.01, 0.1, p);
    var hidden = state === "closed";
    hint.style.opacity = hidden ? "0" : fade.toFixed(3);
    skipBtn.style.opacity = hidden ? "0" : fade.toFixed(3);

    root.style.opacity =
      state === "intro" && p > 0.92
        ? (1 - (p - 0.92) / 0.08).toFixed(3)
        : "1";
  }

  /* 立即回到顶部：暂时关闭平滑滚动，避免解除锁定后出现可见的回滚 */
  function jumpTop() {
    var prev = html.style.scrollBehavior;
    html.style.scrollBehavior = "auto";
    window.scrollTo(0, 0);
    html.style.scrollBehavior = prev;
  }

  function finishOpen() {
    state = "open";
    running = false;
    lastFrame = 0;
    cancelAnimationFrame(raf);
    jumpTop();
    root.classList.add("is-done");
    html.classList.remove("intro-lock");
    /* 刚完成时吸收剩余的滚动惯性，让读者从首页顶部开始 */
    openGuard = performance.now() + BOOK.openGuard;
  }

  function tick(now) {
    if (state !== "intro") {
      running = false;
      lastFrame = 0;
      return;
    }

    /* 与帧率无关的平滑跟随：60fps 时等价于每帧 easing 系数 */
    var dt = lastFrame ? Math.min(now - lastFrame, 48) : 16.7;
    lastFrame = now;

    var base = reduce ? 0.5 : BOOK.easing;
    var k = 1 - Math.pow(1 - base, dt / 16.7);

    progress += (target - progress) * k;

    if (
      Math.abs(target - progress) < 0.0008 ||
      (target === 1 && progress > 0.992)
    ) {
      progress = target;
    }

    render();

    if (progress >= 0.999) {
      finishOpen();
      return;
    }

    raf = requestAnimationFrame(tick);
  }

  function kick() {
    if (!running) {
      running = true;
      lastFrame = 0;
      raf = requestAnimationFrame(tick);
    }
  }

  function addScroll(delta) {
    acc = clamp(acc + delta, 0, distance);
    target = acc / distance;
    kick();
  }

  /* ---------- 滚动 / 触摸 ---------- */

  function onWheel(event) {
    if (state === "open") {
      if (event.ctrlKey) return;
      if (performance.now() < openGuard) event.preventDefault();
      return;
    }

    if (state === "closing") {
      event.preventDefault();
      return;
    }

    if (state === "closed") {
      if (event.deltaY > 0) {
        event.preventDefault();
        startReopen();
      }
      return;
    }

    event.preventDefault();
    addScroll(event.deltaMode === 1 ? event.deltaY * 16 : event.deltaY);
  }

  var touchY = null;

  function onTouchStart(event) {
    if (state === "open") {
      touchY = null;
      return;
    }
    touchY = event.touches[0].clientY;
  }

  function onTouchMove(event) {
    if (state === "open" || touchY === null) return;

    if (state === "closing") {
      event.preventDefault();
      return;
    }

    if (state === "closed") {
      var up = touchY - event.touches[0].clientY;
      touchY = null;
      if (up > 0) {
        event.preventDefault();
        startReopen();
      }
      return;
    }

    event.preventDefault();
    var y = event.touches[0].clientY;
    var dy = touchY - y;
    touchY = y;
    addScroll(dy * 1.35);
  }

  /* ---------- 跳过 ---------- */

  function skip() {
    if (state !== "intro") return;
    acc = distance;
    target = 1;
    kick();
  }

  skipBtn.addEventListener("click", skip);

  /* 开屏 / 合书期间屏蔽键盘滚动，避免页面在锁定时被 PageDown、空格推动 */
  var SCROLL_KEYS = [
    " ",
    "Spacebar",
    "ArrowDown",
    "ArrowUp",
    "PageDown",
    "PageUp",
    "Home",
    "End"
  ];

  document.addEventListener(
    "keydown",
    function (event) {
      if (state === "open") return;

      if (event.key === "Escape" && state === "intro") {
        skip();
        return;
      }

      if (SCROLL_KEYS.indexOf(event.key) !== -1) event.preventDefault();
    },
    { passive: false }
  );

  /* ---------- 再次翻阅 ---------- */

  function startReopen() {
    if (state !== "closed" || closing) return;

    state = "intro";
    acc = 0;
    target = 0;
    progress = 0;

    reopen.hidden = true;
    hint.hidden = false;
    hint.style.opacity = "1";
    skipBtn.style.opacity = "1";
    root.style.opacity = "1";
    veil.style.opacity = "1";

    render();
    kick();
  }

  reopenBtn.addEventListener("click", startReopen);

  /* ---------- 合书 ---------- */

  function closeBook() {
    if (state !== "open" || closing) return;

    closing = true;
    state = "closing";

    html.classList.add("intro-lock");
    root.classList.remove("is-done");
    root.style.opacity = "1";
    progress = 1;
    target = 1;
    measure();
    render();
    veil.style.opacity = "1";

    hint.style.opacity = "0";
    skipBtn.style.opacity = "0";

    var t0 = performance.now();
    var dur = reduce ? 450 : BOOK.closeDuration;

    function step(now) {
      var k = clamp((now - t0) / dur, 0, 1);
      var ea = smoothstep(0, BOOK.closeExpandRatio, k);
      var eb = smoothstep(BOOK.closeExpandRatio, 1, k);
      var openT = 1 - ea;

      book.style.transform =
        "rotateX(" + (5 - 5 * openT).toFixed(2) + "deg)" +
        " rotateY(" + (-7 + 7 * openT).toFixed(2) + "deg)" +
        " scale(" + (1 + (maxScale - 1) * openT).toFixed(4) + ")";

      stage.style.perspective = (1600 + 2600 * openT).toFixed(0) + "px";
      cover.style.transform = "rotateY(" + (-BOOK.maxOpenAngle * (1 - eb)).toFixed(2) + "deg)";
      root.style.setProperty(
        "--bi-page-shadow",
        (BOOK.shadowStrength * (0.22 + 0.78 * eb)).toFixed(3)
      );
      veil.style.opacity = "1";

      if (k < 1) {
        requestAnimationFrame(step);
      } else {
        finishClose();
      }
    }

    requestAnimationFrame(step);
  }

  function finishClose() {
    jumpTop();
    progress = 0;
    target = 0;
    acc = 0;

    state = "closed";
    closing = false;

    reopen.hidden = false;
    hint.hidden = true;
    root.style.opacity = "1";
    veil.style.opacity = "1";

    render();
  }

  if (endBtn) endBtn.addEventListener("click", closeBook);

  /* ---------- 初始化 ---------- */

  /* 站内返回（浏览器后退，或从其他子页点回首页）时不再播放开屏，直接进首页 */
  var navEntries = performance.getEntriesByType
    ? performance.getEntriesByType("navigation")
    : [];
  var navType = navEntries.length ? navEntries[0].type : "";

  var fromSite = false;
  try {
    fromSite =
      !!document.referrer &&
      new URL(document.referrer, location.href).origin === location.origin;
  } catch (e) {}

  if (navType === "back_forward" || fromSite) {
    state = "open";
    root.classList.add("is-done");
    return;
  }

  if (location.hash) {
    history.replaceState(null, "", location.pathname + location.search);
  }

  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  html.classList.add("intro-lock");
  jumpTop();

  measure();
  render();

  window.addEventListener("resize", function () {
    measure();
    if (state === "intro" || state === "closed") render();
  });

  window.addEventListener("wheel", onWheel, { passive: false });
  window.addEventListener("touchstart", onTouchStart, { passive: true });
  window.addEventListener("touchmove", onTouchMove, { passive: false });

  if (reduce) {
    setTimeout(function () {
      if (state === "intro") {
        acc = distance;
        target = 1;
        progress = 1;
        render();
        finishOpen();
      }
    }, 900);
  }
})();
