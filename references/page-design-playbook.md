# P3 逐页设计指南 v2.1（16 role + cover 四式 + P/M/A/C + topo）

每页按"构图→色彩→配图→关系"四步定计（design-notes.md 一页四行），再搭建。

## 构图库 16 role（相邻页必异；全串三现同形即模板）

| role | 两式（取一） | 适用 |
|---|---|---|
| cover | ① 名碑式：关键词 16–24vw 成建筑 + 角落小字 ② 句槽式：4–7 词通栏 + 词间图槽 | 封面（hook 必填） |
| agenda | ① 横向 3–4 步 + 当前高亮 ② 整场色 + 大字 list | 目录 |
| statement | ① 巨字左 + 一条证据小字 ② 居中两行 + support | 立论、金句 |
| bullets | ① 首卡色场 + 余两大字 list（禁三等分卡行）② 大字 list（40–84px 名 + 右栏释） | 并列要点 |
| split | ① 左 accent 块大字 + 右 bullets ② 左图右栏（图 50% + 窄栏 ≤46ch） | 方案、壁垒 |
| data | ① KPI 卡片行（首卡顶条）② 原生柱状图 + 右解读 | 数据、融资额 |
| timeline | ① 横向 Q1→Q4 节点圆点 ② 阶梯句（First… 缩进） | 计划 |
| quote | ① 居中大引言 + 小字出处 ② 双色块对接（5/7 开） | 愿景 |
| closing | ① 整页 accent 场 + 反白大字 ② 反白封面复现 | 收尾（takeaway 必填） |
| gallery | ① 空地双图错层 ② 标本 mosaic（同尺同角） | 多案例/多 SKU |
| list | ① 一字号表（20–30px 四栏）② 右半段 + 孤图 | 名录/清单 |
| pricing | ① 价即 display（120–240px）② 双巨词对决 | 定价/融资额 |
| testimonial | ① 引文 + 名钉左下 ② 名流成句连写 | 证言（proof 有源才用） |
| faq | ① 问答并栏（问左答右）② 全开问 + 小答 | Q&A |
| proof | ① 一数霸屏 + 单位上标 ② 图作脊 + 版围图走 | 证据 |
| stats | ① 一数霸屏 ② small-multiples | 指标 |

## 色彩动作（每页至少 1 个）

- 整页换场：closing 必 accent 场；章节页可选 surface/章场色（硬切，相邻明度跳）。
- 卡片：≥3 条并列 → surface 卡片组，首卡 accent 顶条（禁三等分同形卡行）。
- 高亮：【】词 → accent 衬底块 + 反白字；场上字用场 ink（muted 不上场）。
- 占比：accent 每屏 ≤2 处；全 deck 同 token 一起换。

## 配图动作 P/M/A/C（quote/closing 纯字色场可免）

1. 用户图最优先 → 联网图（搜 inventory 词）→ 现画 SVG（motif 按语义，progress 随页递增）。
2. scrim 四式：定向 0.88→0.30→0 守字侧 / 底 fade 0→0.72 托底题 / vignette 烘气 / 品牌 wash；禁全图匀罩。
3. 同比同处理同方角（二选一）；拉伸/灰盒/冒充见即打回。
4. SVG 不计 floor + 须配数/结论；真图 floor：10–17 页 deck ≥4。
5. assets.json 五字段：`image/kind/source/license/credit(+crop/treatment)`；外来图下载进仓 + 页脚署名 + 报告列。

## 关系 → topo（第 4 行）

`order/link/parent/membership/contrast/overlap/none → topo yes/no`。yes 走结构件（时间线/流程/矩阵/对比/层级），no 走 base。缺行先修大纲。

## 白纸黑字门

三无（无图、无色块、无高亮）→ 打回。豁免：quote/closing 纯字色场（巨字+色场撑满）。
