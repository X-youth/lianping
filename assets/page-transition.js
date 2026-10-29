/* 页面过渡幕布：进站开帘 + 站内 .html 链接合帘 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var curtain = null;
  var styleReady = false;

  function injectStyle() {
    if (styleReady || document.getElementById("pt-style")) {
      styleReady = true;
      return;
    }

    var style = document.createElement("style");
    style.id = "pt-style";
    style.textContent = [
      "#pt-curtain{position:fixed;inset:0;z-index:9998;display:grid;place-items:center;",
      "background:#f3f0e9;opacity:1;pointer-events:none;",
      "transition:opacity .3s ease}",
      "#pt-curtain.is-open{opacity:0;transition:opacity 1.2s ease}",
      "#pt-curtain.is-entering{opacity:0;transition:none}",
      ".pt-ring{display:grid;place-items:center;width:92px;height:92px;",
      "border:1px solid rgba(20,19,18,.4);border-radius:50%;",
      "font:11px/1 \"Helvetica Neue\",\"PingFang SC\",\"Microsoft YaHei\",sans-serif;",
      "letter-spacing:.22em;color:#141312;",
      "transition:transform .8s cubic-bezier(.5,0,.2,1),opacity .6s ease;",
      "will-change:transform}",
      "#pt-curtain.is-open .pt-ring{transform:scale(2.8);opacity:0}"
    ].join("");

    document.head.appendChild(style);
    styleReady = true;
  }

  function buildCurtain(entering) {
    injectStyle();

    var element = document.createElement("div");
    element.id = "pt-curtain";
    element.setAttribute("aria-hidden", "true");

    if (entering) {
      element.classList.add("is-entering");
    }

    var ring = document.createElement("span");
    ring.className = "pt-ring";

    var label = document.createElement("span");
    label.textContent = "连平";

    ring.appendChild(label);
    element.appendChild(ring);
    document.body.insertBefore(element, document.body.firstChild);

    curtain = element;
    return element;
  }

  function removeCurtain() {
    if (!curtain) return;
    if (curtain.parentNode) {
      curtain.parentNode.removeChild(curtain);
    }
    curtain = null;
  }

  function playIntro() {
    var element = buildCurtain();

    window.setTimeout(function () {
      element.classList.add("is-open");
    }, 650);

    /* 最迟 1.8s 强制移除 */
    window.setTimeout(removeCurtain, 1800);
  }

  function closeCurtain(url) {
    if (curtain) {
      /* 开帘过程中点击：先恢复整块幕布 */
      curtain.classList.remove("is-open", "is-entering");
    } else {
      var element = buildCurtain(true);

      /* 强制读取一次布局，让 .3s 合拢过渡生效 */
      element.getBoundingClientRect();

      window.requestAnimationFrame(function () {
        element.classList.remove("is-entering");
      });
    }

    window.setTimeout(function () {
      window.location.href = url;
    }, 620);
  }

  function isInternalHtmlLink(link) {
    if (!link || !link.href) return false;
    if (link.target && link.target !== "_self") return false;
    if (link.hasAttribute("download")) return false;

    var url;
    try {
      url = new URL(link.href, window.location.href);
    } catch (error) {
      return false;
    }

    if (url.origin !== window.location.origin) return false;
    if (!/\.html$/i.test(url.pathname)) return false;

    var samePage =
      url.pathname === window.location.pathname &&
      url.search === window.location.search;

    /* 同页锚点不拦截 */
    if (samePage && url.hash) return false;

    return true;
  }

  document.addEventListener("click", function (event) {
    if (reduceMotion.matches) return;
    if (event.defaultPrevented) return;
    if (event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }

    var link = event.target.closest
      ? event.target.closest("a[href]")
      : null;

    if (!isInternalHtmlLink(link)) return;

    event.preventDefault();

    closeCurtain(new URL(link.href, window.location.href).href);
  });

  /* 从缓存返回时不要留下幕布 */
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      removeCurtain();
    }
  });

  /* 系统偏好减少动态时直接跳过幕布 */
  if (reduceMotion.matches) {
    removeCurtain();
  } else {
    playIntro();
  }
})();
