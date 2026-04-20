# Paper-Color

`Paper-Color` 现在整理为两个独立方向的配色资源目录：

- `gradient color/`
  - 放置渐变色生成相关脚本
  - 当前包含 `curve_gradient_colors.py`
- `nature color/`
  - 放置现有的 `Nature Communications` 风格科研配色库
  - 包含生成脚本、导出资产、测试与详细说明

## 仓库结构

```text
Paper-Color/
├── README.md
├── gradient color/
│   └── curve_gradient_colors.py
└── nature color/
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

## 使用说明

### 渐变色脚本

查看：

- `gradient color/curve_gradient_colors.py`

这个脚本独立抽出了中心线按位置渐变着色的逻辑，并提供了可选的 PNG 可视化输出函数。

### Nature 配色库

查看：

- `nature color/README.md`

该目录保留原有的论文配色库说明、资产导出脚本和测试。
