# EBS设计书分析与合并工具

该工具用于自动化分析Excel格式的EBS接口定义，识别相似的接口并提供合并建议。支持批量处理多个Excel文件。

> **言語 / Language**: [日本語版はこちら / Japanese version](README_ja.md) | [中文版](README.md)

## 🚀 快速开始

查看 [快速入门指南](QUICKSTART.md) 3步开始使用！

## 功能特性

- 读取和解析Excel格式的EBS定义书
- 基于表字段相似度计算IF之间的关联性
- 使用图算法识别需要合并的IF组
- 生成格式化的Excel分组结果报告
- **批量处理input文件夹中的所有Excel文件**
- 自动为每个输入文件生成独立的输出文件
- **🤖 AI功能（始终启用）**：使用SAP AI Core的Claude 4.5 Sonnet模型
  - 按SAP模块和业务场景自动分类IF
  - 自动生成IF概要和代表項目名
  - 智能生成合并后的IF名称
  - 优化的API调用策略（2次调用完成所有生成）

## 安装

```bash
pip install -r requirements.txt
```

### 验证配置

安装完成后，可以运行验证脚本检查配置是否正确：

```bash
python verify_config.py
```

该脚本会检查：
- ✅ .env文件是否存在
- ✅ SAP AI Core配置是否完整
- ✅ Python依赖是否安装
- ✅ 目录结构是否正确
- ✅ 模块是否可以正常导入

## 使用方法

### 基本用法（批量处理）

1. 配置SAP AI Core凭证（编辑`.env`文件）
2. 将需要处理的Excel文件放入 `input` 文件夹
3. 运行工具：

```bash
python -m ebs_merger
```

4. 查看 `output` 文件夹中的结果文件

工具会自动：
- 使用AI按SAP模块和业务场景对IF进行分类
- 为每个分类生成合并结果和模板文件
- 生成IF概要、代表項目名和合并后的IF名称

### 指定输入输出文件夹

```bash
python -m ebs_merger --input-dir "你的输入文件夹" --output-dir "你的输出文件夹"
```

### 调整相似度阈值

```bash
python -m ebs_merger --threshold 0.85
```

### 配置SAP AI Core

在`.env`文件中配置SAP AI Core凭证：

```bash
AICORE_AUTH_URL=https://your-auth-url
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://your-base-url
AICORE_RESOURCE_GROUP=default
AICORE_DEPLOYMENT_ID=your-deployment-id
```

详见 [配置指南](CONFIGURATION_GUIDE.md)

## 命令行参数

- `--input-dir`, `-i`: 输入文件夹路径（默认：`input`）
- `--output-dir`, `-o`: 输出文件夹路径（默认：`output`）
- `--threshold`, `-t`: 相似度阈值，范围0.0-1.0（默认：0.8）

**注意**：AI功能始终启用，无需额外参数。

## 文件夹结构

```
项目根目录/
├── input/              # 输入文件夹（放置待处理的Excel文件）
│   ├── 文件1.xlsx
│   ├── 文件2.xlsx
│   └── ...
├── output/             # 输出文件夹（自动生成结果文件）
│   ├── 分類報告.txt    # AI分类报告
│   ├── [SAP模块]_[业务场景1]/
│   │   ├── [分类名].xlsx
│   │   ├── グルーピング結果_[分类名].xlsx
│   │   └── G001_[AI生成的IF名].xlsm
│   ├── [SAP模块]_[业务场景2]/
│   │   └── ...
│   └── ...
├── template/           # 模板文件夹
│   └── IF_Template.xlsm
├── ebs_merger/         # 源代码
├── tests/              # 测试
├── .env                # 配置文件（需要创建）
├── .env.example        # 配置示例
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

- [QUICKSTART.md](QUICKSTART.md) - 3步快速开始
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - 配置指南
- [USAGE.md](USAGE.md) - 详细使用示例和故障排除
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 从1.x升级到2.0的迁移指南
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志

## 许可证

MIT License
