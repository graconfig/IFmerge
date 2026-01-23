# EBS設計書分析・マージツール

このツールは、Excel形式のEBSインターフェース定義を自動分析し、類似したインターフェースを識別してマージ提案を提供します。複数のExcelファイルの一括処理に対応しています。

> **言語 / Language**: [日本語版](README_ja.md) | [中文版はこちら / Chinese version](README.md)

## 🚀 クイックスタート

[クイックスタートガイド](QUICKSTART_ja.md)を参照して、3ステップで使い始めましょう！

## 機能

- Excel形式のEBS定義書の読み込みと解析
- テーブルフィールドの類似度に基づくIF間の関連性計算
- グラフアルゴリズムを使用したマージ対象IFグループの識別
- フォーマットされたExcelグループ化結果レポートの生成
- **inputフォルダ内のすべてのExcelファイルの一括処理**
- 各入力ファイルに対する個別の出力ファイルの自動生成
- **🤖 AI機能（常時有効）**：SAP AI CoreのClaude 4.5 Sonnetモデルを使用
  - SAPモジュールと業務シナリオに基づくIFの自動分類
  - IF概要と代表項目名の自動生成
  - マージ後のIF名のインテリジェント生成
  - 最適化されたAPI呼び出し戦略（2回の呼び出しですべての生成を完了）

## インストール

```bash
pip install -r requirements.txt
```

### 設定の検証

インストール完了後、検証スクリプトを実行して設定が正しいか確認できます：

```bash
python verify_config.py
```

このスクリプトは以下をチェックします：
- ✅ .envファイルが存在するか
- ✅ SAP AI Core設定が完全か
- ✅ Python依存関係がインストールされているか
- ✅ ディレクトリ構造が正しいか
- ✅ モジュールが正常にインポートできるか

## 使用方法

### Windows用バッチスクリプト（推奨）

Windowsユーザーは、便利なバッチスクリプトを使用できます：

#### クイックスタート（初回使用）
```batch
cd bat
quick_start.bat
```
自動的に依存関係のインストール、設定、実行を行います。

#### 通常の実行
```batch
cd bat
run_merge.bat
```
デフォルト設定でツールを実行します。

#### 設定の検証
```batch
cd bat
verify_setup.bat
```

詳細は[バッチスクリプトガイド](bat/BAT_SCRIPTS_GUIDE.md)を参照してください。

### 基本的な使い方（一括処理）

1. SAP AI Core認証情報を設定（`.env`ファイルを編集）
2. 処理するExcelファイルを`input`フォルダに配置
3. ツールを実行：

```bash
python -m ebs_merger
```

4. `output`フォルダ内の結果ファイルを確認

ツールは自動的に：
- AIを使用してSAPモジュールと業務シナリオに基づいてIFを分類
- 各分類のマージ結果とテンプレートファイルを生成
- IF概要、代表項目名、マージ後のIF名を生成

### 入力/出力フォルダの指定

```bash
python -m ebs_merger --input-dir "入力フォルダ" --output-dir "出力フォルダ"
```

### 類似度閾値の調整

```bash
python -m ebs_merger --threshold 0.85
```

### SAP AI Coreの設定

`.env`ファイルでSAP AI Core認証情報を設定：

```bash
AICORE_AUTH_URL=https://your-auth-url
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://your-base-url
AICORE_RESOURCE_GROUP=default
AICORE_DEPLOYMENT_ID=your-deployment-id
```

詳細は[設定ガイド](CONFIGURATION_GUIDE.md)を参照してください

## コマンドライン引数

- `--input-dir`, `-i`: 入力フォルダパス（デフォルト：`input`）
- `--output-dir`, `-o`: 出力フォルダパス（デフォルト：`output`）
- `--threshold`, `-t`: 類似度閾値、範囲0.0-1.0（デフォルト：0.8）

**注意**：AI機能は常時有効で、追加のパラメータは不要です。

## フォルダ構造

```
プロジェクトルート/
├── input/              # 入力フォルダ（処理するExcelファイルを配置）
│   ├── ファイル1.xlsx
│   ├── ファイル2.xlsx
│   └── ...
├── output/             # 出力フォルダ（結果ファイルが自動生成される）
│   ├── 分類レポート.txt    # AI分類レポート
│   ├── [SAPモジュール]_[業務シナリオ1]/
│   │   ├── [分類名].xlsx
│   │   ├── グルーピング結果_[分類名].xlsx
│   │   └── G001_[AI生成のIF名].xlsm
│   ├── [SAPモジュール]_[業務シナリオ2]/
│   │   └── ...
│   └── ...
├── template/           # テンプレートフォルダ
│   └── IF_Template.xlsm
├── ebs_merger/         # ソースコード
├── tests/              # テスト
├── .env                # 設定ファイル（作成が必要）
├── .env.example        # 設定例
├── requirements.txt    # 依存関係
└── README.md          # 説明ドキュメント
```

## 入力ファイル形式

入力Excelファイルには以下の列が必要です：
- No.
- 文書管理番号
- IF名
- EBSテーブル名
- EBSテーブルID
- 項目ID
- 項目名
- 桁数

## 出力ファイル形式

出力Excelファイルには以下の列が含まれます：
- No.
- 文書管理番号
- IF名
- 項目数
- IF概要
- 代表項目名
- グルーピングID
- マージ要否（○：マージ必要、×：マージ不要）
- グルーピング後のIF名
- グルーピングの根拠

出力ファイル名形式：`グルーピング結果_元のファイル名.xlsx`

## テストの実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジレポートを生成
pytest tests/ --cov=ebs_merger --cov-report=html
```

## プロジェクト構造

```
ebs_merger/
├── ebs_merger/          # ソースコード
│   ├── __init__.py
│   ├── data_loader.py
│   ├── if_grouper.py
│   ├── similarity_calculator.py
│   ├── merge_grouper.py
│   ├── result_generator.py
│   ├── cli.py
│   └── __main__.py
├── input/               # 入力フォルダ
├── output/              # 出力フォルダ
├── tests/               # テスト
│   ├── fixtures/        # テストデータ
│   └── ...
├── requirements.txt     # 依存関係
├── README.md           # 説明ドキュメント
└── USAGE.md            # 詳細使用ガイド
```

## 詳細使用ガイド

- [QUICKSTART_ja.md](QUICKSTART_ja.md) - 3ステップクイックスタート
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - 設定ガイド
- [USAGE.md](USAGE.md) - 詳細な使用例とトラブルシューティング
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 1.xから2.0への移行ガイド
- [CHANGELOG.md](CHANGELOG.md) - バージョン更新履歴

## ライセンス

MIT License

