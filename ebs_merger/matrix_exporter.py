"""類似度マトリックス出力モジュール

類似度分析の結果をExcel形式のマトリックスとして出力する。
按模块输出，不同场景放在不同sheet中。
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from ebs_merger.if_grouper import IFInfo


class MatrixExporter:
    """類似度マトリックスのExcelエクスポーター"""
    
    def _calculate_directional_similarity(
        self,
        if1: IFInfo,
        if2: IFInfo,
        use_if1_as_denominator: bool = True
    ) -> float:
        """计算定向相似度（使用指定IF的字段数作为分母）
        
        パラメータ:
            if1: 第一个IF
            if2: 第二个IF
            use_if1_as_denominator: True时使用if1的字段数作为分母，False时使用if2的字段数
            
        返回:
            相似度值（0.0-1.0）
        """
        if not if1.field_pairs or not if2.field_pairs:
            return 0.0
        
        # 计算共同字段对数量
        common_pairs = if1.field_pairs & if2.field_pairs
        common_count = len(common_pairs)
        
        # 根据参数选择分母
        denominator = len(if1.field_pairs) if use_if1_as_denominator else len(if2.field_pairs)
        
        if denominator == 0:
            return 0.0
        
        similarity = common_count / denominator
        return max(0.0, min(1.0, similarity))
    
    def export_similarity_matrix(
        self,
        if_dict: Dict[str, IFInfo],
        similar_pairs: List[Tuple[str, str, float]],
        output_path: str,
        module_name: str = "",
        category_name: str = ""
    ):
        """類似度マトリックスをExcelファイルとして出力（単一シート版、包含単向和双向两个矩阵）
        
        パラメータ:
            if_dict: IF名称からIFInfoへのマッピング
            similar_pairs: (IF1名, IF2名, 類似度)のリスト
            output_path: 出力ファイルパス
            module_name: モジュール名（オプション）
            category_name: 業務内容/分類名（オプション）
        """
        # IF名のリストを取得（ソート済み）
        if_names = sorted(if_dict.keys())
        
        if not if_names:
            print("    警告：IFが見つかりません。マトリックスを生成できません。")
            return
        
        # 類似度辞書を構築（高速検索用）
        similarity_dict = {}
        for if1, if2, sim in similar_pairs:
            similarity_dict[(if1, if2)] = sim
            similarity_dict[(if2, if1)] = sim  # 双方向
        
        # マトリックスデータを構築
        matrix_data = []
        
        # ========== 第1個矩阵：単向（下三角のみ） ==========
        # ヘッダー行1: モジュール、業務内容
        header_row1 = ["モジュール", "業務内容"] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row1)
        
        # ヘッダー行2: モジュール名、分類名
        header_row2 = [module_name, category_name] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row2)
        
        # 空行
        matrix_data.append([""] * (len(if_names) + 1))
        
        # 列ヘッダー行: 文書管理番号（A列から開始）
        doc_numbers = [if_dict[if_name].doc_number for if_name in if_names]
        column_header = [""] + doc_numbers
        matrix_data.append(column_header)
        
        # データ行: 各IFの類似度（行ヘッダーも文書管理番号）- 単向
        for i, if1 in enumerate(if_names):
            row = [if_dict[if1].doc_number]  # A列に文書管理番号
            for j, if2 in enumerate(if_names):
                if i == j:
                    # 対角線は "-"
                    row.append("-")
                elif i < j:
                    # 上三角は空（NaN）
                    row.append("")
                else:
                    # 下三角は類似度値（百分比格式）
                    sim = similarity_dict.get((if1, if2), "")
                    if sim != "":
                        # 转换为百分比格式，保留1位小数
                        percentage = round(sim * 100, 1)
                        row.append(f"{percentage}%")
                    else:
                        row.append("")
            matrix_data.append(row)
        
        # ========== 空行分隔 ==========
        matrix_data.append([""] * (len(if_names) + 1))
        matrix_data.append([""] * (len(if_names) + 1))
        
        # ========== 第2個矩阵：双向（上下三角都显示） ==========
        # ヘッダー行1
        header_row1_bi = ["モジュール（双方向）", "業務内容"] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row1_bi)
        
        # ヘッダー行2
        header_row2_bi = [module_name, category_name] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row2_bi)
        
        # 空行
        matrix_data.append([""] * (len(if_names) + 1))
        
        # 列ヘッダー行
        column_header_bi = [""] + doc_numbers
        matrix_data.append(column_header_bi)
        
        # データ行 - 双向（使用定向相似度）
        for i, if1_name in enumerate(if_names):
            row = [if_dict[if1_name].doc_number]
            if1 = if_dict[if1_name]
            
            for j, if2_name in enumerate(if_names):
                if i == j:
                    row.append("-")
                else:
                    if2 = if_dict[if2_name]
                    
                    # 计算定向相似度
                    if i < j:
                        # 上三角：使用字段数较大的IF作为分母
                        if len(if1.field_pairs) >= len(if2.field_pairs):
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=True)
                        else:
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=False)
                    else:
                        # 下三角：使用字段数较小的IF作为分母
                        if len(if1.field_pairs) <= len(if2.field_pairs):
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=True)
                        else:
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=False)
                    
                    if sim > 0:
                        percentage = round(sim * 100, 1)
                        row.append(f"{percentage}%")
                    else:
                        row.append("")
            matrix_data.append(row)
        
        # DataFrameに変換
        df = pd.DataFrame(matrix_data)
        
        # Excelファイルとして保存
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='類似度マトリックス', index=False, header=False)
        
        print(f"    類似度マトリックスを保存しました：{Path(output_path).name}")
    
    def export_module_matrices(
        self,
        module_data: Dict[str, Tuple[str, Dict[str, IFInfo], List[Tuple[str, str, float]]]],
        output_path: str,
        module_name: str
    ):
        """按模块输出多sheet相似度矩阵
        
        パラメータ:
            module_data: {scenario: (category_name, if_dict, similar_pairs)}
            output_path: 输出文件路径
            module_name: 模块名（如FI、SD）
        """
        if not module_data:
            print(f"    警告：モジュール {module_name} のデータが見つかりません。")
            return
        
        # 创建Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for scenario, (category_name, if_dict, similar_pairs) in module_data.items():
                # Sheet名：モジュール_業務内容_類似度
                sheet_name = f"{module_name}_{scenario}_類似度"
                # Excel sheet名最大31字符
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                
                # 生成矩阵数据
                matrix_df = self._build_matrix_dataframe(
                    if_dict, 
                    similar_pairs, 
                    module_name, 
                    scenario
                )
                
                # 写入sheet
                matrix_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        print(f"    類似度マトリックス（モジュール別）を保存しました：{Path(output_path).name}")
    
    def _build_matrix_dataframe(
        self,
        if_dict: Dict[str, IFInfo],
        similar_pairs: List[Tuple[str, str, float]],
        module_name: str,
        scenario: str
    ) -> pd.DataFrame:
        """构建矩阵DataFrame（包含单向和双向两个矩阵）
        
        パラメータ:
            if_dict: IF信息字典
            similar_pairs: 相似度对列表（使用min作为分母）
            module_name: 模块名
            scenario: 业务场景名
            
        返回:
            矩阵DataFrame（包含两个矩阵：单向和双向）
        """
        # IF名のリストを取得（ソート済み）
        if_names = sorted(if_dict.keys())
        
        if not if_names:
            return pd.DataFrame()
        
        # 類似度辞書を構築（使用min作为分母的相似度）
        similarity_dict = {}
        for if1, if2, sim in similar_pairs:
            similarity_dict[(if1, if2)] = sim
            similarity_dict[(if2, if1)] = sim
        
        # マトリックスデータを構築
        matrix_data = []
        
        # ========== 第1個矩阵：単向（下三角のみ，使用min作为分母） ==========
        # ヘッダー行
        header_row1 = ["モジュール", "業務内容"] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row1)
        
        header_row2 = [module_name, scenario] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row2)
        
        matrix_data.append([""] * (len(if_names) + 1))
        
        # 列ヘッダー: 文書管理番号
        doc_numbers = [if_dict[if_name].doc_number for if_name in if_names]
        column_header = [""] + doc_numbers
        matrix_data.append(column_header)
        
        # データ行（単向：下三角のみ）
        for i, if1 in enumerate(if_names):
            row = [if_dict[if1].doc_number]
            for j, if2 in enumerate(if_names):
                if i == j:
                    row.append("-")
                elif i < j:
                    row.append("")
                else:
                    sim = similarity_dict.get((if1, if2), "")
                    if sim != "":
                        percentage = round(sim * 100, 1)
                        row.append(f"{percentage}%")
                    else:
                        row.append("")
            matrix_data.append(row)
        
        # ========== 空行分隔 ==========
        matrix_data.append([""] * (len(if_names) + 1))
        matrix_data.append([""] * (len(if_names) + 1))
        
        # ========== 第2個矩阵：双向（使用定向相似度） ==========
        # ヘッダー行
        header_row1_bi = ["モジュール（双方向）", "業務内容"] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row1_bi)
        
        header_row2_bi = [module_name, scenario] + [""] * (len(if_names) - 1)
        matrix_data.append(header_row2_bi)
        
        matrix_data.append([""] * (len(if_names) + 1))
        
        # 列ヘッダー: 文書管理番号
        column_header_bi = [""] + doc_numbers
        matrix_data.append(column_header_bi)
        
        # データ行（双向：使用定向相似度）
        for i, if1_name in enumerate(if_names):
            row = [if_dict[if1_name].doc_number]
            if1 = if_dict[if1_name]
            
            for j, if2_name in enumerate(if_names):
                if i == j:
                    row.append("-")
                else:
                    if2 = if_dict[if2_name]
                    
                    # 计算定向相似度
                    if i < j:
                        # 上三角：使用字段数较大的IF作为分母
                        if len(if1.field_pairs) >= len(if2.field_pairs):
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=True)
                        else:
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=False)
                    else:
                        # 下三角：使用字段数较小的IF作为分母
                        if len(if1.field_pairs) <= len(if2.field_pairs):
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=True)
                        else:
                            sim = self._calculate_directional_similarity(if1, if2, use_if1_as_denominator=False)
                    
                    if sim > 0:
                        percentage = round(sim * 100, 1)
                        row.append(f"{percentage}%")
                    else:
                        row.append("")
            matrix_data.append(row)
        
        return pd.DataFrame(matrix_data)
    

