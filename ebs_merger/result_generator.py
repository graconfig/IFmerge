"""结果生成模块

负责生成输出Excel文件。
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple
from ebs_merger.if_grouper import IFInfo


@dataclass
class OutputRow:
    """输出Excel的一行数据"""
    no: int
    doc_number: str  # 文書管理番号
    if_name: str
    item_count: int  # 項目数
    if_summary: str  # IF概要（可选）
    representative_item: str  # 代表項目名
    grouping_id: str  # グルーピングID（格式：G001, G002, ...）
    merge_required: str  # "○" (需要合并) or "×" (不需要合并)
    merged_if_name: str  # グルーピング後のIF名
    grouping_reason: str  # グルーピングの根拠


class ResultGenerator:
    """结果生成器"""
    
    def generate_output(
        self,
        if_dict: Dict[str, IFInfo],
        group_assignments: Dict[str, str],
        similar_pairs: List[Tuple[str, str, float]],
        output_path: str
    ):
        """生成输出Excel文件
        
        参数:
            if_dict: IF信息字典
            group_assignments: IF到グルーピングIDの映射（格式：G001, G002, ...）
            similar_pairs: 相似IF对列表（用于生成根据）
            output_path: 输出文件路径
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
        
        for if_name in sorted(if_dict.keys()):
            if_info = if_dict[if_name]
            group_id = group_assignments[if_name]
            group_members = groups[group_id]
            
            # 判断是否需要合并：○表示需要合并，×表示不需要合并
            merge_required = "○" if len(group_members) > 1 else "×"
            
            # 生成合并后的IF名
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
                item_count=if_info.item_count,
                if_summary="",  # IF概要留空
                representative_item=if_info.representative_item,
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
        """生成分组根据说明
        
        参数:
            if_name: 当前IF名称
            group_members: 同组的所有IF名称
            similar_pairs: 相似IF对列表
            
        返回:
            根据说明（如"与IF2相似度85%，与IF3相似度82%"）
        """
        if len(group_members) == 1:
            return "独立IF，无需合并"
        
        # 查找与当前IF相关的相似度信息
        reasons = []
        for if1, if2, similarity in similar_pairs:
            if if1 == if_name and if2 in group_members:
                reasons.append(f"与「{if2}」相似度{similarity:.1%}")
            elif if2 == if_name and if1 in group_members:
                reasons.append(f"与「{if1}」相似度{similarity:.1%}")
        
        if reasons:
            return "、".join(reasons)
        else:
            # 如果没有直接相似关系，说明是通过传递性合并的
            return "通过传递性合并"
