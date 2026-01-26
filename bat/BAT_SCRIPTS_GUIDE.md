# バッチスクリプト使用ガイド / Batch Scripts Usage Guide

## 概要 / Overview

このプロジェクトには、Windows環境でツールを簡単に使用するための3つのバッチスクリプトが含まれています。

This project includes 3 batch scripts for easy tool usage in Windows environment.

---

## スクリプト一覧 / Script List

### 1. quick_start.bat - クイックスタート
**用途 / Purpose**: 初回セットアップと実行

**機能 / Features**:
- 依存関係の自動インストール
- .envファイルの自動作成
- Excelファイル配置のガイド
- 設定の自動検証
- ツールの自動実行

**使用方法 / Usage**:
```batch
cd bat
quick_start.bat
```

**推奨 / Recommended**: 初めて使用する場合 / First-time users

---

### 2. run_merge.bat - 標準実行
**用途 / Purpose**: 通常の実行

**機能 / Features**:
- 自動的な環境チェック
- 依存関係の確認
- .envファイルの確認
- Excelファイルの確認
- ツールの実行
- 類似度マトリックスの自動生成
- 結果フォルダの自動オープン

**使用方法 / Usage**:
```batch
cd bat
run_merge.bat
```

**推奨 / Recommended**: 通常の使用 / Regular usage

**実行フロー / Execution Flow**:
```
1. Pythonのバージョン確認
   ↓
2. 依存関係の確認
   ↓
3. .envファイルの確認
   ↓
4. inputフォルダの確認
   ↓
5. Excelファイルの確認
   ↓
6. ツールの実行
   ↓
7. 結果の表示
   ↓
8. outputフォルダを開く（オプション）
```

---

### 3. verify_setup.bat - 設定検証
**用途 / Purpose**: 環境と設定の検証

**機能 / Features**:
- Pythonのバージョン確認
- 依存関係の確認
- .envファイルの確認
- フォルダ構造の確認
- Excelファイルの確認
- モジュールのインポート確認
- 詳細な検証の実行（オプション）

**使用方法 / Usage**:
```batch
cd bat
verify_setup.bat
```

**推奨 / Recommended**: トラブルシューティング時 / For troubleshooting

**検証項目 / Verification Items**:
```
[1/7] Pythonのバージョン確認
[2/7] 依存関係の確認
      - pandas
      - openpyxl
      - requests
      - python-dotenv
[3/7] .envファイルの確認
[4/7] inputフォルダの確認
[5/7] outputフォルダの確認
[6/7] templateフォルダの確認
[7/7] モジュールのインポート確認
```

---

## 使用シナリオ / Usage Scenarios

### シナリオ1: 初めて使用する場合

```batch
# ステップ1: batフォルダに移動
cd bat

# ステップ2: クイックスタートを実行
quick_start.bat

# 自動的に以下が実行されます：
# - 依存関係のインストール
# - .envファイルの作成
# - 設定の検証
# - ツールの実行
```

### シナリオ2: 通常の使用

```batch
# Excelファイルをinputフォルダに配置
# ↓
# batフォルダに移動
cd bat

# ↓
# 標準実行スクリプトを実行
run_merge.bat
```

### シナリオ3: 問題が発生した場合

```batch
# ステップ1: batフォルダに移動
cd bat

# ステップ2: 設定を検証
verify_setup.bat

# ステップ3: 問題を修正
# - 依存関係をインストール
# - .envファイルを編集
# - Excelファイルを配置

# ステップ4: 再度検証
verify_setup.bat

# ステップ5: ツールを実行
run_merge.bat
```

---

## コマンドラインオプション / Command Line Options

### Pythonコマンドで直接実行する場合

batスクリプトを使用せず、Pythonコマンドで直接実行することもできます：

```batch
# 基本的な実行
python -m ebs_merger

# カスタム入力/出力フォルダ
python -m ebs_merger --input-dir data --output-dir results

# カスタム類似度閾値
python -m ebs_merger --threshold 0.85

# すべてのオプションを指定
python -m ebs_merger -i data -o results -t 0.9

# ヘルプを表示
python -m ebs_merger --help
```

**オプション / Options**:
| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-i, --input-dir DIR` | 入力フォルダパス | input |
| `-o, --output-dir DIR` | 出力フォルダパス | output |
| `-t, --threshold NUM` | 類似度閾値 (0.0-1.0) | 0.8 |
| `-h, --help` | ヘルプを表示 | - |

---

## トラブルシューティング / Troubleshooting

### 問題1: Pythonが見つからない

**エラーメッセージ**:
```
エラー：Pythonがインストールされていません
Error: Python is not installed
```

**解決方法**:
1. Pythonをインストール: https://www.python.org/
2. インストール時に「Add Python to PATH」をチェック
3. コマンドプロンプトを再起動

### 問題2: 依存関係がインストールされていない

**エラーメッセージ**:
```
警告：依存関係がインストールされていない可能性があります
Warning: Dependencies may not be installed
```

**解決方法**:
```batch
# 手動でインストール
pip install -r requirements.txt

