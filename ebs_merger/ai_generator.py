"""AI内容生成模块

使用SAP AI Core的Claude模型生成IF概要、代表項目名和グルーピング後のIF名。
使用converse API和tool calling一次性获取所有信息。
"""

import os
import requests
import pandas as pd
import json
from typing import Dict, List
from dotenv import load_dotenv
from ebs_merger.if_grouper import IFInfo

# 加载.env文件
load_dotenv()


class AIGenerator:
    """AI内容生成器"""
    
    def __init__(
        self,
        auth_url: str = None,
        client_id: str = None,
        client_secret: str = None,
        base_url: str = None,
        resource_group: str = "default",
        deployment_id: str = None
    ):
        """初始化AI生成器
        
        参数:
            auth_url: SAP AI Core认证URL
            client_id: 客户端ID
            client_secret: 客户端密钥
            base_url: SAP AI Core基础URL
            resource_group: 资源组名称
            deployment_id: Claude模型的deployment ID
        """
        # 从环境变量或参数获取配置
        self.auth_url = auth_url or os.getenv('AICORE_AUTH_URL')
        self.client_id = client_id or os.getenv('AICORE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('AICORE_CLIENT_SECRET')
        self.base_url = base_url or os.getenv('AICORE_BASE_URL')
        self.resource_group = resource_group or os.getenv('AICORE_RESOURCE_GROUP', 'default')
        # 使用Claude 4.5 Sonnet的deployment ID
        self.deployment_id = deployment_id or os.getenv('AICORE_DEPLOYMENT_ID', 'd9eb209d94991674')
        
        self.access_token = None
        
        # 設定の検証
        if not all([self.auth_url, self.client_id, self.client_secret, self.base_url]):
            raise ValueError(
                "SAP AI Core設定が不足しています。環境変数または.envファイルで以下を設定してください：\n"
                "AICORE_AUTH_URL, AICORE_CLIENT_ID, AICORE_CLIENT_SECRET, AICORE_BASE_URL"
            )
    
    def _get_access_token(self) -> str:
        """アクセストークンを取得"""
        if self.access_token:
            return self.access_token
        
        token_url = f"{self.auth_url}/oauth/token"
        
        response = requests.post(
            token_url,
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'}
        )
        
        if response.status_code != 200:
            raise Exception(f"アクセストークンの取得に失敗しました: {response.status_code} - {response.text}")
        
        self.access_token = response.json()['access_token']
        return self.access_token
    
    def _call_claude_with_tools(
        self,
        prompt: str,
        tools: List[Dict],
        max_tokens: int = 8192
    ) -> Dict:
        """ツール呼び出しを使用してClaudeモデルを呼び出す
        
        パラメータ:
            prompt: プロンプト
            tools: ツール定義リスト（toolSpecでラップする必要がある）
            max_tokens: 最大トークン数（デフォルト: 8192、制限なし）
            
        戻り値:
            ツール呼び出し結果辞書
        """
        token = self._get_access_token()
        
        # 使用converse API
        url = f"{self.base_url}/inference/deployments/{self.deployment_id}/converse"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'AI-Resource-Group': self.resource_group,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': prompt
                        }
                    ]
                }
            ],
            'toolConfig': {
                'tools': tools,
                'toolChoice': {'any': {}}  # 强制使用工具
            },
            'inferenceConfig': {
                'maxTokens': max_tokens,
                'temperature': 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Claudeモデルの呼び出しに失敗しました: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # ツール呼び出し結果の抽出
        tool_calls = {}
        for content_block in result.get('output', {}).get('message', {}).get('content', []):
            if 'toolUse' in content_block:
                tool_use = content_block['toolUse']
                tool_name = tool_use.get('name')
                tool_input = tool_use.get('input', {})
                tool_calls[tool_name] = tool_input
        
        return tool_calls
    
    def generate_all_if_info(
        self,
        if_dict: Dict[str, IFInfo],
        input_df: pd.DataFrame
    ) -> Dict[str, Dict[str, str]]:
        """すべてのIFの情報を一括生成（概要、代表項目名）
        
        パラメータ:
            if_dict: IF情報辞書
            input_df: 入力データDataFrame
            
        戻り値:
            辞書形式: {if_name: {'summary': '...', 'representative_item': '...'}}
        """
        # すべてのIFの情報を準備
        if_info_list = []
        for if_name, if_info in if_dict.items():
            if_data = input_df[input_df['IF名'] == if_name]
            tables = if_data['EBSテーブル名'].unique().tolist()
            items = if_data['項目名'].tolist()
            
            if_info_list.append({
                'if_name': if_name,
                'doc_number': if_info.doc_number,
                'tables': tables[:3],  # 最大3テーブル
                'items': items,  # 所有項目
                'item_count': if_info.item_count,
                'top_20_percent_count': max(1, int(if_info.item_count * 0.2))  # 20%的项目数
            })
        
        # プロンプトの構築
        prompt = f"""以下の{len(if_info_list)}個の日本語インターフェース（IF）の情報を分析し、各インターフェースの概要を生成し、代表項目名を選択してください。

インターフェース情報：
"""
        for idx, info in enumerate(if_info_list, 1):
            # 限制显示的项目数量，避免提示词过长
            sample_items = info['items'][:20]  # 最多显示20个项目作为参考
            prompt += f"""
{idx}. IF名: {info['if_name']}
   文書管理番号: {info['doc_number']}
   関連テーブル: {', '.join(info['tables'])}
   項目総数: {info['item_count']}
   選択すべき代表項目数: {info['top_20_percent_count']}個（項目総数の約20%）
   参考項目（最初の{len(sample_items)}個）: {', '.join(sample_items)}
"""
        
        prompt += """
提供されたツールを使用して、各インターフェースの情報を生成してください。要件：

1. IF概要：日本語で簡潔な機能説明を生成（30-50文字）、インターフェースの主な機能と用途を要約

2. 代表項目名：各インターフェースの項目総数の約20%に相当する代表的な項目名を選択してください。選択基準：
   ① SAP系統における重要性：項目名がSAPシステムで一般的に使用されるキー項目（例：伝票番号、品目コード、顧客コード、注文番号、会計年度、会社コード、プラントコード、在庫組織、勘定科目など）であるかを優先的に考慮
   ② 業務シナリオとの関連性：IF名から推測される業務シナリオにおいて、最も代表的で重要な項目を選択（例：「出荷指示」というIF名の場合、出荷関連の項目を優先）
   
   選択した項目名をカンマで区切って返してください（例：項目総数が50個の場合、約10個の項目名を選択）

generate_all_if_infoツールを呼び出して、すべてのインターフェースの情報を一度に返してください。"""
        
        # ツールの定義 - すべてのIF情報を一度に返すように変更
        tools = [
            {
                'toolSpec': {
                    'name': 'generate_all_if_info',
                    'description': 'すべてのインターフェースの概要と代表項目名を生成',
                    'inputSchema': {
                        'json': {
                            'type': 'object',
                            'properties': {
                                'interfaces': {
                                    'type': 'array',
                                    'description': 'すべてのインターフェースの情報リスト',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'if_name': {
                                                'type': 'string',
                                                'description': 'インターフェース名'
                                            },
                                            'summary': {
                                                'type': 'string',
                                                'description': 'インターフェース機能概要（日本語、30-50文字）'
                                            },
                                            'representative_item': {
                                                'type': 'string',
                                                'description': '代表項目名'
                                            }
                                        },
                                        'required': ['if_name', 'summary', 'representative_item']
                                    }
                                }
                            },
                            'required': ['interfaces']
                        }
                    }
                }
            }
        ]
        
        try:
            # 调用Claude
            tool_calls = self._call_claude_with_tools(prompt, tools)
            
            # 处理结果
            results = {}
            if 'generate_all_if_info' in tool_calls:
                interfaces = tool_calls['generate_all_if_info'].get('interfaces', [])
                print(f"    AI返回了 {len(interfaces)} 個のIF情報")
                
                # 收集AI返回的IF名称
                returned_if_names = set()
                for interface in interfaces:
                    if_name = interface.get('if_name')
                    summary = interface.get('summary', '')
                    rep_item = interface.get('representative_item', '')
                    
                    if if_name:
                        returned_if_names.add(if_name)
                        results[if_name] = {
                            'summary': summary,
                            'representative_item': rep_item
                        }
                
                # 检查是否有IF没有被返回
                expected_if_names = set(if_dict.keys())
                missing_if_names = expected_if_names - returned_if_names
                if missing_if_names:
                    print(f"      警告：{len(missing_if_names)}個のIFがAI応答に含まれていません")
                    # 输出调试信息（限制输出长度避免编码问题）
                    import json
                    print(f"      期待: {len(expected_if_names)}個, 返回: {len(returned_if_names)}個")
            else:
                print(f"    警告：AIがgenerate_all_if_infoツールを呼び出しませんでした")
            
            return results
            
        except Exception as e:
            print(f"    警告：AI一括生成に失敗しました: {e}")
            return {}
    
    def generate_merged_if_name(
        self,
        group_members: List[str],
        if_dict: Dict[str, IFInfo],
        input_df: pd.DataFrame
    ) -> str:
        """グルーピング後のIF名を生成
        
        パラメータ:
            group_members: グループ内のIF名リスト
            if_dict: IF情報辞書
            input_df: 入力データDataFrame
            
        戻り値:
            マージ後のIF名
        """
        if len(group_members) == 1:
            return group_members[0]
        
        # すべてのIFの情報を収集
        if_info_list = []
        for if_name in group_members:
            if_data = input_df[input_df['IF名'] == if_name]
            tables = if_data['EBSテーブル名'].unique().tolist()
            if_info_list.append(f"- {if_name}（関連テーブル：{', '.join(tables[:3])}）")
        
        prompt = f"""以下のマージ対象インターフェース情報に基づいて、新しい簡潔な日本語インターフェース名を生成してください（20-40文字）：

{chr(10).join(if_info_list)}

要件：
1. 名前はすべてのインターフェースの共通機能を要約すること
2. 日本語を使用すること
3. 専門的かつ簡潔であること

generate_merged_nameツールを使用して新しいインターフェース名を返してください。"""
        
        tools = [
            {
                'toolSpec': {
                    'name': 'generate_merged_name',
                    'description': 'マージ後のインターフェース名を生成',
                    'inputSchema': {
                        'json': {
                            'type': 'object',
                            'properties': {
                                'merged_name': {
                                    'type': 'string',
                                    'description': 'マージ後のインターフェース名（日本語、20-40文字）'
                                }
                            },
                            'required': ['merged_name']
                        }
                    }
                }
            }
        ]
        
        try:
            tool_calls = self._call_claude_with_tools(prompt, tools)
            
            if 'generate_merged_name' in tool_calls:
                return tool_calls['generate_merged_name'].get('merged_name', '')
            
            # 返されない場合、デフォルトロジックを使用
            return "_".join(sorted(group_members))
            
        except Exception as e:
            print(f"    警告：AIマージIF名生成に失敗しました: {e}")
            return "_".join(sorted(group_members))
