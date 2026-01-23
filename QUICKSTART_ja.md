# クイックスタートガイド

## 3ステップで使い始める

### ステップ1：依存関係のインストール

```bash
pip install -r requirements.txt
```

### ステップ2：SAP AI Coreの設定

設定例ファイルをコピーして認証情報を入力：

```bash
cp .env.example .env
```

`.env`ファイルを編集し、SAP AI Core認証情報を入力：

```bash
# SAP AI Core設定
AICORE_AUTH_URL=https://your-auth-url
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://your-base-url
AICORE_RESOURCE_GROUP=default
AICORE_DEPLOYMENT_ID=your-deployment-id

# ツール設定
INPUT_DIR=input
OUTPUT_DIR=output
SIMILARITY_THRESHOLD=0.8
```

### ステップ3：入力ファイルの準備と実行

処理するExcelファイルを`input`フォルダに配置：

```
input/
├── ファイル1.xlsx
├── ファイル2.xlsx
└── ファイル3.xlsx
```

ツールを実行：

```bash
python -m ebs_merger
```

これだけです！結果は自動的に`output`フォルダに保存されます。

## 出力結果

処理完了後、`output`フォルダに以下が表示されます：

```
output/
├── 分類レポート.txt                    # AI分類総合レポート
├── WM_出荷管理/
│   ├── WM_出荷管理.xlsx            # 元の分類データ
│   ├── グルーピング結果_WM_出荷管理.xlsx  # マージ結果
│   └── G001_出荷データインターフェース.xlsm      # テンプレートファイル（AI生成の名前）
├── SD_受注処理/
│   ├── SD_受注処理.xlsx
│   ├── グルーピング結果_SD_受注処理.xlsx
│   └── G002_受注管理インターフェース.xlsm
└── ...
```

各出力ファイルには以下が含まれます：
- ✅ AI生成のIF分類（SAPモジュールと業務シナリオ別）
- ✅ AI生成のIF概要と代表項目名
- ✅ 各IFのグループID（形式：G001, G002, G003...）
- ✅ マージの要否（マージ要否：○必要、×不要）
- ✅ AI生成のマージ後IF名（簡潔で意味のある名前）
- ✅ グルーピングの根拠（類似度パーセンテージ）
- ✅ 入力済みのExcelテンプレートファイル

## AI機能の説明

このツールは常にAI機能を使用します：

1. **IF分類**：SAPモジュールと業務シナリオに基づく自動分類
2. **IF概要生成**：各IFの機能説明を生成
3. **代表項目名選択**：中核機能を最もよく表す項目をインテリジェントに選択
4. **マージIF名生成**：マージするIFグループに対して簡潔で意味のある名前を生成

**最適化されたAPI呼び出し**：
- すべてのIF情報を一括生成（1回のAPI呼び出し）
- マージIF名を生成（1回のAPI呼び出し）
- 合計わずか2回のAPI呼び出しで、処理が高速かつ低コスト

## よく使うオプション

### 類似度閾値の調整

```bash
# より厳格（90%）
python -m ebs_merger --threshold 0.9

# より緩和（70%）
python -m ebs_merger --threshold 0.7
```

### カスタムフォルダの使用

```bash
python -m ebs_merger --input-dir "マイ入力" --output-dir "マイ出力"
```

### 組み合わせ使用

```bash
python -m ebs_merger -i data -o results -t 0.85
```

## ヘルプが必要ですか？

- 設定ガイドを参照：[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- 詳細使用ガイドを参照：[USAGE.md](USAGE.md)
- 完全なドキュメントを参照：[README_ja.md](README_ja.md)
- `python -m ebs_merger --help`を実行してすべてのオプションを表示

## トラブルシューティング

### 問題：.envファイルが見つからない

**解決方法**：プロジェクトルートディレクトリに`.env`ファイルを作成してください。`.env.example`からコピーできます

```bash
cp .env.example .env
```

### 問題：AI機能でエラーが発生する

**解決方法**：`.env`ファイルのSAP AI Core設定が正しいか確認し、すべての必須フィールドが入力されているか確認してください

### 問題：Excelファイルが見つからない

**解決方法**：Excelファイルが`input`フォルダにあり、形式が`.xlsx`または`.xls`であることを確認してください

