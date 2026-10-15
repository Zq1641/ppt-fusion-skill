#!/usr/bin/env python3
"""P3 deck builder v2: design tokens + assets aware editable PPTX.

- 色彩：整页色场 / surface 卡片 / accent 高亮块（关键词衬底），palette 六角色全上屏
- 配图：--assets assets.json（{page: {"image": path, "kind": cover|side|bg, "caption":...},
  或 {"svg": path}}），图片按 kind 排布，SVG 由 make_svg_art 生成后由本脚本转 PNG 嵌入
- 高亮：outline 行内【高亮词】自动套 accent 衬底（整词 accent_ink 字 + accent 底块）
- 数据页：--charts 时 data 页按 outline 数字建原生柱状图，否则沿用占位提示

Usage:
    python3 build_deck.py --brief ./ppt-work/brief.json --outline ./ppt-work/outline.md \\
        --assets ./ppt-work/assets.json --out ./ppt-work/deck-v1.pptx [--charts]
"""
import argparse
import io
import json
import re
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

try:
    import cairosvg  # type: ignore
    _HAS_CAIRO = True
except Exception:
    _HAS_CAIRO = False

try:
    from PIL import Image  # type: ignore
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


def hex2rgb(h: str) -> RGBColor:
    h = (h or "#000000").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def parse_outline(text: str):
    pages = []
    cur = None
    for line in text.splitlines():
        m = re.match(r"##\s*P\d+\s*\[(\w+)\]\s*(.+)", line.strip())
        if m:
            if cur:
                pages.append(cur)
            cur = {"layout": m.group(1), "title": m.group(2).strip(), "bullets": []}
        elif cur and line.strip().startswith("- "):
            cur["bullets"].append(line.strip()[2:].strip())
    if cur:
        pages.append(cur)
    # 序号
    for i, p in enumerate(pages, 1):
        p["num"] = i
    return pages


def clean_title(title: str) -> str:
    return title.strip().strip("\"'“” ").strip()


_HL = re.compile(r"【([^】]{1,12})】")
_META_PAREN = (re.compile(r"（目标：[^）]*）"), re.compile(r"\(目标：[^)]*\)"),
               re.compile(r"（三段式预告[^）]*）"), re.compile(r"\(三段式预告[^)]*\)"))
_META_FRAG = re.compile(r"^(一句话(立论|模式)?|三段式预告.*|目标：.*|左|右)$")


def content_bullets(items):
    """只把「内容：」上屏；claim/proof/move/关系/job/论点 都是元行，过滤掉。
    另剥 （目标：…）等元备注，并按 ｜ 拆成多条。"""
    out = []
    for it in items or []:
        s = it.strip()
        if not s:
            continue
        # 元行（v2.1 五栏中除「内容」外的四栏）
        if re.match(r"^(claim|proof|move|关系|job|论点|motif|topo)\s*[:：]", s):
            continue
        for prefix in ("内容：", "内容:", "论据：", "论据:"):
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        for par in _META_PAREN:
            s = par.sub("", s)
        parts = re.split(r"[｜|]", s)
        for frag in parts:
            f = frag.strip().strip("｜| ")
            f = re.sub(r"[，,]\s*一句话模式$", "", f)
            f = re.sub(r"^(左|右)[：:]\s*", "", f)
            if not f or _META_FRAG.match(f):
                continue
            out.append(f)
    return out


def set_bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _style_para(p, size, color, bold=False, alignment=PP_ALIGN.LEFT, space_after=None):
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = alignment
    if space_after is not None:
        p.space_after = Pt(space_after)
    for run in p.runs:
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color


