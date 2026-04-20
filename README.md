# Paper-Color

一套适合科研论文主图、补充图和 method schematic 的通用配色库，风格参考 `Nature Communications` 常见的清洁、克制、白底友好视觉语言。

这不是期刊官方发布的标准色卡，而是一套面向科研绘图实践整理出来的 `inspired palette`。目标不是追求视觉噱头，而是让颜色在以下场景里更稳定：

- 结果图：折线图、柱状图、散点图、热图注释色
- 方法图：流程图、模块图、实验装置示意图
- 补充材料：需要大量图但不希望颜色显得杂乱

## 特点

- `24` 组颜色家族，每组 `5` 个层级，从浅到深排列
- 顶部提供 `8` 组推荐搭配，适合快速选色
- 同时提供 `RGB`、`HEX` 和 Adobe Illustrator 可直接输入的 `RGB(r, g, b)`
- 配色按功能分区组织：`Blue / Navy`、`Cyan / Teal`、`Green`、`Earth / Ochre / Sand`、`Red / Rose / Plum`、`Neutral`
- 适合白底论文图，不依赖深色背景成立

## 仓库结构

```text
Paper-Color/
├── README.md
├── .gitignore
├── generate_nature_comm_palette.py
├── assets/
│   ├── nature_comm_scientific_palette.svg
│   ├── nature_comm_scientific_palette.csv
│   └── nature_comm_scientific_palette.md
└── tests/
    └── test_nature_comm_palette.py
```

## 文件说明

- `generate_nature_comm_palette.py`
  - 配色库生成脚本
  - 定义全部颜色家族
  - 定义推荐搭配组合
  - 生成 `SVG / CSV / Markdown`

- `assets/nature_comm_scientific_palette.svg`
  - 主可视化文件
  - 顶部是推荐搭配区
  - 下方是完整配色库

- `assets/nature_comm_scientific_palette.csv`
  - 机器可读表格
  - 适合 Excel、脚本、代码 agent 精确读取

- `assets/nature_comm_scientific_palette.md`
  - 人类可读的文字版总表
  - 方便快速复制颜色信息

- `tests/test_nature_comm_palette.py`
  - 回归测试
  - 保证颜色家族数量、层级结构、推荐组合和导出文件格式不被意外改坏

## 如何重新生成

环境要求：

- Python 3.10+
- 仅使用 Python 标准库，无额外依赖

在仓库根目录执行：

```bash
python3 generate_nature_comm_palette.py --output-dir assets
```

生成后的文件会写到 `assets/` 目录下。

## 如何验证

```bash
python3 -m unittest tests.test_nature_comm_palette
python3 -m py_compile generate_nature_comm_palette.py tests/test_nature_comm_palette.py
```

## 推荐使用方式

### 1. 自己手动选色

建议优先打开：

- `assets/nature_comm_scientific_palette.svg`

先从顶部 `Recommended Scientific Pairings` 选一组整体搭配，再到下方完整色卡里微调深浅层级。

### 2. 交给 code agent 生成图

最稳的方式是同时把下面两个文件给 agent：

- `assets/nature_comm_scientific_palette.svg`
- `assets/nature_comm_scientific_palette.csv`

原因：

- `SVG` 让 agent 理解整体风格和推荐配色组合
- `CSV` 让 agent 精确拿到色值，不会“看着像”但用错颜色

### 3. 给 code agent 的推荐提示词

```text
参考以下两个文件：
- assets/nature_comm_scientific_palette.svg
- assets/nature_comm_scientific_palette.csv

请使用这套配色生成一个白底科研风格图。
优先使用推荐搭配里的 Core Results。

要求：
- 主图形元素用 Primary
- 次要对照用 Secondary
- 关键强调和显著性标记用 Accent
- 坐标轴、网格、说明块用 Neutral
- 不要使用配色库之外的颜色
- 输出可直接运行的绘图代码
```

如果你已经知道自己想要哪些颜色，最好直接指定色名和色号，例如：

```text
请只使用以下颜色：
- Harbor Blue 4  #48698A
- Steel Blue 3   #68849C
- Brick Red 4    #91564F
- Cool Gray 2    #CED2D7
```

## 使用建议

- 结果图优先选择：
  - `Core Results`
  - `Clinical Warm-Cool`
  - `Engineering Contrast`

- method 图优先选择：
  - `Method Flow`
  - `Mechanics Highlight`

- 补充图或低视觉压力场景优先选择：
  - `Calm Supplement`
  - `Uncertainty Narrative`

## 说明

- 本仓库中的配色为科研绘图实践用途整理，不代表期刊官方配色规范。
- 如果后续需要：
  - 导出为 `PNG / PDF`
  - 增加 `ASE` 调色板
  - 再拆出一套更高对比的主图版本
  - 再拆出一套更柔和的 supplementary 版本

都可以在当前脚本基础上继续扩展。
