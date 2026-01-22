# 快速入门指南

## 3步开始使用

### 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2：准备输入文件

将需要处理的Excel文件放入 `input` 文件夹：

```
input/
├── 文件1.xlsx
├── 文件2.xlsx
└── 文件3.xlsx
```

### 步骤3：运行工具

```bash
python -m ebs_merger
```

就这么简单！结果会自动保存到 `output` 文件夹。

## 输出结果

处理完成后，你会在 `output` 文件夹中看到：

```
output/
├── グルーピング結果_文件1.xlsx
├── グルーピング結果_文件2.xlsx
└── グルーピング結果_文件3.xlsx
```

每个输出文件包含：
- ✅ 每个IF的分组ID（格式：G001, G002, G003...）
- ✅ 是否需要合并（マージ要否：○需要，×不需要）
- ✅ 合并后的IF名称
- ✅ 分组依据（相似度百分比）

## 常用选项

### 调整相似度阈值

```bash
# 更严格（90%）
python -m ebs_merger --threshold 0.9

# 更宽松（70%）
python -m ebs_merger --threshold 0.7
```

### 使用自定义文件夹

```bash
python -m ebs_merger --input-dir "我的输入" --output-dir "我的输出"
```

## 需要帮助？

- 查看详细使用指南：[USAGE.md](USAGE.md)
- 查看完整文档：[README.md](README.md)
- 运行 `python -m ebs_merger --help` 查看所有选项
