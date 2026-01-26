"""相似度计算模块

负责计算IF之间的相似度。
"""

from typing import Dict, List, Tuple
from ebs_merger.if_grouper import IFInfo


class SimilarityCalculator:
    """相似度计算器"""
    
    def calculate_similarity(self, if1: IFInfo, if2: IFInfo) -> float:
        """计算两个IF之间的相似度
        
        相似度定义为：共同字段对数量 / min(IF1字段对数量, IF2字段对数量)
        
        参数:
            if1: 第一个IF的信息
            if2: 第二个IF的信息
            
        返回:
            相似度值，范围[0.0, 1.0]
        """
        # 如果任一IF没有字段对，相似度为0
        if not if1.field_pairs or not if2.field_pairs:
            return 0.0
        
        # 计算共同字段对数量
        common_pairs = if1.field_pairs & if2.field_pairs
        common_count = len(common_pairs)
        
        # 计算相似度：共同对数量 / min(IF1对数量, IF2对数量)
        min_count = min(len(if1.field_pairs), len(if2.field_pairs))
        
        if min_count == 0:
            return 0.0
        
        similarity = common_count / min_count
        
        # 确保相似度在[0.0, 1.0]范围内
        return max(0.0, min(1.0, similarity))
    
    def build_similarity_matrix(
        self, 
        if_dict: Dict[str, IFInfo], 
        threshold: float = 0.8
    ) -> List[Tuple[str, str, float]]:
        """构建所有IF对的相似度矩阵，只返回超过阈值的对
        
        参数:
            if_dict: IF名称到IFInfo的映射
            threshold: 相似度阈值
            
        返回:
            (IF1名称, IF2名称, 相似度)的列表，仅包含相似度>=threshold的对
        """
        similar_pairs = []
        
        # 获取所有IF名称列表
        if_names = list(if_dict.keys())
        
        # 两两比较所有IF
        for i in range(len(if_names)):
            for j in range(i + 1, len(if_names)):
                if1_name = if_names[i]
                if2_name = if_names[j]
                
                if1 = if_dict[if1_name]
                if2 = if_dict[if2_name]
                
                # 计算相似度
                similarity = self.calculate_similarity(if1, if2)
                
                # 只保留超过阈值的对
                if similarity >= threshold:
                    similar_pairs.append((if1_name, if2_name, similarity))
        
        return similar_pairs
    
    def build_full_similarity_matrix(
        self, 
        if_dict: Dict[str, IFInfo]
    ) -> List[Tuple[str, str, float]]:
        """构建所有IF对的完整相似度矩阵（不考虑阈值）
        
        参数:
            if_dict: IF名称到IFInfo的映射
            
        返回:
            (IF1名称, IF2名称, 相似度)的列表，包含所有IF对
        """
        all_pairs = []
        
        # 获取所有IF名称列表
        if_names = list(if_dict.keys())
        
        # 两两比较所有IF
        for i in range(len(if_names)):
            for j in range(i + 1, len(if_names)):
                if1_name = if_names[i]
                if2_name = if_names[j]
                
                if1 = if_dict[if1_name]
                if2 = if_dict[if2_name]
                
                # 计算相似度
                similarity = self.calculate_similarity(if1, if2)
                
                # 保留所有对（包括相似度为0的）
                all_pairs.append((if1_name, if2_name, similarity))
        
        return all_pairs
