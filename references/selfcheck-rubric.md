# P4 自检 rubric v2.1（机器门 + 14-pass 人工门 + caps + 三轮落字）

> 适用范围：**P4 搭建者自检**（加权分，救不回的线 7.5）。P4 过关后才进 P4-final 首席质检（7 维均分，交付线 9.0），其规则见 [qa-director.md](qa-director.md)。两套分数不通用、各自计数。

先跑 `lint_outline.py`（文本门）+ `scripts/selfcheck.py`（机器门），再逐页看渲染图（人工门）。任一硬规则命中即 FAIL，回 P3。

## 硬规则 H1–H7（见一处修一处）

- H1 越界：任何形状超出幻灯片边界。
- H2 溢出：文本框装不下文字；**auto-fit 缩字藏溢出判负**（宁删词不缩字）；标题 >2 行判负；末行单字判负。
- H3 重叠：两个文本框/图文相交（矩形相交实检；装饰线除外）。
- H4 对比度：正文 <4.5:1、大字（≥24pt）<3:1；图上文字无 scrim 即判负；muted 上色场判负。品牌 token 冲突不私自改色，记 `needs_human`。
- H5 页数/格式：与 brief 的页数区间、语言、格式不一致。
- H6 缺件：大纲承诺的论点/图表/页码缺失；真图 floor 未达（10–17 页 deck 真图 <4，quote/closing 豁免页除外）。
- H7 事实错：数字与来源不一致、错别字、品牌名错误；编造 proof（客户名言/营收/Logo 墙）见一处即 H7。

## 软规则 S1–S6（明显差才修）

- S1 行距过密（<1.05 倍字号）→ 1.15–1.3；标题上空 ≥ 下空 2 倍。
- S2 大片空洞（非 breathing 页 >1/3 屏无意义留白）→ 收紧或放大主体。
- S3 对齐漂移（同栏 x 差 >4px；跨页同 role 纵线漂移）→ 吸到网格/母线。
- S4 相邻两页同构图 → 换其中一页；全串三现同形 → 换。
- S5 accent 滥用（一屏 >2 处，场-ink 错配）→ 收到 ≤2 处并配对场 ink。
- S6 全 deck 字号 >5 档 / 正文 <16pt / 注 <13pt（页脚 caption 10pt 白名单）→ 重排。

## R 级 carrier-receipt（缺席写理由，"克制/字够了"不是理由）

- `Presets: (none)` → 何物代劳结构？
- 渐变/强调/滤镜为 0 → 何物代劳层次？
- 关系页多于 topo 页 → 为何没结构化？
- 有图标池而 `icons: 0` → 为何不用？
- 无 live thing → creativity cap ≤7.5 照吃，设计说明必填 live 三选一（可交互/可变/可演）。

## 不碰项

品牌色/字体家族、章节结构、已确认文案语义（brief 级 paraphrase 允许，信息等价：Core message/move/事实限定修饰全存活）、其他页。需 reinterpret 大纲的改动记 `needs_human` 并给改法，不私自重写。

## 打分 + caps + 修序 + 三轮（写进报告）

`overall = 0.4·design + 0.3·usability + 0.2·creativity + 0.1·content`。
caps：硬规则未清 ≤6.0；题三行/三卡片/渐变字 ≤6.5；谁家都行 creativity≤6；竞品成立 ≤7；真图<4 design≤6.5；全 deck 无一切换 ≤7；无 live ≤7.5；占位 content≤5；两屏空地/灰小文 design≤6.5；缺 brief 节 content≤6；封面无行动 usability≤7；压标题 ≤6；空带裁切 ≤5。
修序：idea→层级（一页一主物）→构图→字→图→色→细节→动。拆物留坑不填饰。
**P4 三轮封顶**（自检打磨：critique→Top3→重检）；无陌生人可见问题早停；三轮仍<7.5 如实列余问题，然后**照常进入 P4-final**（P4 的 7.5 不是交付线，9.0 才是）。

落字格式：

```text
ROUND n
Seen in one second（每页一句，答"一页PPT"者标红）:
Idea（一句）:
Live thing:
Layout words: P01=cover / P02=…（连两同、三现标红）
Scores: design _ · usability _ · creativity _ · content _ → overall _._
Caps applied:
Top3（最显眼先，每条+页码+修法）:
```
