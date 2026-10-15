#!/usr/bin/env python3
"""配图管道：SVG/远程图 -> 本地 PNG（python-pptx 只吃位图）-> 登记 assets.json。

- SVG 用 LibreOffice 转 PDF 再渲 PNG（本机已验证链路），无需 cairosvg
- 远程图直下；SVG 字符串也可经 --svg-inline 传
Usage:
    python3 prepare_assets.py --assets ./ppt-work/assets.json --workdir ./ppt-work --images ./images
    # assets.json 形如 {"P05": {"svg": "./images/art-p05.svg", "kind": "side"}, "P07": {"image": "https://...", "kind": "side"}}
"""
import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

NODE = "/Applications/DeepSeek Harness.app/Contents/Resources/runtime/primary-runtime/dependencies/node/bin/node"
CLI = "/Applications/DeepSeek Harness.app/Contents/Resources/app.asar.unpacked/dsh/node_modules/@deepseek-ai/libreoffice-kit/lib/cli.js"


def run(*args: str) -> str:
    r = subprocess.run([NODE, CLI, *args], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {r.stderr[:500]}")
    return r.stdout


def svg_to_png(svg: Path, png: Path) -> None:
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        out = subprocess.run(
            [str(chrome), "--headless", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=/tmp/chrome-svg",
             "--hide-scrollbars", f"--screenshot={png}", "--window-size=800,600",
             f"file://{svg.resolve()}"],
            capture_output=True, text=True, timeout=120)
        if png.exists() and png.stat().st_size > 1000:
            return
        raise RuntimeError(f"chrome screenshot failed: {out.stderr[:300]}")
    # 无 Chrome 时退回 LibreOffice 管道（部分版本不支持 svg→pdf）
    tmp = svg.parent / (svg.stem + "-tmp.pdf")
    run("convert", "--input", str(svg), "--output", str(tmp))
    out_dir = png.parent / (png.stem + "-render")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(run("render", "--input", str(tmp), "--output-dir", str(out_dir), "--pages", "1", "--dpi", "150"))
    src = Path(manifest["images"][0]["path"])
    shutil.move(str(src), str(png))
    shutil.rmtree(out_dir, ignore_errors=True)
    try:
        tmp.unlink()
    except OSError:
        pass


def fetch(url: str, dest: Path) -> bool:
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
    ap.add_argument("--assets", required=True)
    ap.add_argument("--workdir", default="./ppt-work")
    ap.add_argument("--images", default="./images")
    a = ap.parse_args()
    reg = Path(a.assets)
    if not reg.exists():
        print("无 assets.json，跳过配图管道")
        return 0
    data = json.loads(reg.read_text(encoding="utf-8"))
    imgdir = Path(a.images)
    imgdir.mkdir(parents=True, exist_ok=True)
    changed = False
    for page, item in data.items():
        if not isinstance(item, dict):
            continue
        if item.get("svg") and not item.get("image"):
            svg = Path(item["svg"])
            if not svg.exists():
                print(f"{page} svg 不存在：{svg}，跳过")
                continue
            png = imgdir / (svg.stem + ".png")
            if not png.exists():
                svg_to_png(svg, png)
                print(f"{page} SVG→PNG：{png}")
            item["image"] = str(png)
            changed = True
        elif isinstance(item.get("image"), str) and item["image"].startswith("http"):
            dest = imgdir / f"web-{page}.jpg"
            if not dest.exists() and fetch(item["image"], dest):
                print(f"{page} 远程图已下载：{dest}")
                item["image"] = str(dest)
                changed = True
    if changed:
        reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"配图管道完成，共 {len(data)} 页登记")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
