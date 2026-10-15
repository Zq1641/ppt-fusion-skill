#!/usr/bin/env python3
"""P2 palette recommender: recommend 3 directions, lock 1 into brief.json.

Usage:
    python3 palette.py --recommend --industry 科技 --scenario 融资路演 --workdir ./ppt-work
    python3 palette.py --list --workdir ./ppt-work
    python3 palette.py --lock executive-navy --workdir ./ppt-work
"""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

REC_MAP = {
    "融资": ["executive-navy", "ink-paper", "midnight-signal"],
    "汇报": ["executive-navy", "ink-paper", "slate-teal"],
    "发布": ["midnight-signal", "cobalt-field", "ink-paper"],
    "培训": ["paper-leaf", "ink-paper", "slate-teal"],
    "答辩": ["ink-paper", "executive-navy", "paper-leaf"],
    "提案": ["executive-navy", "warm-stone", "midnight-signal"],
}


def load_palettes():
    return json.loads((BASE / "assets" / "palettes.json").read_text(encoding="utf-8"))


def recommend(industry: str, scenario: str):
    pals = {p["id"]: p for p in load_palettes()}
    ids = None
    for k, v in REC_MAP.items():
        if k in (scenario or ""):
            ids = v
            break
    if ids is None:
        ids = ["executive-navy", "ink-paper", "midnight-signal"]
    return [pals[i] for i in ids if i in pals]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recommend", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--lock", default="")
    ap.add_argument("--industry", default="")
    ap.add_argument("--scenario", default="")
    ap.add_argument("--workdir", default="./ppt-work")
    a = ap.parse_args()
    if a.list:
        for p in load_palettes():
            print(f"{p['id']}: {p['name']} bg={p['bg']} ink={p['ink']} accent={p['accent']} — {p['note']}")
        return 0
    if a.recommend:
        recs = recommend(a.industry, a.scenario)
        print("推荐 3 个调色板方向（浅/深搭配），请选 1 个 --lock：")
        for i, p in enumerate(recs, 1):
            print(f"[{i}] {p['id']} — {p['name']}")
            print(f"    bg={p['bg']} surface={p['surface']} ink={p['ink']} muted={p['muted']} accent={p['accent']} accent_ink={p['accent_ink']}")
            print(f"    {p['note']}")
        return 0
    if a.lock:
        pals = {p["id"]: p for p in load_palettes()}
        if a.lock not in pals:
            print(f"未知 palette id：{a.lock}，用 --list 查看")
            return 2
        wd = Path(a.workdir)
        bf = wd / "brief.json"
        if not bf.exists():
            print("先跑 brief_wizard.py --init")
            return 2
        import json as j
        data = j.loads(bf.read_text(encoding="utf-8"))
        p = pals[a.lock]
        data["palette_id"] = p["id"]
        data["palette_custom"] = {k: p[k] for k in ("bg", "surface", "ink", "muted", "accent", "accent_ink")}
        bf.write_text(j.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已锁定 {p['id']} 到 brief.json")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