def add_textbox(slide, left, top, width, height, text, size, color, bold=False, alignment=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    # 【高亮词】拆 run：普通 run + 高亮 run（加粗，由调用方再套底块）
    p.alignment = alignment
    segs = _HL.split(text)
    first = True
    for j, seg in enumerate(segs):
        if not seg:
            continue
        if first:
            p.text = seg
            first = False
            rp = p
        else:
            rp = p.add_run()
            rp.text = seg
        is_hl = (j % 2 == 1)
        for r in ([rp] if j == 0 else [rp]):
            r.font.size = Pt(size)
            r.font.bold = bold or is_hl
            r.font.color.rgb = color
    if space_after_default := None:
        pass
    return box


def add_hl_block(slide, left, top, width, height, pal):
    """accent 衬底块（画在文字下方，调用方先画块后写字）。"""
    shape = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex2rgb(pal["accent"])
    shape.line.fill.background()
    return shape


def add_accent_bar(slide, pal, top=3.42, left=0.6, width=0.9):
    shape = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Pt(6))
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex2rgb(pal["accent"])
    shape.line.fill.background()
    return shape


def add_card(slide, left, top, width, height, pal):
    shape = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex2rgb(pal["surface"])
    shape.line.fill.background()
    return shape


def add_bullets(slide, left, top, width, height, items, size, color):
    items = content_bullets(items)
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    if not items:
        return box
    for i, item in enumerate(items[:5]):
        item = re.sub(r"[【】]", "", item)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + item[:90]
        _style_para(p, size, color, False, PP_ALIGN.LEFT, space_after=8)
        p.level = 0
    return box


def svg_to_png_bytes(svg_path: Path, width_px: int = 1200) -> bytes | None:
    svg = svg_path.read_bytes()
    if _HAS_CAIRO:
        try:
            return cairosvg.svg2png(bytestring=svg, output_width=width_px)
        except Exception:
            pass
    if _HAS_PIL:
        # 兜底：cairosvg 不可用时，用 LibreOffice 转（由 agent 在外层转好再传 png）
        return None
    return None


