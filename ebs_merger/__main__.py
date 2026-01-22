"""主入口模块

提供命令行参数解析和程序入口。
"""

import argparse
import sys
from ebs_merger.cli import EBSMergerCLI


def main():
    """主入口函数，解析命令行参数并执行"""
    parser = argparse.ArgumentParser(
        description='EBS设计书分析与合并工具 - 批量处理版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m ebs_merger
  python -m ebs_merger --input-dir input --output-dir output
  python -m ebs_merger --threshold 0.85
  
说明:
  工具会自动处理输入文件夹中的所有Excel文件（.xlsx和.xls）
  输出文件会保存到输出文件夹，文件名格式为：グルーピング結果_原文件名.xlsx
        """
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        default='input',
        help='输入文件夹路径（默认：input）'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='输出文件夹路径（默认：output）'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.8,
        help='相似度阈值，范围0.0-1.0（默认：0.8）'
    )
    
    args = parser.parse_args()
    
    # 验证阈值范围
    if not 0.0 < args.threshold <= 1.0:
        print("错误：相似度阈值必须在0.0到1.0之间")
        sys.exit(1)
    
    # 创建CLI实例并运行
    cli = EBSMergerCLI(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        threshold=args.threshold
    )
    
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
