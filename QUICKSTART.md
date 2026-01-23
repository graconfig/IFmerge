# 快速入门指南

## 3步开始使用

### 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2：配置SAP AI Core

复制配置示例文件并填入你的凭证：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入SAP AI Core凭证：

```bash
# SAP AI Core配置
AICORE_AUTH_URL=https://your-auth-url
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://your-base-url
AICORE_RESOURCE_GROUP=default
AICORE_DEPLOYMENT_ID=your-deployment-id

# 工具配置
INPUT_DIR=input
OUTPUT_DIR=output
SIMILARITY_THRESHOLD=0.8
```

### 步骤3：准备输入文件并运行

将需要处理的Excel文件放入 `input` 文件夹：

```
input/
├── 文件1.xlsx
├── 文件2.xlsx
└── 文件3.xlsx
```

运行工具：

```bash
python -m ebs_merger
```

就这么简单！结果会自动保存到 `output` 文件夹。

## 输出结果

处理完成后，你会在 `output` 文件夹中看到：

```
output/
├── 分類報告.txt                    # AI分类总报告
├── WM_出货管理/
│   ├── WM_出货管理.xlsx            # 原始分类数据
│   ├── グルーピング結果_WM_出货管理.xlsx  # 合并结果
│   └── G001_出货数据接口.xlsm      # 模板文件（AI生成的名称）
├── SD_订单处理/
│   ├── SD_订单处理.xlsx
│   ├── グルーピング結果_SD_订单处理.xlsx
│   └── G002_订单管理接口.xlsm
└── ...
```

每个输出文件包含：
- ✅ AI生成的IF分类（按SAP模块和业务场景）
- ✅ AI生成的IF概要和代表項目名
- ✅ 每个IF的分组ID（格式：G001, G002, G003...）
- ✅ 是否需要合并（マージ要否：○需要，×不需要）
- ✅ AI生成的合并后IF名称（简洁有意义）
- ✅ 分组依据（相似度百分比）
- ✅ 填充好的Excel模板文件

## AI功能说明

本工具始终使用AI功能，包括：

1. **IF分类**：按SAP模块和业务场景自动分类
2. **IF概要生成**：为每个IF生成功能说明
3. **代表項目名选择**：智能选择最能代表核心功能的项目
4. **合并IF名生成**：为合并的IF组生成简洁有意义的名称

**优化的API调用**：
- 批量生成所有IF信息（1次API调用）
- 生成合并IF名称（1次API调用）
- 总共仅需2次API调用，处理速度快，成本低

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

### 组合使用

```bash
python -m ebs_merger -i data -o results -t 0.85
```

## 需要帮助？

- 查看配置指南：[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- 查看详细使用指南：[USAGE.md](USAGE.md)
- 查看完整文档：[README.md](README.md)
- 运行 `python -m ebs_merger --help` 查看所有选项

## 故障排查

### 问题：找不到.env文件

**解决**：确保在项目根目录创建了`.env`文件，可以从`.env.example`复制

```bash
cp .env.example .env
```

### 问题：AI功能报错

**解决**：检查`.env`文件中的SAP AI Core配置是否正确，确保所有必需字段都已填写

### 问题：找不到Excel文件

**解决**：确保Excel文件在`input`文件夹中，且格式为`.xlsx`或`.xls`
