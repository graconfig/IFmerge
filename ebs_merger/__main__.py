"""主入口模块

提供命令行参数解析和程序入口。
"""

import argparse
import sys
import os
from dotenv import load_dotenv
from ebs_merger.cli import EBSMergerCLI

# 加载.env文件
load_dotenv()


def main():
    """主入口函数，解析命令行参数并执行"""
    # 从环境变量读取默认值
    default_input_dir = os.getenv('INPUT_DIR', 'input')
    default_output_dir = os.getenv('OUTPUT_DIR', 'output')
    default_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.8'))
    
    parser = argparse.ArgumentParser(
        description='EBS設計書分析・マージツール - 一括処理版（AI使用）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python -m ebs_merger
  python -m ebs_merger --input-dir input --output-dir output
  python -m ebs_merger --threshold 0.85
  
説明:
  ツールは入力フォルダ内のすべてのExcelファイル（.xlsxおよび.xls）を自動処理します
  出力ファイルは出力フォルダに保存されます
  AIを使用して分類、IF概要生成、マージIF名生成を行います
        """
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        default=default_input_dir,
        help=f'入力フォルダパス（デフォルト：{default_input_dir}、.envで設定可能）'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default=default_output_dir,
        help=f'出力フォルダパス（デフォルト：{default_output_dir}、.envで設定可能）'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=default_threshold,
        help=f'類似度閾値、範囲0.0-1.0（デフォルト：{default_threshold}、.envで設定可能）'
    )
    
    args = parser.parse_args()
    
    # 閾値範囲の検証
    if not 0.0 < args.threshold <= 1.0:
        print("エラー：類似度閾値は0.0から1.0の間でなければなりません")
        sys.exit(1)
    
    # 创建CLI实例并运行（始终使用AI）
    cli = EBSMergerCLI(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        threshold=args.threshold
    )
    
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
