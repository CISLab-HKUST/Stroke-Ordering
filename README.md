# Stroke Ordering

这是一个独立的 SVG 笔画排序与动画导出项目，参考 Fu 等人的论文 *Animated Construction of Line Drawings*。程序会读取线稿 SVG，估计笔画绘制顺序和方向，并导出按笔画顺序重排 `<path>` 的 SVG。

## 项目文件

```text
animated_drawer.py      核心排序流程
compute_cost.py         单笔成本、过渡成本、T-junction 检测
data_structures.py      Point/Curve/Path/Sketch 与 SVG 读取
direction.py            笔画方向估计
tsp_bnb.py              分支限界 TSP/Hamiltonian path 求解
export.py               ordered SVG 导出
stroke_order_cli.py     命令行入口
test_stroke_ordering.py 基础测试
requirements.txt        Python 依赖
```

## 安装

建议使用 Python 3.10+。

```bash
git clone https://github.com/CISLab-HKUST/Stroke-Ordering.git
cd Stroke-Ordering
python -m pip install -r requirements.txt
```

## 运行

处理示例 SVG：

```bash
python stroke_order_cli.py example_triangle.svg --output-dir outputs
```

## SVG 支持范围

读取支持 `path`、`line`、`polyline`、`polygon`。`path` 中的直线命令会直接转换为线段；曲线和圆弧命令目前按端点近似，因此复杂贝塞尔曲线会被简化。若需要更精确的曲线动画，建议先在 SVG 编辑器中将曲线展平成 polyline/path line segments。