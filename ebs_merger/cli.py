"""命令行接口模块

协调所有组件执行完整的分析和合并流程。
"""

import os
from pathlib import Path
from ebs_merger.data_loader import DataLoader
from ebs_merger.if_grouper import IFGrouper
from ebs_merger.similarity_calculator import SimilarityCalculator
from ebs_merger.merge_grouper import MergeGrouper
from ebs_merger.result_generator import ResultGenerator
from ebs_merger.template_filler import TemplateFiller


class EBSMergerCLI:
    """EBS合并工具命令行接口"""
    
    def __init__(
        self,
        input_dir: str = "input",
        output_dir: str = "output",
        threshold: float = 0.8
    ):
        """初始化CLI配置
        
        参数:
            input_dir: 输入文件夹路径
            output_dir: 输出文件夹路径
            threshold: 相似度阈值（默认0.8）
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        
        # 初始化组件（始终使用AI）
        self.loader = DataLoader()
        self.grouper = IFGrouper()
        self.calculator = SimilarityCalculator()
        self.merge_grouper = MergeGrouper()
        self.result_generator = ResultGenerator(use_ai=True)
        self.template_filler = TemplateFiller()
        
        # 初始化AI分类器
        from ebs_merger.ai_classifier import AIClassifier
        self.classifier = AIClassifier()
    
    def run(self):
        """执行完整的分析和合并流程"""
        try:
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 起動情報の表示
            print("=" * 60)
            print("EBS設計書の一括分析を開始します（AI使用）...")
            print("=" * 60)
            print(f"入力フォルダ：{self.input_dir}")
            print(f"出力フォルダ：{self.output_dir}")
            print(f"類似度閾値：{self.threshold * 100:.0f}%")
            print()
            
            # 查找所有Excel文件
            excel_files = self.find_excel_files()
            
            if not excel_files:
                print(f"エラー：'{self.input_dir}' フォルダにExcelファイルが見つかりません")
                print("Excelファイルをinputフォルダに配置してから再試行してください")
                return 1
            
            print(f"{len(excel_files)} 個のExcelファイルを発見しました")
            print()
            
            # 处理每个文件
            success_count = 0
            fail_count = 0
            
            for idx, input_file in enumerate(excel_files, 1):
                print(f"[{idx}/{len(excel_files)}] ファイル処理中: {input_file.name}")
                print("-" * 60)
                
                try:
                    self.process_single_file(input_file)
                    success_count += 1
                    print("✓ 処理成功")
                except Exception as e:
                    fail_count += 1
                    print(f"✗ 処理失敗: {e}")
                
                print()
            
            # 打印总体摘要
            self.print_batch_summary(success_count, fail_count, len(excel_files))
            
            return 0 if fail_count == 0 else 1
            
        except Exception as e:
            print(f"\nエラー：処理中に予期しないエラーが発生しました：{str(e)}")
            return 1
    
    def find_excel_files(self):
        """查找输入文件夹中的所有Excel文件
        
        返回:
            Excel文件路径列表
        """
        if not self.input_dir.exists():
            return []
        
        excel_files = []
        # 支持.xlsx和.xls格式
        for pattern in ['*.xlsx', '*.xls']:
            excel_files.extend(self.input_dir.glob(pattern))
        
        # 排除临时文件（以~$开头）
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        return sorted(excel_files)
    
    def process_single_file(self, input_file: Path):
        """处理单个Excel文件
        
        参数:
            input_file: 输入文件路径
        """
        # 1. Excelファイルの読み込み
        print(f"  Excelファイルを読み込んでいます...")
        df = self.loader.load_excel(str(input_file))
        print(f"  {len(df)} 行のデータを正常に読み込みました")
        
        # 2. IFのグループ化
        print(f"  IFをグループ化しています...")
        if_dict = self.grouper.group_by_if(df)
        print(f"  {len(if_dict)} 個のIFを発見しました")
        
        # 3. AIによる分類
        print(f"  AIで分類しています...")
        categories = self.classifier.classify_interfaces(if_dict, df)
        print(f"  ✓ 分類完了：{len(categories)}個の分類")
        
        # 分類後のデータを保存（outputの直下に分類フォルダを作成）
        print(f"  分類データを保存しています...")
        file_paths = self.classifier.save_classified_data(df, categories, str(self.output_dir))
        
        # 分類レポートの生成（outputルートディレクトリに配置）
        self.classifier.generate_classification_report(
            categories,
            str(self.output_dir / "分類レポート.txt")
        )
        
        # 各分類ごとにマージ処理を実行
        print(f"  各分類のマージ処理を実行しています...")
        for category_name, category_file in file_paths.items():
            print(f"\n  分類を処理中：{category_name}")
            self.process_classified_file(category_file, category_name)
    
    def process_classified_file(self, classified_file: Path, category_name: str):
        """处理分类后的单个文件
        
        参数:
            classified_file: 分类文件路径
            category_name: 分类名称
        """
        # 获取分类文件夹路径（已经是output/[分类名]/xxx.xlsx）
        category_dir = classified_file.parent
        safe_name = category_name.replace('/', '_').replace('\\', '_')
        
        # 生成输出文件名（放在同一个分类文件夹下）
        output_filename = f"グルーピング結果_{safe_name}.xlsx"
        output_path = category_dir / output_filename
        
        # 1. 分類ファイルの読み込み
        df = self.loader.load_excel(str(classified_file))
        print(f"    {len(df)} 行のデータを読み込みました")
        
        # 2. IFのグループ化
        if_dict = self.grouper.group_by_if(df)
        print(f"    {len(if_dict)} 個のIFを発見しました")
        
        # 3. 類似度の計算
        similar_pairs = self.calculator.build_similarity_matrix(
            if_dict, 
            self.threshold
        )
        print(f"    {len(similar_pairs)} 組の類似IFを発見しました")
        
        # 4. グループの生成
        groups = self.merge_grouper.group_similar_ifs(if_dict, similar_pairs)
        group_assignments = self.merge_grouper.assign_group_ids(groups)
        print(f"    {len(groups)} 個のグループを生成しました")
        
        # 5. 出力ファイルへの書き込み（分類フォルダ内に配置）
        merged_if_names = self.result_generator.generate_output(
            if_dict,
            group_assignments,
            similar_pairs,
            str(output_path),
            input_df=df
        )
        print(f"    出力ファイルを保存しました：{output_filename}")
        
        # 6. 生成合并组的模板文件（放在分类文件夹下）
        self.template_filler.fill_merged_groups(
            if_dict,
            group_assignments,
            similar_pairs,
            df,
            str(category_dir),  # 直接使用分类文件夹
            merged_if_names  # 传递AI生成的合并IF名
        )
        
        # 7. サマリーの表示
        independent_count = sum(1 for group in groups.values() if len(group) == 1)
        total_merge_ifs = sum(len(group) for group in groups.values() if len(group) > 1)
        print(f"    総IF数：{len(if_dict)} | マージ必要：{total_merge_ifs} | 独立：{independent_count} | グループ数：{len(groups)}")
    
    def print_batch_summary(self, success_count, fail_count, total_count):
        """一括処理のサマリーを表示
        
        パラメータ:
            success_count: 成功したファイル数
            fail_count: 失敗したファイル数
            total_count: 総ファイル数
        """
        print("=" * 60)
        print("一括処理が完了しました！")
        print("=" * 60)
        print(f"総ファイル数：{total_count}")
        print(f"成功：{success_count}")
        print(f"失敗：{fail_count}")
        print(f"出力フォルダ：{self.output_dir}")
        print("=" * 60)
