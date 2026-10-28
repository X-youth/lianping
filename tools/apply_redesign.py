"""首页改版：把「探索连平」从整幅县界地图改成 主题切换 + 大幅照片 + 定位小地图。

1. 抽出旧 SVG 里的连平县 path，复用进定位小地图
2. 替换第五节 CSS（旧地图/圆形入口样式 -> 主题切换样式）
3. 替换「场景探索」整段 HTML
4. 在 </body> 前追加主题切换脚本
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
INDEX = os.path.join(SITE, "index.html")

with open(INDEX, encoding="utf-8") as f:
    html = f.read()

# ---- 1. 抽出连平县 path ----

m = re.search(r'class="map-lp"\s+d="([^"]+)"', html)
if not m:
    raise SystemExit("没找到连平县 path")
LP = m.group(1)

# ---- 2. 第五节 CSS ----

CSS5 = """    /* ========= 5. 探索连平：主题切换 ========= */

    .explore-section {
      padding: 80px 6% 110px;

      /* 上下都从纸色渐入，不留硬边 */
      background: linear-gradient(
        180deg,
        var(--paper) 0%,
        #f0f2e8 9%,
        #ecefe4 26%,
        #ecefe4 74%,
        #f0f2e8 91%,
        var(--paper) 100%
      );
    }

    .explore-layout {
      max-width: 1250px;
      margin: auto;

      display: grid;
      grid-template-columns: 0.85fr 1.35fr;
      align-items: center;
      gap: 64px;
    }

    /* 四个主题入口 */

    .theme-tabs {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }

    .theme-tab {
      position: relative;

      padding: 9px 0 9px 24px;

      border: 0;
      background: none;

      font-family: "Songti SC", "SimSun", serif;
      font-size: 27px;
      letter-spacing: 3px;
      color: var(--muted);

      cursor: pointer;
      transition: color 0.3s ease;
    }

    /* 当前主题前的橙色小点 */

    .theme-tab::before {
      content: "";
      position: absolute;
      left: 0;
      top: 50%;

      width: 8px;
      height: 8px;

      border-radius: 50%;
      background: var(--orange);

      opacity: 0;
      transform: translateY(-50%) scale(0.4);

      transition:
        opacity 0.3s ease,
        transform 0.3s ease;
    }

    .theme-tab:hover {
      color: var(--ink);
    }

    .theme-tab.is-active {
      color: var(--ink);
    }

    .theme-tab.is-active::before {
      opacity: 1;
      transform: translateY(-50%) scale(1);
    }

    .theme-tab:focus-visible {
      outline: 3px solid var(--orange);
      outline-offset: 4px;
    }

    /* 当前主题的介绍 */

    .theme-info {
      margin-top: 26px;
    }

    .theme-location {
      margin: 0;

      color: var(--orange);
      font-size: 12px;
      letter-spacing: 4px;
    }

    .theme-description {
      margin: 14px 0 0;
      max-width: 34ch;

      color: #4c5847;
      font-size: 14px;
      line-height: 2.1;
    }

    /* 县域小地图：定位辅助 */

    .mini-map {
      margin-top: 36px;
      max-width: 220px;
    }

    .mini-map svg {
      display: block;
      width: 100%;
      height: auto;
      overflow: visible;
    }

    .mini-lp {
      fill: #d7e1c4;
      stroke: var(--green);
      stroke-width: 7;
      stroke-linejoin: round;
    }

    .mini-towns circle {
      fill: var(--paper);
      stroke: var(--orange);
      stroke-width: 6;

      cursor: pointer;

      transition:
        fill 0.3s ease,
        stroke-width 0.3s ease;
    }

    .mini-towns circle:hover {
      fill: #e9c9b8;
    }

    .mini-towns circle.is-active {
      fill: var(--orange);
      stroke-width: 8;
    }

    .mini-map-note {
      margin: 10px 0 0;

      color: var(--muted);
      font-size: 10.5px;
      letter-spacing: 1px;
      line-height: 1.8;
    }

    /* 大幅实景照片 */

    .explore-photo {
      margin: 0;
    }

    .explore-photo img {
      display: block;
      width: 100%;
      aspect-ratio: 3 / 2;
      object-fit: cover;

      border-radius: 6px;
      box-shadow: 0 26px 60px #314b4026;
    }

    .explore-photo figcaption {
      margin-top: 14px;

      color: var(--muted);
      font-size: 11.5px;
      letter-spacing: 2px;
      text-align: right;
    }

