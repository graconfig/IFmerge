"""数据加载模块

负责读取Excel文件并验证数据格式。
"""

import pandas as pd
from typing import List


class DataLoader:
    """Excel文件加载器"""
    
    # 必需的列名
    REQUIRED_COLUMNS = [
        'No.',
        '文書管理番号',
        'IF名',
        'EBSテーブル名',
        'EBSテーブルID',
        '項目ID',
        '項目名',
        '桁数'
    ]
    
    def load_excel(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件并验证必需的列
        
        参数:
            file_path: Excel文件路径
            
        返回:
            包含EBS定义数据的DataFrame
            
        异常:
            FileNotFoundError: 文件不存在
            ValueError: 缺少必需的列或文件格式错误
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
        except FileNotFoundError:
            raise FileNotFoundError(f"错误：找不到输入文件 '{file_path}'")
        except Exception as e:
            raise ValueError(f"错误：无法读取Excel文件 '{file_path}'，请确认文件格式正确。详细信息：{str(e)}")
        
        # 验证数据不为空
        if df.empty:
            raise ValueError("错误：输入文件不包含任何数据行")
        
        # 验证必需的列
        self.validate_columns(df)
        
        return df
    
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """验证DataFrame是否包含所有必需的列
        
        参数:
            df: 待验证的DataFrame
            
        返回:
            True如果所有必需列都存在
            
        异常:
            ValueError: 缺少必需的列，错误消息包含缺失列名
        """
        # 获取DataFrame的列名
        actual_columns = set(df.columns)
        required_columns = set(self.REQUIRED_COLUMNS)
        
        # 检查缺失的列
        missing_columns = required_columns - actual_columns
        
        if missing_columns:
            missing_list = ', '.join(sorted(missing_columns))
            raise ValueError(f"错误：Excel文件缺少以下必需列：{missing_list}")
        
        return True
