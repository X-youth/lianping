"""把广东省与连平县的 GeoJSON 转成 SVG path（绍宽 780x600）。"""

import json
import math
import os
import sys

BOX_W, BOX_H = 780, 600
PAD = 26


def mercator(lon, lat):
    x = math.radians(lon)
    y = -math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rings(feature):
    geom = feature["geometry"]
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def collect(features):
    """返回每个 feature 的 [外环, 内环...] 列表。"""
    return [rings(f) for f in features]


def douglas(fig, eps):
    """Douglas-Peucker 简化。"""
    if len(fig) < 3:
        return fig

    def point_line_dist(p, a, b):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        if dx == dy == 0:
            return math.hypot(p[0] - ax, p[1] - ay)

        t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        px, py = ax + t * dx, ay + t * dy
        return math.hypot(p[0] - px, p[1] - py)

    dmax, index = 0.0, 0
    for i in range(1, len(fig) - 1):
        d = point_line_dist(fig[i], fig[0], fig[-1])
        if d > dmax:
            dmax, index = d, i

    if dmax > eps:
        left = douglas(fig[: index + 1], eps)
        right = douglas(fig[index:], eps)
        return left[:-1] + right

    return [fig[0], fig[-1]]


def area(pts):
    s = 0.0
    for i in range(len(pts) - 1):
        s += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]

    return abs(s) / 2


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    outline = load(os.path.join(here, "gd-outline.json"))
    cities = load(os.path.join(here, "gd-cities.json"))
    heyuan = load(os.path.join(here, "heyuan.json"))

    # 先把所有点投影，求出包围盒
    raw = []

    for feat in outline["features"]:
        for poly in rings(feat):
            for ring in poly:
                raw.append([mercator(p[0], p[1]) for p in ring])

    for feat in cities["features"]:
        for poly in rings(feat):
            for ring in poly:
                raw.append([mercator(p[0], p[1]) for p in ring])

    for feat in heyuan["features"]:
        for poly in rings(feat):
            for ring in poly:
                raw.append([mercator(p[0], p[1]) for p in ring])

    xs = [p[0] for r in raw for p in r]
    ys = [p[1] for r in raw for p in r]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    scale = min(
        (BOX_W - PAD * 2) / (maxx - minx),
        (BOX_H - PAD * 2) / (maxy - miny),
    )

    offx = (BOX_W - (maxx - minx) * scale) / 2
    offy = (BOX_H - (maxy - miny) * scale) / 2

    def project(lon, lat):
        x, y = mercator(lon, lat)
        return (
            offx + (x - minx) * scale,
            offy + (y - miny) * scale,
        )

    def path_of(features, eps=0.45, min_area=1.6):
        parts = []

        for feat in features:
            for poly in rings(feat):
                for idx, ring in enumerate(poly):
                    pts = [project(p[0], p[1]) for p in ring]
                    pts = douglas(pts, eps)

                    if len(pts) < 3 or area(pts) < (min_area if idx == 0 else 0.0):
                        continue

                    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
                    parts.append(d)

        return "".join(parts)

    province = path_of(outline["features"], eps=0.35, min_area=2.0)
    city_paths = path_of(cities["features"], eps=0.4, min_area=1.6)

    lianping_feats = [
        f for f in heyuan["features"]
        if str(f["properties"].get("adcode")) == "441623"
    ]

    if not lianping_feats:
        print("找不到连平县", file=sys.stderr)
        return 1

    lianping = path_of(lianping_feats, eps=0.3, min_area=1.0)

    # 连平质心（用外环点的平均，够用）
    ring = rings(lianping_feats[0])[0][0]
    cx = sum(project(p[0], p[1])[0] for p in ring) / len(ring)
    cy = sum(project(p[0], p[1])[1] for p in ring) / len(ring)

    # 河源市整体轮廓（用它的县合起来的外框做描边没必要，直接给各县边界）
    out = {
        "viewBox": f"0 0 {BOX_W} {BOX_H}",
        "province": province,
        "cities": city_paths,
        "lianping": lianping,
        "centroid": [round(cx, 1), round(cy, 1)],
    }

    with open(os.path.join(here, "map-data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print("province", len(province), "cities", len(city_paths), "lianping", len(lianping))
    print("centroid", out["centroid"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
