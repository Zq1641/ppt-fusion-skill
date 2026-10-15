#!/usr/bin/env python3
"""P2.2 发三方向：按 brief 发 3 个设计方向，用户选一锁定为 direction.json。

7 张风格卡（先行子集，含义见 references/style-cards.md）：
  monument(名碑) / sentence(句版) / chapters(色章) / motif(一motif) /
  quiet(静器) / darkroom(暗房) / statement(纯字)
选择标准：最能承载 inventory 独特之物的，而非最顺眼的。
Usage:
    python3 deal_directions.py --brief ./ppt-work/brief.json --options 3
    python3 deal_directions.py --brief ./ppt-work/brief.json --pick 1
    python3 deal_directions.py --show --workdir ./ppt-work
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

CARDS = {
    "monument": {"name": "名为碑", "style": "名碑式封面：名字/关键词 16-24vw 成建筑，余下小而静；反色收束",
                 "color": "两值 carry（地+墨），accent 只打一处行动", "fit": "短名品牌/发布会封面"},
    "sentence": {"name": "句为版", "style": "4-7 词短句即构图，主体物顶替一词（图条/数字槽）",
                 "color": " calm 地 + 墨，颜色只来自槽内图", "fit": "Slogan/立论/一句话 claim 页"},
    "chapters": {"name": "色彩章节", "style": "每节一整面 flat 场，硬切无缝，每场一事，相邻场明度必跳，≤6 场",
                 "color": "场色取主体真色；场内只用场 ink", "fit": "章节体系/培训/年报"},
    "motif": {"name": "一 motif", "style": "主体最简几何三四种悬殊尺度复用全页（图 mask/按钮/分隔同形），一形即一形",
              "color": "地墨 + 一 accent，形即色", "fit": "全 deck 纽带（藤蔓/剖面线/印章角）"},
    "quiet": {"name": "静器", "style": "窄栏偏左，标题唯一大物，正文全墨，一屏 accent 一处",
              "color": "纸 + 墨 + 一深 accent", "fit": "答辩/法务财务确定感"},
    "darkroom": {"name": "暗房", "style": "整页暗场展品感，一屏一两件 lit 物，字减 weight",
                 "color": "near-black 微 tint 地 + 柔白字，无 glow", "fit": "高端演讲/黑场"},
    "statement": {"name": "纯字宣言", "style": "字即图：首屏两行内 9-14vw 站满，色替图",
                  "color": "一饱和整场 / 一反白 / 一 accent 场", "fit": "战略愿景/金句串场"},
}
MODES = {"narrative": "situation→tension→resolution，标题是 beat",
         "pyramid": "结论先行，标题即断言，SCQA",
         "instructional": "每页一学习单元，兄弟平行同构",
         "showcase": "图数领衔，标题短促，情绪节奏",
         "briefing": "标题是 topic label，无 thesis"}


def pick3(brief: dict, seed: str):
    rnd = random.Random(seed)
    ids = list(CARDS)
    # 按 style/mode 粗排：路演 mood 优先 motif/sentence/chapters
    mood = (brief.get("style", "") + brief.get("scenario", ""))
    boost = ["motif", "sentence", "chapters"] if ("路演" in mood or "融资" in mood) else []
    ordered = boost + [i for i in ids if i not in boost]
    rnd.shuffle(ordered[3:])
    return ordered[:3]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", default="")
    ap.add_argument("--options", type=int, default=0)
    ap.add_argument("--pick", type=int, default=0)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--workdir", default="./ppt-work")
    a = ap.parse_args()
    wd = Path(a.workdir)
    if a.show:
        dj = wd / "direction.json"
        if not dj.exists():
            print("尚未锁定方向")
            return 2
        print(dj.read_text(encoding="utf-8"))
        return 0
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    seed = hashlib.sha256(f"{brief.get('topic')}{time.strftime('%Y%m%d')}".encode()).hexdigest()[:8]
    if a.options == 3:
        ids = pick3(brief, seed)
        print(f"发三方向（seed={seed}，Mode={brief.get('mode', 'narrative')}）：")
        for i, cid in enumerate(ids, 1):
            c = CARDS[cid]
            print(f"[{i}] {c['name']}（{cid}）—— {c['style']}")
            print(f"    色：{c['color']}；宜：{c['fit']}")
        print("按 inventory 选最能承载独特之物的（非最顺眼的），再 --pick N 锁定。")
        (wd / "direction-options.json").write_text(
            json.dumps({"seed": seed, "options": ids, "mode": brief.get("mode", "narrative")},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    if a.pick:
        optf = wd / "direction-options.json"
        if not optf.exists():
            print("先 --options 3 发牌")
            return 2
        opts = json.loads(optf.read_text(encoding="utf-8"))
        ids = opts["options"]
        if not (1 <= a.pick <= len(ids)):
            print(f"pick 越界 1-{len(ids)}")
            return 2
        cid = ids[a.pick - 1]
        dj = {"seed": opts["seed"], "card": cid, "mode": opts.get("mode", "narrative"),
              "detail": CARDS[cid], "redraws": []}
        (wd / "direction.json").write_text(json.dumps(dj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已锁定：{CARDS[cid]['name']}（{cid}），存 direction.json")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
