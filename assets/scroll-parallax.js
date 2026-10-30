/* ========= 滚动视差显露（全站共用） =========
 *
 * 各区块进入视野时淡入；位移与滚动位置连续绑定：
 * 元素离视口中心越远偏移越大，随滚动漂移，形成视差层。
 * 停止滚动即停在当前偏移，反向滚动沿原路径退回。
 *
 * 可调参数：
 *   FACTOR —— 视差强度，元素距视口中心半个屏高时的最大偏移（px）
 */

(function () {
  "use strict";

  var FACTOR = 46;

  var motionPreference = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );

  var items = Array.prototype.slice.call(
    document.querySelectorAll(".reveal")
  );

  if (!items.length) {
    return;
  }

  /* 原「一次性上浮」的 transform 过渡取消，位移改由滚动逐帧驱动 */
  var style = document.createElement("style");
  style.textContent =
    ".motion-enabled .reveal-inner," +
    ".motion-enabled .reveal-content {" +
    "transition-property: opacity;" +
    "}";
  document.head.appendChild(style);

  var observer = null;
  var parallaxOn = false;

  function setAllVisible() {
    items.forEach(function (el) {
      el.classList.add("is-visible", "visible");
    });
  }

  /* ---- 视差位移：仅在滚动或视口变化时更新 ---- */

  var lastY = -1;
  var lastW = 0;
  var lastH = 0;

  function update() {
    if (!parallaxOn) {
      return;
    }

    var y = window.scrollY || window.pageYOffset;

    if (
      y === lastY &&
      window.innerWidth === lastW &&
      window.innerHeight === lastH
    ) {
      return;
    }

    lastY = y;
    lastW = window.innerWidth;
    lastH = window.innerHeight;

    var mid = lastH / 2;

    items.forEach(function (el) {
      var inner = el.querySelector(".reveal-inner, .reveal-content");

      if (!inner) {
        return;
      }

      var rect = el.getBoundingClientRect();
      var p = (rect.top + rect.height / 2 - mid) / lastH;
      p = Math.max(-0.9, Math.min(0.9, p));

      inner.style.transform =
        "translateY(" + (p * FACTOR).toFixed(1) + "px)";
    });
  }

  function loop() {
    update();
    window.requestAnimationFrame(loop);
  }

  /* ---- 初始化与降级 ---- */

  function setup() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }

    document.documentElement.classList.remove("motion-enabled");
    parallaxOn = false;

    items.forEach(function (el) {
      el.classList.remove("is-visible", "visible");

      var inner = el.querySelector(".reveal-inner, .reveal-content");
      if (inner) {
        inner.style.transform = "";
      }
    });

    if (!("IntersectionObserver" in window) || motionPreference.matches) {
      /* 降级：直接全部显示，不做视差 */
      setAllVisible();
      return;
    }

    observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          entry.target.classList.toggle("is-visible", entry.isIntersecting);
          entry.target.classList.toggle("visible", entry.isIntersecting);
        });
      },
      { threshold: 0 }
    );

    items.forEach(function (el) {
      observer.observe(el);
    });

    document.documentElement.classList.add("motion-enabled");
    parallaxOn = true;
    lastY = -1;
    update();
  }

  setup();
  window.requestAnimationFrame(loop);

  if (motionPreference.addEventListener) {
    motionPreference.addEventListener("change", setup);
  }

  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      setup();
    }
  });
})();
