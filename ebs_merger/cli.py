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
        
        # 初始化组件
        self.loader = DataLoader()
        self.grouper = IFGrouper()
        self.calculator = SimilarityCalculator()
        self.merge_grouper = MergeGrouper()
        self.result_generator = ResultGenerator()
        self.template_filler = TemplateFiller()
    
    def run(self):
        """执行完整的分析和合并流程"""
        try:
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 打印启动信息
            print("=" * 60)
            print("开始批量分析EBS设计书...")
            print("=" * 60)
            print(f"输入文件夹：{self.input_dir}")
            print(f"输出文件夹：{self.output_dir}")
            print(f"相似度阈值：{self.threshold * 100:.0f}%")
            print()
            
            # 查找所有Excel文件
            excel_files = self.find_excel_files()
            
            if not excel_files:
                print(f"错误：在 '{self.input_dir}' 文件夹中未找到Excel文件")
                print("请将Excel文件放入input文件夹后重试")
                return 1
            
            print(f"发现 {len(excel_files)} 个Excel文件")
            print()
            
            # 处理每个文件
            success_count = 0
            fail_count = 0
            
            for idx, input_file in enumerate(excel_files, 1):
                print(f"[{idx}/{len(excel_files)}] 处理文件: {input_file.name}")
                print("-" * 60)
                
                try:
                    self.process_single_file(input_file)
                    success_count += 1
                    print("✓ 处理成功")
                except Exception as e:
                    fail_count += 1
                    print(f"✗ 处理失败: {e}")
                
                print()
            
            # 打印总体摘要
            self.print_batch_summary(success_count, fail_count, len(excel_files))
            
            return 0 if fail_count == 0 else 1
            
        except Exception as e:
            print(f"\n错误：处理过程中发生意外错误：{str(e)}")
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
        # 生成输出文件名
        output_filename = f"グルーピング結果_{input_file.stem}.xlsx"
        output_path = self.output_dir / output_filename
        
        # 1. 读取Excel文件
        print(f"  正在读取Excel文件...")
        df = self.loader.load_excel(str(input_file))
        print(f"  成功读取 {len(df)} 行数据")
        
        # 2. 分组IF
        print(f"  正在分组IF...")
        if_dict = self.grouper.group_by_if(df)
        print(f"  发现 {len(if_dict)} 个IF")
        
        # 3. 计算相似度
        print(f"  正在计算相似度...")
        similar_pairs = self.calculator.build_similarity_matrix(
            if_dict, 
            self.threshold
        )
        print(f"  发现 {len(similar_pairs)} 对相似IF")
        
        # 4. 生成分组
        print(f"  正在生成分组...")
        groups = self.merge_grouper.group_similar_ifs(if_dict, similar_pairs)
        group_assignments = self.merge_grouper.assign_group_ids(groups)
        print(f"  生成 {len(groups)} 个分组")
        
        # 5. 写入输出文件
        print(f"  正在写入输出文件...")
        self.result_generator.generate_output(
            if_dict,
            group_assignments,
            similar_pairs,
            str(output_path)
        )
        print(f"  输出文件已保存：{output_path.name}")
        
        # 6. 生成合并组的模板文件
        print(f"  正在生成合并组的模板文件...")
        self.template_filler.fill_merged_groups(
            if_dict,
            group_assignments,
            similar_pairs,
            df,
            str(self.output_dir)
        )
        
        # 7. 打印文件摘要
        self.print_file_summary(if_dict, groups, group_assignments)
    
    def print_file_summary(self, if_dict, groups, group_assignments):
        """打印单个文件的处理摘要
        
        参数:
            if_dict: IF信息字典
            groups: 分组结果
            group_assignments: IF到分组ID的映射
        """
        # 统计需要合并的IF数量
        independent_count = sum(1 for group in groups.values() if len(group) == 1)
        total_merge_ifs = sum(len(group) for group in groups.values() if len(group) > 1)
        
        print(f"  总IF数：{len(if_dict)} | 需要合并：{total_merge_ifs} | 独立：{independent_count} | 分组数：{len(groups)}")
    
    def print_batch_summary(self, success_count, fail_count, total_count):
        """打印批量处理摘要
        
        参数:
            success_count: 成功处理的文件数
            fail_count: 失败的文件数
            total_count: 总文件数
        """
        print("=" * 60)
        print("批量处理完成！")
        print("=" * 60)
        print(f"总文件数：{total_count}")
        print(f"成功处理：{success_count}")
        print(f"处理失败：{fail_count}")
        print(f"输出文件夹：{self.output_dir}")
        print("=" * 60)