# または quick_start.bat を使用
cd bat
quick_start.bat
```

### 問題3: .envファイルが見つからない

**エラーメッセージ**:
```
警告：.envファイルが見つかりません
Warning: .env file not found
```

**解決方法**:
```batch
# .env.exampleからコピー
copy .env.example .env

# エディタで開いて編集
notepad .env
```

### 問題4: Excelファイルが見つからない

**エラーメッセージ**:
```
警告：inputフォルダにExcelファイルが見つかりません
Warning: No Excel files found in input folder
```

**解決方法**:
1. inputフォルダを開く
2. Excelファイル（.xlsxまたは.xls）を配置
3. スクリプトを再実行

### 問題5: AI機能でエラーが発生

**エラーメッセージ**:
```
エラー：ツールの実行に失敗しました
Error: Tool execution failed
```

**解決方法**:
1. .envファイルのSAP AI Core設定を確認
2. 認証情報が正しいか確認
3. ネットワーク接続を確認
4. verify_setup.batで詳細を確認

---

## 高度な使用方法 / Advanced Usage

### カスタムバッチスクリプトの作成

独自のバッチスクリプトを作成する例：

```batch
@echo off
chcp 65001 >nul

REM プロジェクトルートに移動
cd ..

REM カスタム設定
set INPUT_DIR=my_custom_input
set OUTPUT_DIR=my_custom_output
set THRESHOLD=0.85

REM ツールを実行
python -m ebs_merger --input-dir "%INPUT_DIR%" --output-dir "%OUTPUT_DIR%" --threshold %THRESHOLD%

REM 結果を開く
explorer "%OUTPUT_DIR%"

pause
```

### タスクスケジューラとの統合

Windowsタスクスケジューラで自動実行する場合：

1. タスクスケジューラを開く
2. 新しいタスクを作成
3. アクション: プログラムの開始
4. プログラム: `cmd.exe`
5. 引数: `/c "C:\path\to\bat\run_merge.bat"`
6. 開始: `C:\path\to\project`
7. スケジュールを設定

### ログファイルの作成

実行ログを保存する場合：

```batch
@echo off
cd ..
set LOG_FILE=logs\ebs_merger_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
if not exist logs mkdir logs
python -m ebs_merger > "%LOG_FILE%" 2>&1
```

---

## ベストプラクティス / Best Practices

### 1. 初回セットアップ
- ✅ `quick_start.bat`を使用
- ✅ .envファイルを正しく設定
- ✅ `verify_setup.bat`で検証

### 2. 通常の使用
- ✅ Excelファイルをinputフォルダに配置
- ✅ `run_merge.bat`を実行
- ✅ outputフォルダで結果を確認

### 3. トラブルシューティング
- ✅ `verify_setup.bat`で問題を特定
- ✅ エラーメッセージを確認
- ✅ ドキュメントを参照

### 4. セキュリティ
- ✅ .envファイルをバージョン管理に含めない
- ✅ 認証情報を安全に保管
- ✅ 定期的に認証情報を更新

---

## FAQ

### Q1: スクリプトが文字化けする

**A**: スクリプトの先頭に`chcp 65001`が含まれていることを確認してください。これはUTF-8エンコーディングを設定します。

### Q2: 複数のExcelファイルを一度に処理できますか？

**A**: はい、inputフォルダに複数のExcelファイルを配置すると、自動的にすべて処理されます。

### Q3: 処理結果はどこに保存されますか？

**A**: デフォルトでは`output`フォルダに保存されます。Pythonコマンドで`-o`オプションを使用して変更できます。

### Q4: エラーが発生した場合はどうすればいいですか？

**A**: 
1. `verify_setup.bat`を実行して問題を特定
2. エラーメッセージを確認
3. トラブルシューティングセクションを参照
4. それでも解決しない場合はGitHub Issuesで報告

### Q5: batフォルダから実行する必要がありますか？

**A**: はい、batスクリプトはプロジェクトルートからの相対パスを使用しているため、batフォルダ内から実行してください。スクリプトは自動的に`cd ..`でプロジェクトルートに移動します。

### Q6: カスタムパラメータを使用したい場合は？

**A**: Pythonコマンドを直接使用してください：
```batch
python -m ebs_merger -i custom_input -o custom_output -t 0.85
```

---

## まとめ / Summary

| スクリプト | 用途 | 推奨シーン |
|-----------|------|-----------|
| `quick_start.bat` | 初回セットアップ | 初めて使用する時 |
| `run_merge.bat` | 標準実行 | 通常の使用 |
| `verify_setup.bat` | 設定検証 | トラブルシューティング時 |

**重要**: すべてのスクリプトは`bat`フォルダ内から実行してください。

---

**最終更新 / Last Updated**: 2026-01-23  
**バージョン / Version**: 2.0.0
