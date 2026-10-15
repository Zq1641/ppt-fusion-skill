#!/usr/bin/env python3
"""P1 brief wizard: init / set / check a v2.1 brief.json (13 问 / 11 必填 + inventory/reading_mode/mode).

Usage:
    python3 brief_wizard.py --init --topic "..." --workdir ./ppt-work
    python3 brief_wizard.py --set industry=科技 scenario=融资路演 --workdir ./ppt-work
    python3 brief_wizard.py --set inventory="南瓜藤蔓生长线;产地分级标准;500万建仓" --workdir ./ppt-work
    python3 brief_wizard.py --check --workdir ./ppt-work
    python3 brief_wizard.py --confirm --workdir ./ppt-work
"""
import argparse
import json
import re
import sys
from pathlib import Path

FIELDS = ["topic", "industry", "scenario", "audience", "audience_traits",
          "page_count", "style", "palette_id", "expected_outcome",
          "output_format", "source_material_type", "language",
          "inventory", "reading_mode", "mode"]
REQUIRED = ["topic", "audience", "page_count", "style", "output_format",
            "source_material_type", "language", "expected_outcome",
            "inventory", "reading_mode", "mode"]
SEMANTIC = {"topic": "Literal", "audience": "Literal", "inventory": "Identity",
            "expected_outcome": "Semantic", "mode": "Semantic"}
NEXT_QUESTION = {
    "industry": "Q1 行业/领域？选项：科技互联网 / 金融 / 教育 / 医疗健康 / 制造零售 / 政务公共 / 文化创意 / 其他",
    "scenario": "Q2 使用场景？选项：融资路演 / 内部汇报 / 对外提案 / 发布会演讲 / 课程培训 / 学术答辩 / 招投标 / 其他（含：现场讲还是会后阅读？→推导 reading_mode）",
    "audience": "Q3 面对人群？选项：投资人高管 / 客户决策人 / 同事跨部门 / 学生学员 / 评审专家 / 公众用户",
    "audience_traits": "Q4 受众特点？选项：技术懂行 / 业务懂行技术一般 / 完全外行 / 年轻偏好网感 / 严肃偏好稳重 / 时间极少只看结论",
    "page_count": "Q5 页数要求？选项：10页内精简版 / 15-20页标准版 / 30页以上完整版 / 不限你定（示例：15-20）",
    "style": "Q6 风格要求？见 style-cards.md 7 张卡单选：名碑/句版/色章/一motif/静器/暗房/纯字",
    "palette_id": "Q7 配色要求？用 palette.py --recommend 看3个方向后填 id，或填品牌色hex；无要求填：按风格定",
    "expected_outcome": "Q8 预期效果？选项：说服拿单 / 对齐决策 / 讲清理解 / 留存传阅 / 评审过关",
    "output_format": "Q9 输出格式？选项：pptx / pdf / both",
    "source_material_type": "Q10 现有资料？选项：一段想法 / 零散资料 / 现成大纲 / 详细内容文档 / 已有PPTX",
    "topic": "请先给一句话主题（--topic 或 --set topic=...）",
    "language": "语言？示例：zh-CN",
    "inventory": "Q0 主体盘点：8-12 件只属于这个主题、不属于竞品的东西（名字含义/街景/数字/约束/材料/仪式/印刷品），分号隔开",
    "reading_mode": "阅读模式？presentation（一页一断言，解释进备注）/ balanced（默认，一页一主张+简释）/ text（近读自足）",
    "mode": "论证 Mode？narrative（路演弧光，推荐）/ pyramid（结论先行）/ instructional（教学）/ showcase（视觉主导）/ briefing（中性覆盖）",
}


def load_brief(workdir: Path) -> dict:
    f = workdir / "brief.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    tpl = Path(__file__).resolve().parent.parent / "assets" / "brief-template.json"
    base = json.loads(tpl.read_text(encoding="utf-8"))
    return base["fields"]


def save_brief(workdir: Path, data: dict) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    # parse page_count range
    pc = str(data.get("page_count", ""))
    m = re.search(r"(\d+)\s*[-~–—]\s*(\d+)", pc)
    if m:
        data["page_count_min"], data["page_count_max"] = int(m.group(1)), int(m.group(2))
    else:
        m2 = re.search(r"(\d+)", pc)
        if m2:
            n = int(m2.group(1))
            data["page_count_min"], data["page_count_max"] = n, n
    (workdir / "brief.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--set", nargs="*", default=[])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--topic", default="")
    ap.add_argument("--workdir", default="./ppt-work")
    a = ap.parse_args()
    wd = Path(a.workdir)
    data = load_brief(wd)
    if a.init:
        if a.topic:
            data["topic"] = a.topic
        save_brief(wd, data)
        print(f"brief 初始化：{wd / 'brief.json'}")
    for item in a.set:
        if "=" not in item:
            print(f"跳过非法 --set 项：{item}（要用 key=value）", file=sys.stderr)
            continue
        k, v = item.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in FIELDS or k in ("palette_custom", "source_files", "canvas", "delivery_context"):
            data[k] = v
        else:
            print(f"未知字段：{k}", file=sys.stderr)
    if a.set or a.init:
        save_brief(wd, data)
    if a.confirm:
        missing = [k for k in REQUIRED if not str(data.get(k, "")).strip()]
        if missing:
            print("尚不能确认开工，缺：", ", ".join(missing))
            return 2
        data["confirmed"] = True
        save_brief(wd, data)
        print("brief 已确认开工。")
        return 0
    if a.check or True:
        missing = [k for k in FIELDS if k in REQUIRED and not str(data.get(k, "")).strip()]
        optional_missing = [k for k in FIELDS if k not in REQUIRED and not str(data.get(k, "")).strip()]
        print("== brief 现状 ==")
        for k in FIELDS:
            sem = f" [{SEMANTIC[k]}]" if k in SEMANTIC else ""
            print(f"  {k}{sem}: {data.get(k, '')}")
        if not missing:
            print("PASS：必填 11 项齐全，可 --confirm 进入 P2。")
        else:
            print(f"下一问：{NEXT_QUESTION[missing[0]]}")
        if optional_missing:
            print("选填未填：", ", ".join(optional_missing))
        return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
