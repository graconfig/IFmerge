"""IF分组模块

负责按IF名称分组并提取特征。
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, Set, Tuple


@dataclass
class IFInfo:
    """IF的元数据和特征"""
    if_name: str
    doc_number: str  # 文書管理番号
    field_pairs: Set[Tuple[str, str]]  # (EBSテーブルID, 項目ID)对的集合
    item_count: int  # 項目数
    representative_item: str  # 代表項目名（第一个項目名）


class IFGrouper:
    """IF分组器"""
    
    def group_by_if(self, df: pd.DataFrame) -> Dict[str, IFInfo]:
        """按IF名称分组并提取每个IF的特征
        
        参数:
            df: 包含EBS定义的DataFrame
            
        返回:
            字典，键为IF名称，值为IFInfo对象
        """
        if_dict = {}
        
        # 按IF名分组
        grouped = df.groupby('IF名')
        
        for if_name, if_df in grouped:
            # 提取字段对
            field_pairs = self.extract_field_pairs(if_df)
            
            # 获取文書管理番号（取第一个）
            doc_number = if_df['文書管理番号'].iloc[0]
            
            # 获取代表項目名（取第一个非空的項目名）
            representative_item = ""
            for item_name in if_df['項目名']:
                if pd.notna(item_name) and str(item_name).strip():
                    representative_item = str(item_name)
                    break
            
            # 創建IFInfo对象
            if_info = IFInfo(
                if_name=str(if_name),
                doc_number=str(doc_number),
                field_pairs=field_pairs,
                item_count=len(field_pairs),
                representative_item=representative_item
            )
            
            if_dict[str(if_name)] = if_info
        
        return if_dict
    
    def extract_field_pairs(self, if_df: pd.DataFrame) -> Set[Tuple[str, str]]:
        """从IF的DataFrame中提取(EBSテーブルID, 項目ID)对
        
        参数:
            if_df: 单个IF的所有行
            
        返回:
            (EBSテーブルID, 項目ID)对的集合，过滤掉空值
        """
        field_pairs = set()
        
        for _, row in if_df.iterrows():
            table_id = row['EBSテーブルID']
            item_id = row['項目ID']
            
            # 过滤空值
            if pd.notna(table_id) and pd.notna(item_id):
                # 转换为字符串并去除空格
                table_id_str = str(table_id).strip()
                item_id_str = str(item_id).strip()
                
                # 只添加非空的字段对
                if table_id_str and item_id_str:
                    field_pairs.add((table_id_str, item_id_str))
        
        return field_pairs
