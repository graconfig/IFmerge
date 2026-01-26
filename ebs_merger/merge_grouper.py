"""合并分组模块

使用Union-Find算法识别需要合并的IF组。
"""

from typing import Dict, List, Tuple
from ebs_merger.if_grouper import IFInfo


class UnionFind:
    """Union-Find数据结构，用于管理不相交集合"""
    
    def __init__(self, elements: List[str]):
        """初始化，每个元素自成一组
        
        参数:
            elements: 元素列表
        """
        # parent[x] 表示x的父节点
        self.parent = {x: x for x in elements}
        # rank[x] 表示以x为根的树的高度（用于优化）
        self.rank = {x: 0 for x in elements}
    
    def find(self, x: str) -> str:
        """查找元素所属组的代表元素（带路径压缩）
        
        参数:
            x: 要查找的元素
            
        返回:
            该元素所属组的代表元素
        """
        if self.parent[x] != x:
            # 路径压缩：将x直接连接到根节点
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: str, y: str):
        """合并两个元素所属的组
        
        参数:
            x: 第一个元素
            y: 第二个元素
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return  # 已经在同一组
        
        # 按秩合并：将较小的树连接到较大的树
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
    
    def get_groups(self) -> Dict[str, List[str]]:
        """返回所有组，键为代表元素，值为组内元素列表
        
        返回:
            分组字典
        """
        groups = {}
        for element in self.parent.keys():
            root = self.find(element)
            if root not in groups:
                groups[root] = []
            groups[root].append(element)
        return groups


class MergeGrouper:
    """合并分组器"""
    
    def group_similar_ifs(
        self, 
        if_dict: Dict[str, IFInfo],
        similar_pairs: List[Tuple[str, str, float]]
    ) -> Dict[str, List[str]]:
        """基于相似IF对构建合并组
        
        参数:
            if_dict: IF名称到IFInfo的映射
            similar_pairs: 相似度超过阈值的IF对列表
            
        返回:
            分组结果，键为代表IF名，值为该组的IF名称列表
        """
        # 获取所有IF名称
        if_names = list(if_dict.keys())
        
        # 初始化Union-Find
        uf = UnionFind(if_names)
        
        # 合并相似的IF
        for if1_name, if2_name, _ in similar_pairs:
            uf.union(if1_name, if2_name)
        
        # 获取分组结果
        return uf.get_groups()
    
    def assign_group_ids(
        self, 
        groups: Dict[str, List[str]],
        module: str = ""
    ) -> Dict[str, str]:
        """为每个IF分配グルーピングID
        
        参数:
            groups: 分组结果
            module: 模块名（如FI、SD），用于生成模块特定的ID
            
        返回:
            IF名称到グルーピングID的映射（格式：FI001, SD001, ...）
        """
        group_assignments = {}
        group_id = 1
        
        # 为每个组分配ID（格式：[MODULE]001, [MODULE]002, ...）
        for group_members in groups.values():
            if module:
                formatted_id = f"{module}{group_id:03d}"  # 格式化为FI001, SD001等
            else:
                formatted_id = f"G{group_id:03d}"  # 默认格式G001, G002等
            
            for if_name in group_members:
                group_assignments[if_name] = formatted_id
            group_id += 1
        
        return group_assignments