"""

start = html.index("    /* ========= 5.")
end = html.index("    /* ========= 6.")
html = html[:start] + CSS5 + html[end:]

# ---- 3. 场景探索 HTML ----

EXPLORE = """    <!-- 场景探索：四个主题入口 + 大幅实景照片 + 定位小地图 -->
    <section
      class="explore-section"
      id="explore"
      aria-labelledby="explore-title"
    >

      <div class="reveal">
        <div class="section-heading reveal-inner">

          <p class="eyebrow" lang="en">
            EXPLORE LIANPING
          </p>

          <h2 id="explore-title">
            循着风物，走进连平
          </h2>

          <p class="section-description">
            四种方式认识连平，选择一个主题开始。
          </p>

        </div>
      </div>

      <div class="reveal">
        <div class="explore-layout reveal-inner" id="explore-app">

          <!-- 左栏：主题入口 + 介绍 + 定位小地图 -->
          <div class="explore-panel">

            <div class="theme-tabs" role="group" aria-label="四个主题入口">
              <button
                class="theme-tab is-active"
                type="button"
                data-theme="history"
                aria-pressed="true"
              >读一段连平</button>

              <button
                class="theme-tab"
                type="button"
                data-theme="nature"
                aria-pressed="false"
              >走进山水</button>

              <button
                class="theme-tab"
                type="button"
                data-theme="life"
                aria-pressed="false"
              >点亮地方生活</button>

              <button
                class="theme-tab"
                type="button"
                data-theme="food"
                aria-pressed="false"
              >尝一口连平</button>
            </div>

            <div class="theme-info">
              <p class="theme-location" id="theme-location">
                大湖镇 · 围龙屋
              </p>

              <p class="theme-description" id="theme-description">
                半月塘环着客家围屋，一圈一圈，围出连平人家的岁月。
              </p>

              <a
                class="text-link theme-link"
                id="theme-link"
                href="./history.html"
              >进入历史故事 ↗</a>
            </div>

            <!-- 县域小地图：仅作定位辅助，镇点可点按切换主题 -->
            <div class="mini-map">
              <svg
                viewBox="0 0 1000 800"
                role="img"
                aria-label="连平县示意图，四个镇点对应四个主题"
              >
                <path
                  class="mini-lp"
                  d="__LP__"
                />

                <g class="mini-towns">
                  <circle
                    data-theme="nature"
                    cx="497.5"
                    cy="191.3"
                    r="18"
                    tabindex="0"
                  />
                  <circle
                    data-theme="food"
                    cx="372.6"
                    cy="383.6"
                    r="18"
                    tabindex="0"
                  />
                  <circle
                    data-theme="history"
                    cx="816.1"
                    cy="547.3"
                    r="18"
                    tabindex="0"
                  />
                  <circle
                    data-theme="life"
                    cx="687.4"
                    cy="580"
                    r="18"
                    tabindex="0"
                  />
                </g>
              </svg>

              <p class="mini-map-note">
                连平县示意 · 镇点按真实经纬度标注
              </p>
            </div>

          </div>

          <!-- 右栏：大幅实景照片 -->
          <figure class="explore-photo">
            <img
              id="theme-photo"
              src="./img/weilongwu.png"
              alt="大湖镇围龙屋"
            >
            <figcaption id="theme-caption">
              大湖镇 · 围龙屋
            </figcaption>
          </figure>

        </div>
      </div>

    </section>"""

start = html.index("    <!-- 场景探索 -->")
end = html.index("</section>", start) + len("</section>")
html = html[:start] + EXPLORE.replace("__LP__", LP) + html[end:]

# ---- 4. 主题切换脚本 ----

JS = """
  <script>
    /* ========= 探索连平：主题切换 ========= */

    (function () {
      const THEMES = {
        history: {
          location: "大湖镇 · 围龙屋",
          description:
            "半月塘环着客家围屋，一圈一圈，围出连平人家的岁月。",
          photo: "./img/weilongwu.png",
          alt: "大湖镇围龙屋",
          link: "./history.html",
          linkText: "进入历史故事 ↗"
        },
        nature: {
          location: "上坪镇 · 桃花山",
          description:
            "春天一来，桃花沿山势铺开，是连平最柔软的颜色。",
          photo: "./img/peach-blossom.png",
          alt: "上坪桃花",
          link: "./nature.html",
          linkText: "进入山水风景 ↗"
        },
        life: {
          location: "忠信镇 · 花灯",
          description:
            "一盏花灯，从竹篾与纸开始，点亮地方的日子。",
          photo: "./img/lantern.jpg",
          alt: "忠信花灯",
          link: "./life.html",
          linkText: "进入地方生活 ↗"
        },
        food: {
          location: "元善镇 · 鹰嘴蜜桃",
          description:
            "一枚鹰嘴蜜桃，藏着连平山野的甜。",
          photo: "./img/peach-fruit.jpg",
          alt: "鹰嘴蜜桃",
          link: "./food.html",
          linkText: "进入风味故事 ↗"
        }
      };

      const app = document.getElementById("explore-app");

      if (!app) {
        return;
      }

      const tabs = Array.from(app.querySelectorAll(".theme-tab"));
      const dots = Array.from(app.querySelectorAll(".mini-towns circle"));
      const photo = document.getElementById("theme-photo");
      const caption = document.getElementById("theme-caption");
      const location = document.getElementById("theme-location");
      const description = document.getElementById("theme-description");
      const link = document.getElementById("theme-link");

      function select(key) {
        const theme = THEMES[key];

        if (!theme) {
          return;
        }

        tabs.forEach((tab) => {
          const on = tab.dataset.theme === key;
          tab.classList.toggle("is-active", on);
          tab.setAttribute("aria-pressed", String(on));
        });

        dots.forEach((dot) => {
          dot.classList.toggle("is-active", dot.dataset.theme === key);
        });

        photo.src = theme.photo;
        photo.alt = theme.alt;
        caption.textContent = theme.location;
        location.textContent = theme.location;
        description.textContent = theme.description;
        link.href = theme.link;
        link.textContent = theme.linkText;
      }

      tabs.forEach((tab) => {
        tab.addEventListener("click", () => select(tab.dataset.theme));
      });

      // 镇点：点击与手机触摸都能切换
      dots.forEach((dot) => {
        dot.addEventListener("click", () => select(dot.dataset.theme));
        dot.addEventListener(
          "touchstart",
          () => select(dot.dataset.theme),
          { passive: true }
        );
        dot.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            select(dot.dataset.theme);
          }
        });
      });
    })();
  </script>

</body>"""

html = html.replace("\n</body>", JS, 1)

with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)

print("探索区块已替换，连平 path 长度", len(LP))
