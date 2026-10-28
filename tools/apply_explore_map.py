"""把 build_explore_map.py 输出的真实县界 path 写进 index.html 的探索区块。"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)


def grab(text, name):
    m = re.search(rf"-- {name}[^\n]*\n(M[^\n]+)", text)
    if not m:
        raise SystemExit(f"没找到 {name} 的 path")
    return m.group(1).strip()


with open(os.path.join(HERE, "explore-map-out.txt"), encoding="utf-8-sig") as f:
    out = f.read()

lp = grab(out, "连平县")
hp = grab(out, "和平县")
dy = grab(out, "东源县")

block = f"""          <!-- 真实县界底图：连平县高亮 + 邻县背景 + 镇点标注 -->
          <svg
            class="explore-map"
            viewBox="0 0 1000 800"
            preserveAspectRatio="xMidYMid slice"
            aria-hidden="true"
          >

            <!-- 邻县背景 -->
            <path
              class="map-neighbor"
              d="{hp}"
            />

            <path
              class="map-neighbor"
              d="{dy}"
            />

            <!-- 连平县 -->
            <path
              class="map-lp"
              d="{lp}"
            />

            <!-- 县名 -->
            <text
              class="map-county-name"
              x="880"
              y="140"
            >和平县</text>

            <text
              class="map-county-name"
              x="700"
              y="762"
            >东源县</text>

            <text
              class="map-lp-name"
              x="465"
              y="470"
            >连平县</text>

            <!-- 入口指向的镇 -->
            <path class="map-leader" d="M352 196L488 192"/>
            <path class="map-leader" d="M682 172L505 188"/>
            <path class="map-leader" d="M382 606L678 582"/>
            <path class="map-leader" d="M812 596L816 556"/>

            <!-- 镇点 -->
            <g class="map-towns">
              <circle cx="497.5" cy="191.3" r="5"/>
              <circle cx="687.4" cy="580" r="5"/>
              <circle cx="816.1" cy="547.3" r="5"/>
              <circle cx="372.6" cy="383.6" r="5"/>
            </g>

            <!-- 镇名 -->
            <text class="map-town-name" x="497" y="213">上坪镇</text>
            <text class="map-town-name" x="687" y="604">忠信镇</text>
            <text class="map-town-name" x="816" y="528">大湖镇</text>
            <text class="map-town-name" x="372" y="406">元善镇</text>

          </svg>"""

path = os.path.join(SITE, "index.html")

with open(path, encoding="utf-8") as f:
    lines = f.read().split("\n")

start = next(i for i, l in enumerate(lines) if "主题场景底图" in l)
end = next(i for i in range(start, len(lines)) if lines[i].strip() == "</svg>")

lines[start:end + 1] = block.split("\n")

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))

print("替换行", start + 1, "-", end + 1, "path 长度", len(lp), len(hp), len(dy))
