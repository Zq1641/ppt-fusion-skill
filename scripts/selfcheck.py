#!/usr/bin/env python3
"""P4 selfcheck v2.1: machine gate (H1-H7 + S1-S6 + R receipt + floor + 落字格式），交付门在 P4-final（qa_director.py）。

Usage:
    python3 selfcheck.py --pptx ./ppt-work/deck-v1.pptx --brief ./ppt-work/brief.json \\
        --assets ./ppt-work/assets.json --report ./ppt-work/selfcheck.md
"""
import argparse
import json
import re
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu


def lum(rgb) -> float:
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c(rgb[0]), c(rgb[1]), c(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg) -> float:
    l1, l2 = lum(fg), lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def shape_bg(shape, slide_bg):
    """读形状 fill 色（色场/卡片），读不到回 slide 底。"""
    try:
        return tuple(shape.fill.fore_color.rgb)
    except Exception:
        return slide_bg


def rect_of(shape):
    try:
        return (Emu(shape.left).inches, Emu(shape.top).inches,
                Emu(shape.width).inches, Emu(shape.height).inches)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--assets", default="")
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    assets = {}
    if a.assets and Path(a.assets).exists():
        try:
            assets = json.loads(Path(a.assets).read_text(encoding="utf-8"))
        except Exception:
            pass
    prs = Presentation(a.pptx)
    SW = Emu(prs.slide_width).inches
    SH = Emu(prs.slide_height).inches
    hard, soft, receipt = [], [], []
    n = len(prs.slides)
    n_min = int(brief.get("page_count_min") or 0)
    n_max = int(brief.get("page_count_max") or 0)
    if n_min and n_max and not (n_min <= n <= n_max):
        hard.append(f"H5 页数不符：实际 {n}，brief 要求 {n_min}-{n_max}")
    texts = []
    sizes = set()
    h3_pairs = 0
    for i, slide in enumerate(prs.slides, 1):
        try:
            slide_bg = tuple(slide.background.fill.fore_color.rgb)
        except Exception:
            slide_bg = (255, 255, 255)
        rects = []
        for shape in slide.shapes:
            r = rect_of(shape)
            if r is None:
                continue
            x, y, w, h = r
            # H1 越界
            if x < -0.02 or y < -0.02 or x + w > SW + 0.02 or y + h > SH + 0.02:
                hard.append(f"H1 P{i:02d} 越界：{shape.name}（{x:.2f},{y:.2f},{w:.2f}x{h:.2f}）")
            rects.append((shape.name, r, shape))
            if not shape.has_text_frame:
                continue
            tf = shape.text_frame
            full = "".join(run.text for p in tf.paragraphs for run in p.runs)
            is_footer = "｜ P" in full
            # H2 溢出近似：字数×字号面积 vs 框面积（auto-fit 缩字不救，另判）
            # H2 auto-fit：只有 TEXT_TO_FIT_SHAPE（缩字藏溢出）才判负；
            # SHAPE_TO_FIT_TEXT（框随字长，python-pptx 默认）与 NONE 允许
            try:
                from pptx.enum.text import MSO_AUTO_SIZE
                autofit = tf.auto_size
                shrink = (autofit == MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE)
            except Exception:
                shrink = False
            if shrink:
                hard.append(f"H2 P{i:02d} auto-fit 缩字藏溢出：{shape.name} → 删词或分页（宁删词不缩字）")
            chars = len(full.strip())
            if chars > 40 and w > 0.1 and h > 0.1:
                # 粗估：一字≈0.28in(20pt)，行≈0.35in
                need_h = max(1, round(chars * 0.28 / max(w, 0.5))) * 0.38
                if need_h > h + 0.6 and chars > 120:
                    hard.append(f"H2 P{i:02d} 疑似溢出：{shape.name}（{chars}字 vs 框高{h:.1f}in）→ 删词或分页")
            for para in tf.paragraphs:
                for run in para.runs:
                    if run.text.strip():
                        texts.append(run.text.strip())
                    try:
                        sz = run.font.size.pt if run.font.size else None
                    except Exception:
                        sz = None
                    if sz:
                        sizes.add(round(sz))
                        if not is_footer:
                            if sz < 13:
                                hard.append(f"H-S6 P{i:02d} 字号过小硬门（{sz:.0f}pt<13pt）：{run.text[:12]}")
                            elif sz < 16:
                                soft.append(f"S6 P{i:02d} 正文偏小（{sz:.0f}pt<16pt）：{run.text[:12]}")
                    # H4 对比度：run 色 vs 形状底（色场/卡片），无 scrim 图字另由人工判
                    try:
                        rgb = run.font.color.rgb
                    except Exception:
                        rgb = None
                    if run.text.strip() and rgb is not None:
                        fg = tuple(rgb)
                        bg = shape_bg(shape, slide_bg)
                        cr = contrast(fg, bg)
                        size = sz or 18
                        need = 3.0 if size >= 24 else 4.5
                        if cr < need:
                            soft.append(f"H4/S-对比度 P{i:02d}（{cr:.1f}:1，需 ≥{need}）：{run.text[:14]}")
        # H3 重叠：两个文本框两两相交（装饰线/页脚/卡片+卡内字除外）。
        # 卡片+卡内字是父子叠放：小框被大框包含≥80% 面积即豁免（包含非重叠）。
        boxes = [(nm, r) for nm, r, sh in rects if sh.has_text_frame]
        for k in range(len(boxes)):
            for m in range(k + 1, len(boxes)):
                (n1, (x1, y1, w1, h1)), (n2, (x2, y2, w2, h2)) = boxes[k], boxes[m]
                if w1 < 0.3 or h1 < 0.2 or w2 < 0.3 or h2 < 0.2:
                    continue
                ix = min(x1 + w1, x2 + w2) - max(x1, x2)
                iy = min(y1 + h1, y2 + h2) - max(y1, y2)
                if ix > 0.15 and iy > 0.15:
                    a1, a2 = w1 * h1, w2 * h2
                    inter = ix * iy
                    if inter / min(a1, a2) > 0.8:
                        continue  # 父子包含（卡片+卡内字），豁免
                    h3_pairs += 1
                    if h3_pairs <= 8:
                        hard.append(f"H3 P{i:02d} 重叠：{n1} × {n2}（交叠 {ix:.2f}×{iy:.2f}in）")
    if not texts:
        hard.append("H6 空 deck：未提取到任何文字")
    # S6 全 deck 档数
    if len(sizes) > 5:
        soft.append(f"S6 全 deck 字号 {len(sizes)} 档>5 档（{sorted(sizes)}）→ 并档")
    # H6 真图 floor（assets 登记的本地图；SVG/图标不计，由 assets kind 区分：image 即真图）
    real = sum(1 for _, it in assets.items()
               if isinstance(it, dict) and it.get("image") and not str(it.get("image", "")).endswith(".svg"))
    if n >= 10 and real < 4:
        hard.append(f"H6 真图 floor 未达：整 deck 真图 {real} <4（SVG/图标不计）→ 补真图或现画配数 SVG")
    # R 级 receipt
    receipt.append(f"真图 {real}（floor 4；SVG/图标不计）")
    receipt.append("渐变/题内变体：机器未扫 → 人工 pass7/ rubric H14 确认")
    receipt.append("topo 页：见 design-notes 第4行；关系页未 topo 的须在此写理由")
    receipt.append("live thing：见设计说明；无 live 则 creativity cap ≤7.5")
    verdict = "PASS" if not hard else "FAIL"
    rep = [f"# 自检报告（{verdict}）", "",
           f"- 文件：{a.pptx}", f"- 页数：{n}（要求 {n_min}-{n_max}）",
           f"- 提取文字片段：{len(texts)}，字号档：{sorted(sizes)}", "",
           "## 硬规则",
           *([f"- [ ] {h}" for h in hard] if hard else ["- [x] 无硬规则命中"]), "",
           "## 软规则",
           *([f"- [ ] {s}" for s in soft] if soft else ["- [x] 无软规则命中"]), "",
           "## R 级 receipt（缺席写理由）",
           *[f"- [ ] {r}" for r in receipt], "",
           "## 人工门 14 passes（逐页看渲染图，只看图不看代码）",
           "- [ ] P1 一秒（页页唯一物）/ P2 眯眼（缩略图墙）/ P3 遮标 / P4 左缘2-3线",
           "- [ ] P5 空间 / P6 字 / P7 色占比accent≤2 / P8 图floor同比",
           "- [ ] P9 同形全串三现cap / P10 手机传阅 / P11 饱满白纸黑字门 / P12 实质",
           "- [ ] P13 碰撞 / P14 竞品+live",
           "",
           "## 落字（critique ROUND）",
           "```text",
           "ROUND 1",
           "Seen in one second:",
           "Idea:",
           "Live thing:",
           "Layout words:",
           "Scores: design _ · usability _ · creativity _ · content _ → overall _._",
           "Caps applied:",
           "Top3:",
           "```",
           "",
           ("结论：FAIL，回 P3 修复后再重跑本脚本，不交付。"
            if verdict == "FAIL" else "结论：机器门 PASS；人工 14 passes 全勾 + 落字后方可交付。")]
    Path(a.report).write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