def place_image(slide, img_path: Path, kind: str, pal):
    """kind: cover 全幅底图 / side 右栏配图 / bg 底纹（半透明效果用浅色罩代替）。"""
    if kind == "cover":
        slide.shapes.add_picture(str(img_path), Inches(6.8), Inches(0.8), Inches(5.9), Inches(5.9))
    elif kind == "side":
        add_card(slide, 6.8, 0.8, 5.9, 5.6, pal)
        slide.shapes.add_picture(str(img_path), Inches(7.0), Inches(1.0), Inches(5.5), Inches(4.4))
    elif kind == "bg":
        slide.shapes.add_picture(str(img_path), Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    else:  # tile 顶部横图
        slide.shapes.add_picture(str(img_path), Inches(0.6), Inches(0.6), Inches(4.0), Inches(2.4))


def extract_numbers(items) -> list[tuple[str, float]]:
    out = []
    for it in items:
        for m in re.finditer(r"([\u4e00-\u9fa5A-Za-z]{1,8})(\d+(?:\.\d+)?)(万|吨|亩|%|个|元)?", it):
            try:
                out.append((m.group(1) + (m.group(3) or ""), float(m.group(2))))
            except ValueError:
                continue
    # 去重保序，取前 6
    seen, res = set(), []
    for k, v in out:
        if k not in seen:
            seen.add(k)
            res.append((k, v))
        if len(res) >= 6:
            break
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--outline", required=True)
    ap.add_argument("--assets", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--charts", action="store_true")
    a = ap.parse_args()
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    pal = brief.get("palette_custom") or {}
    pal = {"bg": pal.get("bg") or "#FFFFFF", "surface": pal.get("surface") or "#F7F7F5",
           "ink": pal.get("ink") or "#000000", "muted": pal.get("muted") or "#5A5A5A",
           "accent": pal.get("accent") or "#FE7141", "accent_ink": pal.get("accent_ink") or "#000000"}
    assets: dict = {}
    if a.assets and Path(a.assets).exists():
        try:
            assets = json.loads(Path(a.assets).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"assets 解析失败，忽略配图：{e}")
    pages = parse_outline(Path(a.outline).read_text(encoding="utf-8"))
    if not pages:
        print("outline 为空，先跑 outline_builder.py")
        return 2
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    for idx, pg in enumerate(pages):
        num = pg["num"]
        slide = prs.slides.add_slide(blank)
        ink, muted = hex2rgb(pal["ink"]), hex2rgb(pal["muted"])
        # 封面/收尾：accent 色场收尾呼应想法句
        if pg["layout"] == "cover":
            set_bg(slide, hex2rgb(pal["bg"]))
            add_textbox(slide, 0.6, 0.6, 7.0, 0.5, f"{brief.get('industry','')} ｜ {brief.get('scenario','')}", 16, muted)
            add_textbox(slide, 0.6, 1.5, 7.0, 2.4, pg["title"][:36], 40, ink, bold=True)
            add_accent_bar(slide, pal, top=4.0, width=1.4)
            if pg["bullets"]:
                add_bullets(slide, 0.6, 4.5, 7.0, 2.0, pg["bullets"], 18, muted)
            # 右侧：配图或 accent 色块（想法装置位）
            asset = assets.get(f"P{num:02d}", assets.get(str(num), {}))
            if asset.get("image"):
                place_image(slide, Path(asset["image"]), asset.get("kind", "cover"), pal)
            else:
                add_hl_block(slide, 8.2, 0.6, 4.5, 6.3, pal)
                add_textbox(slide, 8.5, 2.8, 3.9, 2.0, "让南瓜\n不再愁生长", 32, hex2rgb(pal["accent_ink"]), bold=True)
        elif pg["layout"] == "closing":
            set_bg(slide, hex2rgb(pal["accent"]))
            ai = hex2rgb(pal["accent_ink"])
            add_textbox(slide, 0.8, 2.0, 11.7, 2.0, pg["title"][:30], 38, ai, bold=True)
            if pg["bullets"]:
                box = slide.shapes.add_textbox(Inches(0.8), Inches(4.4), Inches(11.7), Inches(1.6))
                tf = box.text_frame
                tf.word_wrap = True
                items = content_bullets(pg["bullets"])
                for i, item in enumerate(items[:3]):
                    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    p.text = "• " + re.sub(r"[【】]", "", item[:60])
                    _style_para(p, 20, ai, False, PP_ALIGN.LEFT, space_after=8)
        elif pg["layout"] == "data":
            set_bg(slide, hex2rgb(pal["bg"]))
            nums = extract_numbers(content_bullets(pg["bullets"]))
            add_textbox(slide, 0.6, 0.4, 12.1, 1.2, pg["title"][:32], 30, ink, bold=True)
            use_chart = bool(a.charts and len(nums) >= 2)
            kpi_cards = [] if use_chart else content_bullets(pg["bullets"])[:4]
            if not kpi_cards:
                add_accent_bar(slide, pal)  # KPI 卡片自带顶条时不再画通用横条
            if use_chart:
                add_card(slide, 0.6, 1.9, 12.1, 4.6, pal)
                data = CategoryChartData()
                data.categories = [k for k, _ in nums[:5]]
                data.add_series("数值", [v for _, v in nums[:5]])
                frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.9), Inches(2.1), Inches(7.5), Inches(4.0), data)
                chart = frame.chart
                chart.has_legend = False
                if pg["bullets"]:
                    add_bullets(slide, 8.8, 2.1, 3.8, 4.0, pg["bullets"], 16, ink)
            else:
                # KPI 卡片行：数字放大 + accent 顶条
                cards = content_bullets(pg["bullets"])[:4]
                if cards:
                    w = 12.1 / max(1, len(cards))
                    for ci, card in enumerate(cards):
                        x = 0.6 + ci * w
                        add_card(slide, x + 0.05, 1.9, w - 0.15, 4.4, pal)
                        add_accent_bar(slide, pal, top=1.9, left=x + 0.05, width=w - 0.15)
                        m = re.search(r"(.{1,14})", card)
                        add_textbox(slide, x + 0.25, 2.3, w - 0.5, 3.6, card[:44], 20, ink, bold=True)
                else:
                    add_textbox(slide, 0.6, 6.7, 12.1, 0.4, "[数据图表位：按来源口径补原生图表]", 13, muted)
        elif pg["layout"] == "quote":
            set_bg(slide, hex2rgb(pal["bg"]))
            title = clean_title(pg["title"])[:40]
            add_accent_bar(slide, pal, top=1.4, width=1.4)
            add_textbox(slide, 1.2, 1.9, 10.9, 2.6, f"\u201c{title}\u201d", 34, ink, bold=True)
            if pg["bullets"]:
                add_bullets(slide, 1.2, 4.7, 10.9, 1.6, pg["bullets"], 16, muted)
        elif pg["layout"] == "split":
            # split 独立分支（必须在通用 else 之前）：标题永远收窄左栏，避免撞右图
            set_bg(slide, hex2rgb(pal["bg"]))
            asset = assets.get(f"P{num:02d}", assets.get(str(num), {}))
            items = content_bullets(pg["bullets"])
            add_textbox(slide, 0.6, 0.4, 5.6, 1.6, pg["title"][:30], 30, ink, bold=True)
            add_accent_bar(slide, pal)
            if asset.get("image"):
                add_bullets(slide, 0.6, 2.2, 5.6, 4.3, pg["bullets"], 18, ink)
                place_image(slide, Path(asset["image"]), asset.get("kind", "side"), pal)
            elif len(items) >= 2:
                add_hl_block(slide, 0.6, 1.9, 5.2, 2.2, pal)
                add_textbox(slide, 0.9, 2.1, 4.6, 1.8, re.sub(r"[【】]", "", items[0][:60]), 22, hex2rgb(pal["accent_ink"]), bold=True)
                add_bullets(slide, 6.4, 1.9, 6.3, 4.6, items[1:], 17, ink)
            else:
                add_bullets(slide, 0.6, 1.9, 11.0, 4.6, pg["bullets"], 18, ink)
        else:
            # 内容页：左文右图（有图）/ surface 卡片组（无图多条）/ 单栏（少条）
            set_bg(slide, hex2rgb(pal["bg"]))
            asset = assets.get(f"P{num:02d}", assets.get(str(num), {}))
            items = content_bullets(pg["bullets"])
            has_img = bool(asset.get("image"))
            tw = 5.6 if has_img else 12.1
            add_textbox(slide, 0.6, 0.4, tw, 1.2, pg["title"][:30], 30, ink, bold=True)
            if not (len(items) >= 3 and not has_img):
                # 有图时横条紧跟标题（top=1.7），不压正文
                add_accent_bar(slide, pal, top=1.7 if has_img else 3.42)
            if has_img:
                add_bullets(slide, 0.6, 2.2, 5.6, 4.3, pg["bullets"], 18, ink)
                place_image(slide, Path(asset["image"]), asset.get("kind", "side"), pal)
            elif len(items) >= 3:
                w = 12.1 / len(items[:3])
                for ci, card in enumerate(items[:3]):
                    x = 0.6 + ci * w
                    add_card(slide, x + 0.05, 1.9, w - 0.15, 4.6, pal)
                    if ci == 0:
                        add_accent_bar(slide, pal, top=1.9, left=x + 0.05, width=w - 0.15)
                    add_textbox(slide, x + 0.25, 2.2, w - 0.5, 4.0, re.sub(r"[【】]", "", card[:60]), 18, ink)
            else:
                add_bullets(slide, 0.6, 1.9, 11.0, 4.6, pg["bullets"], 18, ink)
        # 页脚
        add_textbox(slide, 0.6, 7.0, 12.1, 0.3, f"{brief.get('topic','')} ｜ P{idx+1:02d}", 10, muted)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    prs.save(a.out)
    hits = sum(1 for p in pages if ("P%02d" % p["num"]) in assets or str(p["num"]) in assets)
    print(f"deck 已生成：{a.out}（{len(pages)} 页，assets 命中 {hits} 页）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
