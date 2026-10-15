#!/usr/bin/env python3
"""P2 outline builder v2.1: brief(含 mode/reading_mode/inventory) + sources -> outline.md

输出每页五栏（build_deck 只把「内容：」上屏，其余为元行）：
    ## P03 [split] <标题（按 Mode 声口）>
    - claim：一句话断言（本页论点，按 Mode 声口写）
    - proof：证据/数据；无源则 [待用户提供]
    - move：观众前→后状态（Audience move）
    - 关系：order|link|parent|membership|contrast|overlap|none（→ 供 P3 判 topo）
    - 内容：上屏要点（【】标高亮词，｜分隔多条）

不做机械 layout 轮转：按 Mode 偏好选布局，且避免相邻重复与同形三现。
Usage:
    python3 outline_builder.py --brief ./ppt-work/brief.json --sources ./sources --out ./ppt-work/outline.md
"""
import argparse
import json
import re
from pathlib import Path

MODE_LAYOUTS = {
    "narrative": ["statement", "split", "data", "timeline", "quote", "split", "bullets"],
    "pyramid": ["statement", "data", "split", "bullets", "data", "matrix", "quote"],
    "instructional": ["agenda", "bullets", "split", "timeline", "data", "bullets", "quote"],
    "showcase": ["gallery", "statement", "data", "quote", "gallery", "split", "quote"],
    "briefing": ["agenda", "bullets", "list", "data", "list", "bullets", "quote"],
}
MODE_TITLE_HINT = {
    "narrative": "标题是推进弧的 beat（如“然后数字对不上了”）",
    "pyramid": "标题即结论断言（如“留存而非获客驱动增长”）",
    "instructional": "标题=教什么（每页一学习单元）",
    "showcase": "标题短促、图数领衔",
    "briefing": "标题是 topic label，不造结论",
}
REL_BY_LAYOUT = {
    "timeline": "order", "data": "contrast", "split": "contrast", "matrix": "contrast",
    "list": "membership", "bullets": "membership", "gallery": "membership",
    "agenda": "order", "quote": "none", "statement": "none", "cover": "none", "closing": "none",
}


def read_sources(src: Path, limit_chars: int = 30000) -> str:
    if not src.exists():
        return ""
    parts = []
    for f in sorted(src.iterdir()):
        if f.suffix.lower() in (".md", ".txt", ".csv"):
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            parts.append(f"\n[source: {f.name}]\n{t[:8000]}")
    return "\n".join(parts)[:limit_chars]


def split_claims(text: str):
    lines = [l.strip("-•* \t") for l in text.splitlines()]
    lines = [l.strip() for l in lines if len(l.strip()) >= 8]
    heads = [l for l in lines if re.match(r"^#{1,4}\s+", l)]
    if heads:
        return [re.sub(r"^#{1,4}\s+", "", h) for h in heads]
    joined = " ".join(lines)
    return [s.strip() for s in re.split(r"[。！？\n]", joined) if len(s.strip()) >= 8]


def pick_layout(mode: str, i: int, used: list) -> str:
    """按 Mode 偏好选，避开相邻重复与同形三现。"""
    pool = MODE_LAYOUTS.get(mode, MODE_LAYOUTS["narrative"])
    for k in range(len(pool)):
        cand = pool[(i + k) % len(pool)]
        if used and cand == used[-1]:
            continue
        if used.count(cand) >= 2:
            continue
        return cand
    return pool[i % len(pool)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--sources", default="./sources")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    n_min = int(brief.get("page_count_min") or 12)
    n_max = int(brief.get("page_count_max") or 15)
    n = max(5, min(40, (n_min + n_max) // 2))
    topic = brief.get("topic", "未命名主题")
    outcome = brief.get("expected_outcome", "")
    mode = (brief.get("mode") or "narrative").strip()
    reading = (brief.get("reading_mode") or "balanced").strip()
    inventory = [s.strip() for s in re.split(r"[;；]", str(brief.get("inventory") or "")) if s.strip()]
    claims = split_claims(read_sources(Path(a.sources)))

    pages = []  # (layout, title, claim, proof, move, rel, content)
    pages.append(("cover", topic,
                  f"{topic}（目标：{outcome}）",
                  f"inventory 最强物：{inventory[0] if inventory else '[待用户提供]'}",
                  "陌生→想听下去（hook 已抓注意）",
                  "none",
                  f"【{topic}】｜一句话是什么/给谁/要什么"))
    if n >= 6:
        pages.append(("agenda", "路线图",
                      f"全篇走「{mode}」节奏：先立张、再给据、后给行动",
                      "各章 claim 一览",
                      "无地图→知道要去哪",
                      "order",
                      "三段式预告：【愁什么】→【怎么解】→【要什么】"))
    used = [p[0] for p in pages]
    idx = 0
    while len(pages) < n - 1:
        layout = pick_layout(mode, len(pages), used)
        if layout in ("cover", "closing", "agenda"):
            layout = "split"
        if idx < len(claims):
            claim = claims[idx][:40]
            idx += 1
            proof = "来源论据 2-3 条（引用来源即可，勿扩写）"
        else:
            claim = f"待补判断 {len(pages)}"
            proof = "[待用户提供]"
        hint = inventory[len(pages) % len(inventory)] if inventory else topic
        rel = REL_BY_LAYOUT.get(layout, "none")
        pages.append((layout,
                      claim,
                      claim,
                      proof,
                      f"未意识到→接受「{claim[:12]}」",
                      rel,
                      f"【{hint}】｜{claim}｜证据：{proof}"))
        used.append(layout)
    pages.append(("closing", "下一步行动",
                  f"回到目标（{outcome}）",
                  "决策事项 / 联系方式 / 一页总结（三选一，[待用户提供]）",
                  "被说服→知道下一步做什么",
                  "none",
                  f"【{outcome}】｜{topic}｜行动与联系方式（[待用户提供]）"))

    out = [f"# 大纲：{topic}", "",
           f"页数：{len(pages)}（brief 要求 {n_min}-{n_max}）｜Mode：{mode}｜阅读态：{reading}",
           f"标题声口：{MODE_TITLE_HINT.get(mode, '')}",
           f"inventory：{'；'.join(inventory) if inventory else '[待用户提供]'}",
           "", "> 每页五栏：claim（断言）/ proof（证据，勿编）/ move（观众前→后）/ 关系（→P3 判 topo）/ 内容（上屏，【】高亮）。", ""]
    for i, (layout, title, claim, proof, move, rel, content) in enumerate(pages, 1):
        out.append(f"## P{i:02d} [{layout}] {title}")
        out.append(f"- claim：{claim}")
        out.append(f"- proof：{proof}")
        out.append(f"- move：{move}")
        out.append(f"- 关系：{rel}")
        out.append(f"- 内容：{content}")
        out.append("")
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print(f"大纲已生成：{a.out}（{len(pages)} 页，Mode={mode}）")
    if not inventory:
        print("提示：brief 缺 inventory（Q0），想法句与配图查询将无原料 → 回 P1 补。")
    if not claims:
        print("提示：未读到来源内容，proof 均为 [待用户提供]，请在 P2 确认时补齐。")
    elif idx >= len(claims):
        print("提示：来源论点已用完，部分页 proof 标 [待用户提供]，请在 P2 确认时补齐。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
