"""把河源市各县 GeoJSON 转成「四种方式认识连平」区块用的 SVG path。

舞台 viewBox 为 1000x800（宽高比 1.25，与 .map-stage 一致）。
输出：各县 path、连平高亮 path、四个镇的真实投影坐标与百分比。

镇坐标来源：OpenStreetMap Nominatim（2026-10-29 查询）。
"""

import os
import sys

from build_map import mercator, douglas, rings, load, area

BOX_W, BOX_H = 1000, 800
PAD = 46

# 镇名 -> (lon, lat)
TOWNS = {
    "上坪镇": (114.5873314, 24.4888675),
    "忠信镇": (114.7333330, 24.2166670),
    "大湖镇": (114.8322440, 24.2395680),
    "元善镇": (114.4913925, 24.3542443),
}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    heyuan = load(os.path.join(here, "heyuan.json"))
    feats = heyuan["features"]

    raw = []
    for feat in feats:
        for poly in rings(feat):
            for ring in poly:
                raw.append([mercator(p[0], p[1]) for p in ring])

    lp_feats = [f for f in feats if str(f["properties"].get("adcode")) == "441623"]
    if not lp_feats:
        print("找不到连平县", file=sys.stderr)
        return 1

    # 以连平县为中心放大（周边县只作背景，超出画布的部分被裁掉）
    lp_pts = [
        mercator(p[0], p[1])
        for poly in rings(lp_feats[0])
        for ring in poly
        for p in ring
    ]
    lx = [p[0] for p in lp_pts]
    ly = [p[1] for p in lp_pts]

    scale = min(
        (BOX_W - PAD * 2) / (max(lx) - min(lx)),
        (BOX_H - PAD * 2) / (max(ly) - min(ly)),
    )

    offx = (BOX_W - (max(lx) - min(lx)) * scale) / 2
    offy = (BOX_H - (max(ly) - min(ly)) * scale) / 2

    def project(lon, lat):
        x, y = mercator(lon, lat)
        return (
            offx + (x - min(lx)) * scale,
            offy + (y - min(ly)) * scale,
        )

    def path_of(features, eps=0.45, min_area=1.2):
        parts = []
        for feat in features:
            for poly in rings(feat):
                for idx, ring in enumerate(poly):
                    pts = [project(p[0], p[1]) for p in ring]
                    pts = douglas(pts, eps)
                    if len(pts) < 3 or area(pts) < (min_area if idx == 0 else 0.0):
                        continue
                    parts.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
        return "".join(parts)

    print("=== 需要的县 path ===")
    for feat in feats:
        adcode = str(feat["properties"].get("adcode"))
        name = feat["properties"].get("name", "?")

        if adcode == "441623":          # 连平：主图，保留细节
            d, eps = path_of([feat], eps=0.45), 0.45
        elif adcode in ("441624", "441625"):   # 和平、东源：背景邻县，放宽简化
            d, eps = path_of([feat], eps=1.1), 1.1
        else:                            # 其余县在画面外，跳过
            continue

        ring0 = rings(feat)[0][0]
        pts0 = [project(p[0], p[1]) for p in ring0]
        cx = sum(p[0] for p in pts0) / len(pts0)
        cy = sum(p[1] for p in pts0) / len(pts0)
        print(f"\n-- {name} ({adcode}) len={len(d)} eps={eps} centroid=({cx:.0f},{cy:.0f})")
        print(d)

    print("\n=== 镇点（viewBox 坐标 / 舞台百分比）===")
    for name, (lon, lat) in TOWNS.items():
        x, y = project(lon, lat)
        print(f"{name}: x={x:.1f} y={y:.1f}  left={x / BOX_W * 100:.1f}% top={y / BOX_H * 100:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
