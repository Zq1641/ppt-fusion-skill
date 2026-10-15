#!/usr/bin/env python3
"""P3-B 联网配图：优先 firecrawl_cli，无网络/无 key 时如实报错并提示走 C 路（现画 SVG）。

Usage:
    python3 fetch_images.py --query "南瓜 农场 秋收" --out ./images --max 3
    python3 fetch_images.py --query "pumpkin farm harvest" --out ./images --max 3 --register ./ppt-work/assets.json --page P05 --kind side
"""
import argparse
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path


def try_firecrawl_urls(query: str, n: int) -> list[str]:
    # firecrawl search 返回 json，取外链图片 URL；失败返回 []
    try:
        r = subprocess.run(["firecrawl", "search", query, "--limit", "8"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return []
        urls = []
        for line in r.stdout.splitlines():
            for tok in line.split():
                t = tok.strip('",')
                if t.startswith("http") and any(t.lower().split("?")[0].endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp")):
                    urls.append(t)
        seen, out = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
        return dest.stat().st_size > 20000
    except Exception:
        if dest.exists():
            dest.unlink()
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--out", default="./images")
    ap.add_argument("--max", type=int, default=3)
    ap.add_argument("--register", default="")
    ap.add_argument("--page", default="")
    ap.add_argument("--kind", default="side", choices=["cover", "side", "bg", "tile"])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    urls = try_firecrawl_urls(a.query, a.max)
    if not urls:
        print("联网配图不可用（无 firecrawl / 无网络 / 无外链图）→ 请走 C 路：make_svg_art.py 现画 SVG。")
        return 2
    got = []
    for i, u in enumerate(urls):
        dest = out / f"web-{abs(hash(u)) % 10**8}-{i}.jpg"
        if download(u, dest):
            got.append(dest)
            print(f"已下载：{dest} ← {u}")
    if not got:
        print("外链均下载失败 → 请走 C 路现画 SVG。")
        return 2
    if a.register and a.page:
        reg = Path(a.register)
        data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {}
        data[a.page] = {"image": str(got[0]), "kind": a.kind,
                        "source": "web search", "license": "需人工核对商用许可"}
        reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已登记到 {reg}（{a.page} ← {got[0]}；许可待人工核对）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
