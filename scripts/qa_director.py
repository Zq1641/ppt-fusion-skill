#!/usr/bin/env python3
"""P4-final 首席视觉质检总监管道：截屏 + 机器预检 + 轮次循环（Condition/Loop）。

- Step 1 截屏：LibreOffice 直渲 PPTX；黑屏（全黑图）则走 PPTX→PDF→渲PDF 中转；报告声明链路。
- Step 2 机器预检（总监必须从严采纳）：同骨架相邻 / 三无页 / 标题超行 / 溢出可疑 / 真图数。
- Step 3 轮次：qa-round.json 记录 {round, scores, avg, verdict}；avg<9.0 且 round<=3 → 打回；
  round>3 仍<9.0 → 熔断，输出遗憾说明交付最高分版。
Usage:
    python3 qa_director.py --pptx ./ppt-work/deck-v1.pptx --out-dir ./ppt-work/qa-shot --dpi 144
    python3 qa_director.py --precheck --pptx ./ppt-work/deck-v1.pptx --assets ./ppt-work/assets.json --brief ./ppt-work/brief.json
    python3 qa_director.py --verdict --avg 8.6 --round 1 --workdir ./ppt-work
    python3 qa_director.py --accept --avg 9.2 --round 2 --workdir ./ppt-work --dims "D1=9.5,D2=9.0,D3=9.5,D4=9.0,D5=9.0,D6=9.2,D7=9.4"
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from pptx import Presentation

NODE = "/Applications/DeepSeek Harness.app/Contents/Resources/runtime/primary-runtime/dependencies/node/bin/node"
CLI = "/Applications/DeepSeek Harness.app/Contents/Resources/app.asar.unpacked/dsh/node_modules/@deepseek-ai/libreoffice-kit/lib/cli.js"
MAX_RETRIES = 3
TARGET = 9.0


def run(*args: str) -> str:
    r = subprocess.run([NODE, CLI, *args], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {r.stderr[:400]}")
    return r.stdout


def is_black(png: Path) -> bool:
    try:
        from PIL import Image
        im = Image.open(png).convert("L")
        small = im.resize((32, 32))
        px = list(small.getdata())
        return sum(px) / len(px) < 8
    except Exception:
        return png.stat().st_size < 8000


def cmd_shot(args) -> int:
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(run("render", "--input", args.pptx, "--output-dir", str(out),
                              "--dpi", str(args.dpi)))
    imgs = [Path(m["path"]) for m in manifest["images"]]
    chain = "direct-pptx"
    if imgs and all(is_black(p) for p in imgs[:3]):
        # 黑屏：走 PPTX→PDF→渲PDF 中转
        pdf = out.parent / (Path(args.pptx).stem + "-qa.pdf")
        run("convert", "--input", args.pptx, "--output", str(pdf))
        out2 = out.parent / (out.name + "-pdf")
        out2.mkdir(parents=True, exist_ok=True)
        manifest = json.loads(run("render", "--input", str(pdf), "--output-dir", str(out2),
                                  "--dpi", str(args.dpi)))
        for m in manifest["images"]:
            shutil.copy(m["path"], out / Path(m["path"]).name)
        chain = "pptx->pdf->png"
    (out / "chain.txt").write_text(chain, encoding="utf-8")
    print(f"截屏完成：{len(imgs)} 页 → {out}（链路：{chain}）")
    print("总监 Step 1：请逐页看图做 7 维像素级审视（只看图，不看代码）。")
    return 0


def layout_signature(slide) -> str:
    """粗粒度骨架签名：文本框数量级 + 是否有图 + 是否有表/图 + 大字标题长度级。"""
    n_text = sum(1 for sh in slide.shapes if sh.has_text_frame)
    n_pic = sum(1 for sh in slide.shapes if getattr(sh, "shape_type", None) and int(sh.shape_type) == 13)
    has_chart = any(getattr(sh, "has_chart", False) for sh in slide.shapes)
    has_table = any(getattr(sh, "has_table", False) for sh in slide.shapes)
    return f"T{min(n_text,6)}|P{min(n_pic,2)}|C{int(has_chart)}|B{int(has_table)}"


def cmd_precheck(args) -> int:
    prs = Presentation(args.pptx)
    assets = {}
    if args.assets and Path(args.assets).exists():
        try:
            assets = json.loads(Path(args.assets).read_text(encoding="utf-8"))
        except Exception:
            pass
    hits = []
    prev_sig = None
    for i, slide in enumerate(prs.slides, 1):
        sig = layout_signature(slide)
        if sig == prev_sig:
            hits.append(f"同骨架相邻：P{i-1:02d}×P{i:02d}（签名{sig}）→ D2 从严，总监复核是否真同骨架")
        prev_sig = sig
        # 三无页：无图、无色场/卡片（autoshap 矩形）、无【】高亮
        pics = sum(1 for sh in slide.shapes if getattr(sh, "shape_type", None) and int(sh.shape_type) == 13)
        rects = sum(1 for sh in slide.shapes if getattr(sh, "shape_type", None) and int(sh.shape_type) == 1)
        texts = "".join(r.text for sh in slide.shapes if sh.has_text_frame
                        for p in sh.text_frame.paragraphs for r in p.runs)
        if pics == 0 and rects <= 1 and ("【" not in texts):
            hits.append(f"三无嫌疑 P{i:02d}（无图/无色块/无高亮）→ D2/D4 从严，白纸黑字门复核")
        # 标题超行近似：首个大字框（≥24pt）字符>30 告警
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    try:
                        sz = r.font.size.pt if r.font.size else 0
                    except Exception:
                        sz = 0
                    if sz and sz >= 24 and len(r.text.strip()) > 30:
                        hits.append(f"标题超行嫌疑 P{i:02d}（{sz:.0f}pt×{len(r.text.strip())}字）：{r.text[:18]}")
                        break
    real = sum(1 for _, it in assets.items()
               if isinstance(it, dict) and it.get("image") and not str(it.get("image", "")).endswith(".svg"))
    print("== 机器预检（总监必须从严采纳） ==")
    for h in hits:
        print("PRECHECK", h)
    print(f"PRECHECK 真图 {real}（floor 4；SVG/图标不计）")
    if not hits:
        print("PRECHECK CLEAN")
    return 0


def load_rounds(wd: Path) -> list:
    f = wd / "qa-round.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_rounds(wd: Path, rounds: list) -> None:
    wd.mkdir(parents=True, exist_ok=True)
    (wd / "qa-round.json").write_text(json.dumps(rounds, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_verdict(args) -> int:
    """avg<9.0 → 打回单（stdout）+ 记录轮次；round>3 → 熔断遗憾说明。返回码：0=继续循环/熔断交付，1=需重做。"""
    wd = Path(args.workdir)
    rounds = load_rounds(wd)
    rounds.append({"round": args.round, "avg": args.avg, "verdict": "retry"})
    save_rounds(wd, rounds)
    if args.avg >= TARGET:
        print(f"平均分 {args.avg} ≥ {TARGET}：应走 --accept 生成验收报告放行 P5。")
        return 0
    if args.round > MAX_RETRIES:
        print(f"🚨 熔断：已 {args.round - 1} 轮仍 {args.avg} < {TARGET}。")
        print("《质检遗憾说明》：强制输出当前最高分版交付；遗憾页与分差见 qa-round.json；")
        print("建议后续：补真图/换方向卡/加 breathing 页后再战。")
        return 0
    print(f"🚨 质检未通过 | 当前平均分: {args.avg} 分 (目标: ≥ {TARGET}) | 轮次: {args.round}/{MAX_RETRIES}")
    print("请按 reference/qa-director.md【输出格式A】写《质检打回修改指令单》，喂回 P3，改完 --round "
          f"{args.round + 1} 回到 Step 1 复审。")
    return 1


def cmd_accept(args) -> int:
    wd = Path(args.workdir)
    rounds = load_rounds(wd)
    rounds.append({"round": args.round, "avg": args.avg, "dims": args.dims, "verdict": "accept"})
    save_rounds(wd, rounds)
    print(f"🏆 首席品鉴验收通过 | 最终平均分: {args.avg} 分 | 轮次: {args.round}")
    print(f"维度：{args.dims}")
    print("准予放行 P5 交付（验收报告按 reference/qa-director.md【输出格式B】落字）。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", default="")
    ap.add_argument("--out-dir", default="./ppt-work/qa-shot")
    ap.add_argument("--dpi", type=int, default=144)
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--assets", default="")
    ap.add_argument("--verdict", action="store_true")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--avg", type=float, default=0.0)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--dims", default="")
    ap.add_argument("--workdir", default="./ppt-work")
    a = ap.parse_args()
    if a.precheck:
        if not a.pptx:
            print("需 --pptx")
            return 2
        return cmd_precheck(a)
    if a.verdict:
        return cmd_verdict(a)
    if a.accept:
        return cmd_accept(a)
    if not a.pptx:
        ap.print_help()
        return 1
    return cmd_shot(a)


if __name__ == "__main__":
    raise SystemExit(main())
