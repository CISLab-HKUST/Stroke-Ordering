# Stroke Ordering

这是一个独立的 SVG 笔画排序与动画导出项目，参考 Fu 等人的论文 *Animated Construction of Line Drawings*。程序会读取线稿 SVG，估计笔画绘制顺序和方向，并导出：

- 按笔画顺序重排 `<path>` 的 SVG
- 按排序结果逐笔绘制的 GIF
- 按排序结果逐笔绘制的 MP4

## 项目文件

```text
animated_drawer.py      核心排序流程
compute_cost.py         单笔成本、过渡成本、T-junction 检测
data_structures.py      Point/Curve/Path/Sketch 与 SVG 读取
direction.py            笔画方向估计
tsp_bnb.py              分支限界 TSP/Hamiltonian path 求解
export.py               ordered SVG/GIF/MP4 导出
stroke_order_cli.py     命令行入口
test_stroke_ordering.py 基础测试
example_triangle.svg    示例输入
example_house.svg       示例输入
requirements.txt        Python 依赖
```

## 安装

建议使用 Python 3.10+。

```bash
cd /Users/dingzhe/Downloads/stroke_ordering
python -m pip install -r requirements.txt
```

MP4 导出需要 `imageio-ffmpeg` 或系统中存在 `ffmpeg` 命令。本机已检测到 `/opt/homebrew/bin/ffmpeg`。

## 运行

处理示例 SVG：

```bash
python stroke_order_cli.py example_triangle.svg --output-dir outputs
python stroke_order_cli.py example_house.svg --output-dir outputs
```

处理自己的 SVG：

```bash
python stroke_order_cli.py path/to/input.svg --output-dir outputs
```

常用参数：

```bash
python stroke_order_cli.py input.svg \
  --output-dir outputs \
  --max-k 4 \
  --w 0.1111111 \
  --fps 12 \
  --frames-per-stroke 8
```

只导出 ordered SVG 和 GIF：

```bash
python stroke_order_cli.py input.svg --output-dir outputs --no-mp4
```

如果需要调试用编号或元数据：

```bash
python stroke_order_cli.py input.svg --output-dir outputs --show-labels --include-metadata
```

运行完成后会生成：

```text
outputs/input_ordered.svg
outputs/input.gif
outputs/input.mp4
```

## 测试

```bash
python test_stroke_ordering.py
```

当前基础测试结果：`10 passed, 0 failed`。

## SVG 支持范围

读取支持 `path`、`line`、`polyline`、`polygon`。`path` 中的直线命令会直接转换为线段；曲线和圆弧命令目前按端点近似，因此复杂贝塞尔曲线会被简化。若需要更精确的曲线动画，建议先在 SVG 编辑器中将曲线展平成 polyline/path line segments。

## 代码检查结论

原项目的主要问题已经修复：

- `__init__.py` 的 `__all__` 未闭合，包导入会语法失败。
- 测试脚本直接运行时，相对导入会失败。
- `n < max_k` 时 k-NN 图不会生成边，导致小图排序退化。
- TSP 求解固定从第 0 笔开始，不是真正搜索最优起点。
- `PriorityQueue` 在相同优先级下会尝试比较 `Node`，可能抛异常。
- `compute_thetas()` 的第二个角度错误使用了第一条笔画的切向量，并且 clamp 写错。
- 原项目没有实现 GIF/MP4/ordered SVG 的实际导出。

仍需注意：这份实现是论文思想的轻量独立版，不是完整复现。T-junction、曲率、SVG 曲线采样等部分都有简化，适合线段化 SVG 和中小规模草图。
