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
from ebs_merger.matrix_exporter import MatrixExporter


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
        self.matrix_exporter = MatrixExporter()
        
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
        
        # 分類レポートの生成（outputルートディレクトリに配置）
        self.classifier.generate_classification_report(
            categories,
            str(self.output_dir / "分類レポート.txt")
        )
        
        # 按模块组织数据
        print(f"  モジュール別にデータを整理しています...")
        module_data = self._organize_by_module(categories, if_dict, df)
        
        # 收集所有行用于统一的グルーピング結果文件
        all_output_rows = []
        
        # 各模块ごとに処理
        print(f"  各モジュールのマージ処理を実行しています...")
        for module_name, scenarios in module_data.items():
            print(f"\n  モジュールを処理中：{module_name}")
            module_rows = self.process_module(module_name, scenarios, df)
            all_output_rows.extend(module_rows)
        
        # 输出统一的グルーピング結果文件（不分模块）
        output_filename = "グルーピング結果.xlsx"
        output_path = self.output_dir / output_filename
        self._write_unified_output(all_output_rows, output_path)
        print(f"\n  ✓ グルーピング結果ファイルを保存しました：{output_filename}")
    
    def _organize_by_module(self, categories, if_dict, df):
        """按模块组织分类数据
        
        返回:
            {module: {scenario: (category_name, if_dict, df)}}
        """
        from collections import defaultdict
        module_data = defaultdict(dict)
        
        for category_name, (module, scenario, if_names) in categories.items():
            # 筛选该分类的IF
            category_if_dict = {name: if_dict[name] for name in if_names if name in if_dict}
            category_df = df[df['IF名'].isin(if_names)]
            
            module_data[module][scenario] = (category_name, category_if_dict, category_df)
        
        return module_data
    
    def process_module(self, module_name: str, scenarios: dict, full_df):
        """处理单个模块的所有场景
        
        参数:
            module_name: 模块名（如FI、SD）
            scenarios: {scenario: (category_name, if_dict, df)}
            full_df: 完整的数据DataFrame
            
        返回:
            所有场景的输出行列表
        """
        # 创建模块文件夹
        module_dir = self.output_dir / module_name
        module_dir.mkdir(parents=True, exist_ok=True)
        
        # 收集所有场景的数据
        all_module_rows = []
        module_matrix_data = {}
        
        for scenario, (category_name, if_dict, df) in scenarios.items():
            print(f"    場景を処理中：{scenario}")
            print(f"      {len(if_dict)} 個のIF, {len(df)} 行のデータ")
            
            # 計算相似度（用于分组，只包含超过阈值的）
            similar_pairs = self.calculator.build_similarity_matrix(if_dict, self.threshold)
            print(f"      {len(similar_pairs)} 組の類似IFを発見しました")
            
            # 計算完整相似度（用于矩阵输出，包含所有IF对）
            all_similarity_pairs = self.calculator.build_full_similarity_matrix(if_dict)
            
            # 生成分組
            groups = self.merge_grouper.group_similar_ifs(if_dict, similar_pairs)
            group_assignments = self.merge_grouper.assign_group_ids(groups, module=module_name)
            print(f"      {len(groups)} 個のグループを生成しました")
            
            # 生成输出行
            rows = self._generate_output_rows(
                if_dict, group_assignments, similar_pairs, df,
                module_name, scenario
            )
            all_module_rows.extend(rows)
            
            # 保存矩阵数据（使用完整相似度数据）
            module_matrix_data[scenario] = (category_name, if_dict, all_similarity_pairs)
            
            # 生成模板文件（直接放到模块文件夹，不创建业务场景子文件夹）
            merged_if_names = self._get_merged_if_names(
                if_dict, group_assignments, groups, similar_pairs, df
            )
            
            self.template_filler.fill_merged_groups(
                if_dict, group_assignments, similar_pairs, df,
                str(module_dir), merged_if_names
            )
        
        # 输出相似度矩阵（模块级别，多sheet）
        matrix_filename = f"類似度マトリックス_{module_name}.xlsx"
        matrix_path = module_dir / matrix_filename
        self.matrix_exporter.export_module_matrices(
            module_matrix_data, str(matrix_path), module_name
        )
        
        # 返回所有行用于统一输出
        return all_module_rows
    
    def _generate_output_rows(self, if_dict, group_assignments, similar_pairs, df,
                              module_name, scenario):
        """生成输出行数据"""
        from ebs_merger.result_generator import OutputRow
        
        # 构建分组信息
        groups = {}
        for if_name, group_id in group_assignments.items():
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(if_name)
        
        # 生成AI内容
        merged_if_names_cache = {}
        all_if_info = {}
        
        if self.result_generator.use_ai:
            try:
                all_if_info = self.result_generator.ai_generator.generate_all_if_info(if_dict, df)
            except:
                pass
            
            for group_id, group_members in groups.items():
                if len(group_members) > 1:
                    try:
                        merged_name = self.result_generator.ai_generator.generate_merged_if_name(
                            group_members, if_dict, df
                        )
                        merged_if_names_cache[group_id] = merged_name
                    except:
                        merged_if_names_cache[group_id] = self.result_generator.create_merged_if_name(sorted(group_members))
        
        # 生成输出行
        output_rows = []
        for if_name in sorted(if_dict.keys()):
            if_info = if_dict[if_name]
            group_id = group_assignments[if_name]
            group_members = groups[group_id]
            
            merge_required = "○" if len(group_members) > 1 else "×"
            
            if if_name in all_if_info:
                if_summary = all_if_info[if_name].get('summary', '')
                representative_item = all_if_info[if_name].get('representative_item', if_info.representative_item)
            else:
                if_summary = ""
                representative_item = if_info.representative_item
            
            if group_id in merged_if_names_cache:
                merged_if_name = merged_if_names_cache[group_id]
            else:
                merged_if_name = self.result_generator.create_merged_if_name(sorted(group_members))
            
            grouping_reason = self.result_generator.create_grouping_reason(
                if_name, group_members, similar_pairs
            )
            
            output_rows.append({
                '文書管理番号': if_info.doc_number,
                'IF名': if_name,
                'モジュール': module_name,
                '業務内容': scenario,
                '項目数': if_info.item_count,
                'IF概要': if_summary,
                '代表項目名': representative_item,
                'グルーピングID': group_id,
                'マージ要否': merge_required,
                'グルーピング後のIF名': merged_if_name,
                'グルーピングの根拠': grouping_reason
            })
        
        return output_rows
    
    def _get_merged_if_names(self, if_dict, group_assignments, groups, similar_pairs, df):
        """获取合并IF名称"""
        merged_if_names = {}
        
        # 构建分组信息：group_id -> [if_names]
        groups_dict = {}
        for if_name, group_id in group_assignments.items():
            if group_id not in groups_dict:
                groups_dict[group_id] = []
            groups_dict[group_id].append(if_name)
        
        for group_id, group_members in groups_dict.items():
            if len(group_members) > 1:
                try:
                    merged_name = self.result_generator.ai_generator.generate_merged_if_name(
                        group_members, if_dict, df
                    )
                    merged_if_names[group_id] = merged_name
                except:
                    merged_if_names[group_id] = self.result_generator.create_merged_if_name(sorted(group_members))
        
        return merged_if_names
    
    def _write_unified_output(self, rows, output_path):
        """写入统一的グルーピング結果文件"""
        import pandas as pd
        
        # 添加No.列
        for idx, row in enumerate(rows, 1):
            row['No.'] = idx
        
        # 重新排列列顺序
        df = pd.DataFrame(rows)
        column_order = ['No.', '文書管理番号', 'IF名', 'モジュール', '業務内容', 
                       '項目数', 'IF概要', '代表項目名', 'グルーピングID', 
                       'マージ要否', 'グルーピング後のIF名', 'グルーピングの根拠']
        df = df[column_order]
        
        df.to_excel(output_path, index=False, engine='openpyxl')
    
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
