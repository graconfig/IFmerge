# EBS设计书分析与合并工具

该工具用于自动化分析Excel格式的EBS接口定义，识别相似的接口并提供合并建议。支持批量处理多个Excel文件。

## 🚀 快速开始

查看 [快速入门指南](QUICKSTART.md) 3步开始使用！

## 功能特性

- 读取和解析Excel格式的EBS定义书
- 基于表字段相似度计算IF之间的关联性
- 使用图算法识别需要合并的IF组
- 生成格式化的Excel分组结果报告
- **批量处理input文件夹中的所有Excel文件**
- 自动为每个输入文件生成独立的输出文件

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法（批量处理）

1. 将需要处理的Excel文件放入 `input` 文件夹
2. 运行工具：

```bash
python -m ebs_merger
```

3. 查看 `output` 文件夹中的结果文件

### 指定输入输出文件夹

```bash
python -m ebs_merger --input-dir "你的输入文件夹" --output-dir "你的输出文件夹"
```

### 调整相似度阈值

```bash
python -m ebs_merger --threshold 0.85
```

## 命令行参数

- `--input-dir`, `-i`: 输入文件夹路径（默认：`input`）
- `--output-dir`, `-o`: 输出文件夹路径（默认：`output`）
- `--threshold`, `-t`: 相似度阈值，范围0.0-1.0（默认：0.8）

## 文件夹结构

```
项目根目录/
├── input/              # 输入文件夹（放置待处理的Excel文件）
│   ├── 文件1.xlsx
│   ├── 文件2.xlsx
│   └── ...
├── output/             # 输出文件夹（自动生成结果文件）
│   ├── グルーピング結果_文件1.xlsx
│   ├── グルーピング結果_文件2.xlsx
│   └── ...
├── ebs_merger/         # 源代码
├── tests/              # 测试
├── requirements.txt    # 依赖
└── README.md          # 说明文档
```

## 输入文件格式

输入Excel文件应包含以下列：
- No.
- 文書管理番号
- IF名
- EBSテーブル名
- EBSテーブルID
- 項目ID
- 項目名
- 桁数

## 输出文件格式

输出Excel文件包含以下列：
- No.
- 文書管理番号
- IF名
- 項目数
- IF概要
- 代表項目名
- グルーピングID
- マージ要否（○：需要合并，×：不需要合并）
- グルーピング後のIF名
- グルーピングの根拠

输出文件名格式：`グルーピング結果_原文件名.xlsx`

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=ebs_merger --cov-report=html
```

## 项目结构

```
ebs_merger/
├── ebs_merger/          # 源代码
│   ├── __init__.py
│   ├── data_loader.py
│   ├── if_grouper.py
│   ├── similarity_calculator.py
│   ├── merge_grouper.py
│   ├── result_generator.py
│   ├── cli.py
│   └── __main__.py
├── input/               # 输入文件夹
├── output/              # 输出文件夹
├── tests/               # 测试
│   ├── fixtures/        # 测试数据
│   └── ...
├── requirements.txt     # 依赖
├── README.md           # 说明文档
└── USAGE.md            # 详细使用指南
```

## 详细使用指南

查看 [USAGE.md](USAGE.md) 获取更多使用示例和故障排除信息。

## 许可证

MIT License
