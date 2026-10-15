#!/usr/bin/env python3
"""P3-C 现画 SVG 插图：按想法 motif + palette 生成扁平风 SVG（再由 build_deck 转 PNG 嵌入）。

motif: vine（南瓜藤蔓生长线）/ pumpkins（三瓜分级）/ warehouse（产地仓）/ coins（收入线）/ generic
Usage:
    python3 make_svg_art.py --motif vine --page 05 --palette ./ppt-work/brief.json --out ./images/art-p05.svg
    python3 make_svg_art.py --motif generic --title "四条收入线" --palette ./ppt-work/brief.json --out ./images/art.svg
"""
import argparse
import json
from pathlib import Path


def load_pal(path: str) -> dict:
    b = json.loads(Path(path).read_text(encoding="utf-8"))
    p = b.get("palette_custom") or {}
    return {"bg": p.get("bg", "#FFFFFF"), "surface": p.get("surface", "#F7F7F5"),
            "ink": p.get("ink", "#000000"), "muted": p.get("muted", "#5A5A5A"),
            "accent": p.get("accent", "#FE7141"), "accent_ink": p.get("accent_ink", "#000000")}


def svg_wrap(inner: str, pal: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
<rect width="800" height="600" fill="{pal['surface']}"/>
{inner}
</svg>
"""


def art_vine(pal: dict, progress: float = 0.5) -> str:
    # 生长线：底部藤蔓 + 叶子 + 一颗随 progress 变大的南瓜
    r = 40 + progress * 70
    return f"""
<path d="M40,520 C220,470 320,540 470,490 S700,430 760,460" stroke="{pal['accent']}" stroke-width="14" fill="none" stroke-linecap="round"/>
<ellipse cx="250" cy="480" rx="46" ry="22" fill="#4F8F3A" transform="rotate(-18 250 480)"/>
<ellipse cx="540" cy="460" rx="52" ry="24" fill="#4F8F3A" transform="rotate(12 540 460)"/>
<g>
<ellipse cx="400" cy="{420 - progress * 60}" rx="{r}" ry="{r * 0.78}" fill="{pal['accent']}"/>
<path d="M400,{420 - progress * 60 - r * 0.78} q6,-26 26,-30" stroke="#3E7A2E" stroke-width="10" fill="none" stroke-linecap="round"/>
<path d="M400,{420 - progress * 60 - r * 0.6} L400,{420 - progress * 60 + r * 0.6}" stroke="#C74A1B" stroke-width="4" opacity="0.55"/>
<path d="M{400 - r * 0.5},{420 - progress * 60 - r * 0.3} L{400 - r * 0.5},{420 - progress * 60 + r * 0.3}" stroke="#C74A1B" stroke-width="4" opacity="0.4"/>
<path d="M{400 + r * 0.5},{420 - progress * 60 - r * 0.3} L{400 + r * 0.5},{420 - progress * 60 + r * 0.3}" stroke="#C74A1B" stroke-width="4" opacity="0.4"/>
</g>
<circle cx="120" cy="120" r="52" fill="{pal['accent']}" opacity="0.16"/>
<circle cx="690" cy="130" r="30" fill="{pal['ink']}" opacity="0.08"/>
"""


def art_pumpkins(pal: dict) -> str:
    def pumpkin(cx, size, color, label):
        return f"""
<g>
<ellipse cx="{cx}" cy="360" rx="{size}" ry="{size * 0.78}" fill="{color}"/>
<path d="M{cx},{360 - size * 0.4} L{cx},{360 + size * 0.4}" stroke="#00000022" stroke-width="5"/>
<rect x="{cx - 70}" y="{360 + size * 0.78 + 12}" width="140" height="34" fill="{pal['ink']}"/>
<text x="{cx}" y="{360 + size * 0.78 + 36}" font-size="22" text-anchor="middle" fill="{pal['bg']}" font-family="sans-serif">{label}</text>
</g>"""
    return (pumpkin(200, 90, pal["accent"], "好瓜·团购")
            + pumpkin(430, 66, "#FFB37E", "次瓜·加工")
            + pumpkin(620, 46, "#4F8F3A", "种子·未来"))


def art_warehouse(pal: dict) -> str:
    return f"""
<rect x="180" y="220" width="440" height="260" fill="{pal['bg']}" stroke="{pal['ink']}" stroke-width="10"/>
<path d="M150,220 L400,110 L650,220 Z" fill="{pal['accent']}"/>
<rect x="340" y="340" width="120" height="140" fill="{pal['ink']}"/>
<rect x="220" y="270" width="90" height="70" fill="{pal['surface']}" stroke="{pal['ink']}" stroke-width="6"/>
<rect x="490" y="270" width="90" height="70" fill="{pal['surface']}" stroke="{pal['ink']}" stroke-width="6"/>
<circle cx="120" cy="480" r="26" fill="{pal['accent']}"/>
<circle cx="690" cy="480" r="26" fill="{pal['accent']}"/>
"""


def art_coins(pal: dict) -> str:
    bars = ""
    vals = [("抽佣", 200), ("团购", 150), ("仓储", 120), ("加工", 180)]
    for i, (name, h) in enumerate(vals):
        x = 120 + i * 150
        bars += f"""
<rect x="{x}" y="{460 - h}" width="90" height="{h}" fill="{pal['accent'] if i % 2 == 0 else pal['ink']}"/>
<text x="{x + 45}" y="500" font-size="26" text-anchor="middle" fill="{pal['ink']}" font-family="sans-serif">{name}</text>"""
    return bars + f"""<text x="400" y="120" font-size="44" text-anchor="middle" fill="{pal['ink']}" font-family="sans-serif">四条收入线</text>"""


def art_generic(pal: dict, title: str) -> str:
    return f"""
<circle cx="400" cy="260" r="120" fill="{pal['accent']}"/>
<text x="400" y="280" font-size="52" text-anchor="middle" fill="{pal['accent_ink']}" font-family="sans-serif">{title[:6]}</text>
<rect x="140" y="430" width="520" height="26" fill="{pal['ink']}" opacity="0.85"/>
<rect x="220" y="470" width="360" height="18" fill="{pal['ink']}" opacity="0.35"/>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motif", default="generic", choices=["vine", "pumpkins", "warehouse", "coins", "generic"])
    ap.add_argument("--page", default="01")
    ap.add_argument("--title", default="")
    ap.add_argument("--progress", type=float, default=0.5)
    ap.add_argument("--palette", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pal = load_pal(a.palette)
    if a.motif == "vine":
        inner = art_vine(pal, a.progress)
    elif a.motif == "pumpkins":
        inner = art_pumpkins(pal)
    elif a.motif == "warehouse":
        inner = art_warehouse(pal)
    elif a.motif == "coins":
        inner = art_coins(pal)
    else:
        inner = art_generic(pal, a.title or f"P{a.page}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg_wrap(inner, pal), encoding="utf-8")
    print(f"SVG 已生成：{out}（motif={a.motif}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
