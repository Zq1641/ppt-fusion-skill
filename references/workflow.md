# 全程工作流与门控（workflow v2.1）

## 阶段与阻塞门

| 阶段 | 产物 | 门 |
|---|---|---|
| P1 脑爆对齐+盘点 | `brief.json`（13 问 / 11 必填，含 inventory/reading_mode/mode） | ⛔ 用户亲口"确认开工" |
| P2 设计定稿 | Mode + 方向卡（`direction.json` 含 seed）+ palette（含中性层）+ `outline.md`（五栏：claim/proof/move/关系/内容） | ⛔ 用户确认"方向+大纲"（含竞品 test 口述） |
| P3 搭建 | `deck-v*.pptx`（design-notes 四行/页：构图/色彩/配图/关系→topo） | 内部门：lint CLEAN + 大纲页数一致才开工 |
| P4 自检 | `selfcheck.md`（机器 PASS + 14 passes + 落字 ROUND） | ⛔ 不 PASS 不进 P4-final |
| **P4-final 首席质检** | `qa-shot/`（逐页截屏）+ 打分 + 打回单/验收报告 + `qa-round.json` | ⛔ **平均分 ≥9.0 才放行 P5**；<9.0 打回 P3 复审（最多 3 轮）；>3 轮熔断交付最高分版 + 遗憾说明 |
| P5 导出 | 终版 PPTX / PDF + 设计说明（十项）+ 验收报告 | 前置：P4-final 已放行 |

## P4-final 循环机制（Condition/Loop）

```text
Step1 截屏 → Step2 7维打分 → Step3 判定
   ├─ avg < 9.0 且 round ≤ 3 → 打回单 → 回 P3 修 → round+1 → 回 Step1
   ├─ avg < 9.0 且 round > 3 → 熔断：交付最高分版 + 质检遗憾说明
   └─ avg ≥ 9.0 → 验收报告 → 放行 P5
```

- 打分维度：D1 内容文字 / D2 独立骨架 / D3 风格契合 / D4 视觉焦点 / D5 色彩可读 / D6 排版空间 / D7 逻辑连贯。
- D2 零容忍：枯燥纯文本列表页、与上一页完全同骨架页 → D2=0 + 强制重做。
- 轮次与分数写 `qa-round.json`；截屏链路写 `qa-shot/chain.txt`（直渲 / PPTX→PDF→PDF 中转）。
- 防死循环：`MAX_RETRIES = 3`，由 `qa_director.py --verdict` 自动熔断。

## 不盲猜清单（遇到即问）

文案口径、数字口径、图片归属、品牌色 hex、Logo 用法、演讲时长与字量、保密红线。证明类内容无来源留空 `[待用户提供]`，不编。sample 可编满密度 + 报告待换；proof 留空待提供。

## 品牌 allow（单项放行）

品牌 VI 自带禁色/禁形（如紫渐变/玻璃）时：保留品牌资产 + 自检单项放行 + 报告声明，不扩散到全 deck。

## 失败回退指针

- 文本门 lint FAIL→回 P2 改大纲（删词/换形/删页），不进 P3。
- 页面越界/重叠/溢出→回 P3 修该页。
- 页数/格式/语言与 brief 不符→回 P2 改大纲或回 P1 改 brief（改 brief 重走确认）。
- 对比度/配色看不清→回 P2 换 palette token，全 deck 同 token 一起换。
- 品牌 token 冲突→不碰图，记 needs_human 等用户拍板。
- 渲染失败/字体缺失→先修环境再重渲（字体未载则截图作废），不交付未看过的页。
- 同形三现/无焦点页→回 P3.1 重定该页（换 layout/motif 变体），不是全 deck 重做。
- P4-final 打回→按打回单逐页修（修在拥有层：页面回 P3，大纲缺件回 P2）；改完重跑 P4 机器门再回 Step 1 复审。
- P4-final 连续 3 轮不达标→熔断交付最高分版 + 遗憾说明，并列后续建议（补真图/换方向卡/加 breathing 页）。

## 版本纪律

`deck-v1/v2…` 递增，`brief.json` 改一处即升版并重走确认；`selfcheck.md` 每次全量重跑；`qa-round.json` 记录质检轮次与分数（每轮追加，不覆盖）；`direction.json` 存 seed，连续项目避重样（redraw 记理由）。
