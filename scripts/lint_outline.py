#!/usr/bin/env python3
"""P2/P4 文本门 lint：跑 outline.md，不碰 PPTX（比 PPT 态拦早一拍）。

检查：标题超长（中文封面>14字/页题>16字≈32字符线）/禁词（unlock系/三顿/纠正式/
reimagined/Welcome/冒号题/题内变体/Step复读/中点串/em-dash成癖/Get started）/
无claim页/三现同形。
Usage: python3 lint_outline.py --outline ./ppt-work/outline.md
"""
import argparse
import re
import sys
from pathlib import Path

BANNED = [
    (r"unlock|unleash|supercharge|elevate|empower|streamline|seamless|effortless|robust|cutting-edge|next-gen|world-class|all-in-one|blazing|赋能|颠覆|抓手|闭环|心智|赛道", "生成味词（unlock系/黑话）"),
    (r"^(Fast|Simple|Secure|更快|更强|更好)[.，、\s]+.*[.，、\s]+.*$", "三顿式标题（Fast. Simple. Secure.）"),
    (r"不止是|不仅仅是|不只是|More than|more than", "纠正式标题（不止是X是Y）"),
    (r"reimagined|Reimagined|Welcome to|Meet |欢迎来到|全新定义", "reimagined/Welcome/Meet式标题"),
    (r"Step\s*\d|Phase\s*\d|第一步|第二步|第三步", "Step/阶段复读"),
    (r"·.*·.*·", "中点串词"),
    (r"Get started|Learn more|了解更多|立即开始", "Get started/Learn more式按钮词"),
]
TITLE_BANNED_SUFFIX = ("：", ":")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outline", required=True)
    a = ap.parse_args()
    lines = Path(a.outline).read_text(encoding="utf-8").splitlines()
    fails, warns = [], []
    layouts = []
    cur = None
    need_rel = {}   # 页标题行号 -> 是否已见「关系：」
    need_content = {}
    for ln, line in enumerate(lines, 1):
        m = re.match(r"##\s*P\d+\s*\[(\w+)\]\s*(.+)", line.strip())
        if m:
            layout, title = m.group(1), m.group(2).strip()
            cur = ln
            need_rel[ln] = False
            need_content[ln] = False
            layouts.append(layout)
            n = len(title)
            limit = 16 if layout == "cover" else 18
            if n > limit:
                fails.append(f"L{ln} 标题超长（{n}字>{limit}）：{title[:24]}… → 删词到{limit}字内（宁删词不缩字）")
            if title.rstrip().endswith(TITLE_BANNED_SUFFIX) or title.count("：") >= 1 and len(title) > 12:
                warns.append(f"L{ln} 冒号题嫌疑：{title[:24]}")
            for pat, why in BANNED:
                if re.search(pat, title):
                    fails.append(f"L{ln} {why}：{title[:30]}")
            if title.startswith("论点") or title.startswith("待补判断") or "待用户补具体论据" in title:
                fails.append(f"L{ln} 无claim页（占位待补）：{title[:24]} → 补claim或删页")
            if "[待用户提供]" in title:
                warns.append(f"L{ln} 标题未落证据（[待用户提供]）：{title[:24]} → P2 确认前补齐")
        elif cur:
            s = line.strip()
            if s.startswith("- 关系："):
                need_rel[cur] = True
            elif s.startswith("- 内容："):
                need_content[cur] = True
    # v2.1 五栏完整性：缺「关系」→ P3 无法判 topo；缺「内容」→ 无上屏要点
    for ln, ok in need_rel.items():
        if not ok:
            fails.append(f"L{ln} 缺「关系」行 → P3 无法判 topo（order|link|parent|membership|contrast|overlap|none）")
    for ln, ok in need_content.items():
        if not ok:
            fails.append(f"L{ln} 缺「内容」行 → 无上屏要点")
    from collections import Counter
    for lay, c in Counter(layouts).items():
        if c >= 3 and lay not in ("bullets", "data"):
            warns.append(f"同形三现：{lay}×{c} → 换其中页的 layout")
    print(f"== lint: {a.outline} ==")
    for f in fails:
        print("FAIL", f)
    for w in warns:
        print("WARN", w)
    if not fails and not warns:
        print("CLEAN：无文本门问题")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
