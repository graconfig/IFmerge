"""结果生成模块

负责生成输出Excel文件。
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from ebs_merger.if_grouper import IFInfo
from ebs_merger.ai_generator import AIGenerator


@dataclass
class OutputRow:
    """输出Excel的一行数据"""
    no: int
    doc_number: str  # 文書管理番号
    if_name: str
    module: str  # モジュール（新增）
    scenario: str  # 業務内容（新增）
    item_count: int  # 項目数
    if_summary: str  # IF概要（可选）
    representative_item: str  # 代表項目名
    grouping_id: str  # グルーピングID（格式：FI001, SD001, ...）
    merge_required: str  # "○" (需要合并) or "×" (不需要合并)
    merged_if_name: str  # グルーピング後のIF名
    grouping_reason: str  # グルーピングの根拠


class ResultGenerator:
    """结果生成器"""
    
    def __init__(self, use_ai: bool = False):
        """初始化结果生成器
        
        参数:
            use_ai: 是否使用AI生成内容
        """
        self.use_ai = use_ai
        self.ai_generator = AIGenerator() if use_ai else None
    
    def generate_output(
        self,
        if_dict: Dict[str, IFInfo],
        group_assignments: Dict[str, str],
        similar_pairs: List[Tuple[str, str, float]],
        output_path: str,
        input_df: Optional[pd.DataFrame] = None,
        module: str = "",
        scenario: str = ""
    ) -> Dict[str, str]:
        """生成输出Excel文件
        
        参数:
            if_dict: IF信息字典
            group_assignments: IF到グルーピングIDの映射（格式：FI001, SD001, ...）
            similar_pairs: 相似IF对列表（用于生成根据）
            output_path: 输出文件路径
            input_df: 输入数据DataFrame（使用AI时需要）
            module: 模块名（如FI、SD）
            scenario: 业务场景名
            
        返回:
            AI生成的合并IF名字典 {group_id: merged_name}
        """
        # 构建分组信息：group_id -> [if_names]
        groups = {}
        for if_name, group_id in group_assignments.items():
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(if_name)
        
        # 生成输出行
        output_rows = []
        row_no = 1
        
        # 如果使用AI，批量生成所有IF的信息
        merged_if_names_cache = {}
        if self.use_ai and input_df is not None:
            print("  AIでコンテンツを生成しています...")
            try:
                # すべてのIFの概要と代表項目名を一括生成
                all_if_info = self.ai_generator.generate_all_if_info(if_dict, input_df)
                print(f"    ✓ {len(all_if_info)} 個のIF情報を一括生成しました")
            except Exception as e:
                print(f"    警告：AI一括生成に失敗しました: {e}")
                all_if_info = {}
            
            # 预先生成合并后的IF名称（按组）
            for group_id, group_members in groups.items():
                if len(group_members) > 1:
                    try:
                        merged_name = self.ai_generator.generate_merged_if_name(
                            group_members, if_dict, input_df
                        )
                        merged_if_names_cache[group_id] = merged_name
                        print(f"    ✓ マージIF名を生成しました: {group_id} -> {merged_name}")
                    except Exception as e:
                        print(f"    警告：AIマージIF名生成に失敗しました ({group_id}): {e}")
                        merged_if_names_cache[group_id] = self.create_merged_if_name(sorted(group_members))
        else:
            all_if_info = {}
        
        for if_name in sorted(if_dict.keys()):
            if_info = if_dict[if_name]
            group_id = group_assignments[if_name]
            group_members = groups[group_id]
            
            # 判断是否需要合并：○表示需要合并，×表示不需要合并
            merge_required = "○" if len(group_members) > 1 else "×"
            
            # 获取AI生成的信息
            if if_name in all_if_info:
                if_summary = all_if_info[if_name].get('summary', '')
                representative_item = all_if_info[if_name].get('representative_item', if_info.representative_item)
            else:
                if_summary = ""
                representative_item = if_info.representative_item
            
            # 生成合并后的IF名
            if group_id in merged_if_names_cache:
                merged_if_name = merged_if_names_cache[group_id]
            else:
                merged_if_name = self.create_merged_if_name(sorted(group_members))
            
            # 生成分组根据
            grouping_reason = self.create_grouping_reason(
                if_name, 
                group_members, 
                similar_pairs
            )
            
            # 创建输出行
            output_row = OutputRow(
                no=row_no,
                doc_number=if_info.doc_number,
                if_name=if_name,
                module=module,
                scenario=scenario,
                item_count=if_info.item_count,
                if_summary=if_summary,
                representative_item=representative_item,
                grouping_id=group_id,
                merge_required=merge_required,
                merged_if_name=merged_if_name,
                grouping_reason=grouping_reason
            )
            
            output_rows.append(output_row)
            row_no += 1
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {
                'No.': row.no,
                '文書管理番号': row.doc_number,
                'IF名': row.if_name,
                'モジュール': row.module,
                '業務内容': row.scenario,
                '項目数': row.item_count,
                'IF概要': row.if_summary,
                '代表項目名': row.representative_item,
                'グルーピングID': row.grouping_id,
                'マージ要否': row.merge_required,
                'グルーピング後のIF名': row.merged_if_name,
                'グルーピングの根拠': row.grouping_reason
            }
            for row in output_rows
        ])
        
        # 写入Excel文件
        try:
            df.to_excel(output_path, index=False, engine='openpyxl')
        except Exception as e:
            raise IOError(f"错误：无法写入输出文件 '{output_path}'：{str(e)}")
        
        # 返回AI生成的合并IF名
        return merged_if_names_cache
    
    def create_merged_if_name(self, if_names: List[str]) -> str:
        """为合并的IF组生成新名称
        
        参数:
            if_names: 组内的IF名称列表
            
        返回:
            合并后的IF名称（如"IF1_IF2_IF3"）
        """
        if len(if_names) == 1:
            return if_names[0]
        
        # 使用"_"连接所有IF名称
        return "_".join(if_names)
    
    def create_grouping_reason(
        self, 
        if_name: str, 
        group_members: List[str],
        similar_pairs: List[Tuple[str, str, float]]
    ) -> str:
        """グルーピング根拠の説明を生成
        
        パラメータ:
            if_name: 現在のIF名
            group_members: 同じグループのすべてのIF名
            similar_pairs: 類似IFペアのリスト
            
        戻り値:
            根拠の説明（例：「IF2と類似度85%、IF3と類似度82%」）
        """
        if len(group_members) == 1:
            return "独立IF、マージ不要"
        
        # 現在のIFに関連する類似度情報を検索
        reasons = []
        for if1, if2, similarity in similar_pairs:
            if if1 == if_name and if2 in group_members:
                reasons.append(f"「{if2}」と類似度{similarity:.1%}")
            elif if2 == if_name and if1 in group_members:
                reasons.append(f"「{if1}」と類似度{similarity:.1%}")
        
        if reasons:
            return "、".join(reasons)
        else:
            # 直接的な類似関係がない場合、推移性によるマージ
            return "推移性によるマージ"
