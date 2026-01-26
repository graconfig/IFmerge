"""AI分类模块

使用AI按照SAP模块和业务场景对IF进行分组。
"""

import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
from ebs_merger.ai_generator import AIGenerator
from ebs_merger.if_grouper import IFInfo


class AIClassifier:
    """AI分类器 - 按SAP模块和业务场景分组IF"""
    
    def __init__(self, ai_generator: AIGenerator = None):
        """初始化分类器
        
        参数:
            ai_generator: AI生成器实例（可选）
        """
        self.ai_generator = ai_generator or AIGenerator()
    
    def classify_interfaces(
        self,
        if_dict: Dict[str, IFInfo],
        input_df: pd.DataFrame
    ) -> Dict[str, Tuple[str, str, List[str]]]:
        """使用AI对IF进行分类
        
        参数:
            if_dict: IF信息字典
            input_df: 输入数据DataFrame
            
        返回:
            分类结果字典: {category_name: (module, scenario, [if_names])}
            其中module是SAP模块（如FI、SD），scenario是业务场景
        """
        # 准备所有IF的信息
        if_info_list = []
        for if_name, if_info in if_dict.items():
            if_data = input_df[input_df['IF名'] == if_name]
            tables = if_data['EBSテーブル名'].unique().tolist()
            items = if_data['項目名'].tolist()
            
            if_info_list.append({
                'if_name': if_name,
                'doc_number': if_info.doc_number,
                'tables': tables[:5],  # 最多5个表
                'items': items[:10],  # 最多10个项目
                'item_count': if_info.item_count
            })
        
        # プロンプトの構築
        prompt = f"""以下の{len(if_info_list)}個の日本語インターフェース（IF）を分析し、SAPモジュールと業務シナリオに基づいてグループ化してください。

インターフェース情報：
"""
        for idx, info in enumerate(if_info_list, 1):
            prompt += f"""
{idx}. IF名: {info['if_name']}
   文書管理番号: {info['doc_number']}
   関連テーブル: {', '.join(info['tables'])}
   項目総数: {info['item_count']}
   サンプル項目: {', '.join(info['items'][:5])}
"""
        
        prompt += """
以下の観点でインターフェースをグループ化してください：
1. SAPモジュール（例：SD販売、MM購買、PP生産、WM倉庫、FI財務など）
2. 業務シナリオ（例：受注処理、在庫管理、出荷管理、購買管理など）

グループ化要件：
- 各インターフェースは1つのグループにのみ属する
- グループ名の形式：[SAPモジュール]_[業務シナリオ]（例：WM_出荷管理）
- 明確に分類できない場合は「その他_未分類」を使用

classify_interfacesツールを使用して分類結果を返してください。"""
        
        # 定义工具
        tools = [
            {
                'toolSpec': {
                    'name': 'classify_interfaces',
                    'description': 'SAPモジュールと業務シナリオに基づいてインターフェースを分類',
                    'inputSchema': {
                        'json': {
                            'type': 'object',
                            'properties': {
                                'categories': {
                                    'type': 'array',
                                    'description': '分類結果のリスト',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'category_name': {
                                                'type': 'string',
                                                'description': '分類名（形式：[SAPモジュール]_[業務シナリオ]）'
                                            },
                                            'category_description': {
                                                'type': 'string',
                                                'description': '分類の説明（日本語）'
                                            },
                                            'if_names': {
                                                'type': 'array',
                                                'description': 'この分類に属するインターフェース名のリスト',
                                                'items': {
                                                    'type': 'string'
                                                }
                                            }
                                        },
                                        'required': ['category_name', 'category_description', 'if_names']
                                    }
                                }
                            },
                            'required': ['categories']
                        }
                    }
                }
            }
        ]
        
        try:
            # 调用AI
            tool_calls = self.ai_generator._call_claude_with_tools(prompt, tools, max_tokens=2000)
            
            # 处理结果
            categories = {}
            category_descriptions = {}
            
            if 'classify_interfaces' in tool_calls:
                for category in tool_calls['classify_interfaces'].get('categories', []):
                    category_name = category.get('category_name')
                    if_names = category.get('if_names', [])
                    description = category.get('category_description', '')
                    
                    if category_name and if_names:
                        # 解析模块和场景（格式：模块_场景）
                        parts = category_name.split('_', 1)
                        if len(parts) == 2:
                            module, scenario = parts
                        else:
                            module, scenario = category_name, "未分類"
                        
                        categories[category_name] = (module, scenario, if_names)
                        category_descriptions[category_name] = description
            
            # 保存分类说明
            self.category_descriptions = category_descriptions
            
            return categories
            
        except Exception as e:
            print(f"    警告：AI分類に失敗しました: {e}")
            # フォールバック：すべてのIFを「その他_未分類」に配置
            return {"その他_未分類": ("その他", "未分類", list(if_dict.keys()))}
    
    def save_classified_data(
        self,
        input_df: pd.DataFrame,
        categories: Dict[str, Tuple[str, str, List[str]]],
        output_dir: str = "output"
    ) -> Dict[str, Tuple[Path, str, str]]:
        """保存分类后的数据到不同文件
        
        参数:
            input_df: 输入数据DataFrame
            categories: 分类结果字典 {category_name: (module, scenario, if_names)}
            output_dir: 输出目录（直接在output下创建分类文件夹）
            
        返回:
            文件路径字典: {category_name: (file_path, module, scenario)}
        """
        output_path = Path(output_dir)
        
        file_paths = {}
        
        for category_name, (module, scenario, if_names) in categories.items():
            # 筛选属于该分类的数据
            category_df = input_df[input_df['IF名'].isin(if_names)]
            
            if len(category_df) > 0:
                # 生成文件名（替换特殊字符）
                safe_name = category_name.replace('/', '_').replace('\\', '_')
                
                # 创建分类文件夹：output/[模块_分类]/
                category_dir = output_path / safe_name
                category_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存原始数据到分类文件夹
                filename = f"{safe_name}.xlsx"
                filepath = category_dir / filename
                
                # 保存到Excel
                category_df.to_excel(filepath, index=False, engine='openpyxl')
                file_paths[category_name] = (filepath, module, scenario)
                
                print(f"    ✓ {category_name}: {len(if_names)}個のIF, {len(category_df)}行のデータ -> {safe_name}/{filename}")
        
        return file_paths
    
    def generate_classification_report(
        self,
        categories: Dict[str, Tuple[str, str, List[str]]],
        output_path: str = "output/分類レポート.txt"
    ):
        """分類レポートを生成
        
        パラメータ:
            categories: 分類結果辞書 {category_name: (module, scenario, if_names)}
            output_path: レポートファイルパス（outputルートディレクトリに配置）
        """
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("IF分類レポート（SAPモジュールと業務シナリオ別）\n")
            f.write("=" * 80 + "\n\n")
            
            total_ifs = sum(len(data[2]) for data in categories.values())
            f.write(f"総分類数：{len(categories)}\n")
            f.write(f"総IF数：{total_ifs}\n\n")
            
            for idx, (category_name, (module, scenario, if_names)) in enumerate(sorted(categories.items()), 1):
                f.write(f"{idx}. {category_name}\n")
                f.write(f"   モジュール：{module}\n")
                f.write(f"   業務内容：{scenario}\n")
                
                # 分類説明がある場合
                if hasattr(self, 'category_descriptions') and category_name in self.category_descriptions:
                    f.write(f"   説明：{self.category_descriptions[category_name]}\n")
                
                f.write(f"   IF数：{len(if_names)}\n")
                f.write(f"   出力パス：output/{category_name.replace('/', '_').replace(chr(92), '_')}/\n")
                f.write(f"   IFリスト：\n")
                for if_name in sorted(if_names):
                    f.write(f"     - {if_name}\n")
                f.write("\n")
        
        print(f"    ✓ 分類レポートを保存しました：{report_path}")
