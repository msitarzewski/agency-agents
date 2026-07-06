#!/usr/bin/env python3
"""
分支管理工具 - 快速创建和管理开发分支
"""

import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

class BranchManager:
    """分支管理器"""
    
    def __init__(self):
        self.branch_types = {
            'feature': {
                'prefix': 'feature/',
                'base': 'develop',
                'description': '功能开发分支'
            },
            'enhancement': {
                'prefix': 'enhancement/',
                'base': 'develop', 
                'description': '中文增强分支'
            },
            'hotfix': {
                'prefix': 'hotfix/',
                'base': 'main',
                'description': '紧急修复分支'
            },
            'release': {
                'prefix': 'release/',
                'base': 'develop',
                'description': '发布准备分支'
            }
        }
    
    def run_git_command(self, command):
        """执行Git命令"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git命令执行失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return None
    
    def check_git_status(self):
        """检查Git状态"""
        status = self.run_git_command('git status --porcelain')
        if status is None:
            return False
        
        if status:
            logger.warning(f"⚠️  检测到未提交的更改:")
            print(status)
            response = input("是否继续？(y/N): ")
            return response.lower() == 'y'
        
        return True
    
    def get_current_branch(self):
        """获取当前分支"""
        return self.run_git_command('git branch --show-current')
    
    def branch_exists(self, branch_name):
        """检查分支是否存在"""
        result = self.run_git_command(f'git branch --list {branch_name}')
        return bool(result)
    
    def remote_branch_exists(self, branch_name):
        """检查远程分支是否存在"""
        result = self.run_git_command(f'git branch -r --list origin/{branch_name}')
        return bool(result)
    
    def create_branch(self, branch_type, branch_name, description=None):
        """创建新分支"""
        if branch_type not in self.branch_types:
            logger.error(f"❌ 不支持的分支类型: {branch_type}")
            logger.info(f"支持的类型: {', '.join(self.branch_types.keys())}")
            return False
        
        config = self.branch_types[branch_type]
        full_branch_name = f"{config['prefix']}{branch_name}"
        base_branch = config['base']
        
        logger.info(f"🌿 创建{config['description']}: {full_branch_name}")
        logger.info(f"📍 基于分支: {base_branch}")
        
        # 检查Git状态
        if not self.check_git_status():
            return False
        
        # 检查分支是否已存在
        if self.branch_exists(full_branch_name):
            logger.error(f"❌ 分支 {full_branch_name} 已存在")
            return False
        
        # 确保基础分支是最新的
        logger.info(f"🔄 更新基础分支 {base_branch}...")
        if not self.run_git_command(f'git checkout {base_branch}'):
            return False
        
        if not self.run_git_command(f'git pull origin {base_branch}'):
            logger.error(f"⚠️  拉取基础分支失败，继续使用本地版本")
        
        # 创建新分支
        logger.info(f"✨ 创建分支 {full_branch_name}...")
        if not self.run_git_command(f'git checkout -b {full_branch_name}'):
            return False
        
        # 推送到远程
        logger.info(f"📤 推送分支到远程...")
        if not self.run_git_command(f'git push -u origin {full_branch_name}'):
            logger.error(f"⚠️  推送到远程失败，分支仅在本地创建")
        
        # 创建分支信息文件
        self.create_branch_info(full_branch_name, branch_type, description)
        
        logger.info(f"✅ 分支 {full_branch_name} 创建成功！")
        logger.info(f"💡 现在可以开始在此分支上开发")
        
        return True
    
    def create_branch_info(self, branch_name, branch_type, description):
        """创建分支信息文件"""
        info_dir = Path('.git/branch_info')
        info_dir.mkdir(exist_ok=True)
        
        info_file = info_dir / f"{branch_name.replace('/', '_')}.json"
        
        import json

        branch_info = {
            'name': branch_name,
            'type': branch_type,
            'description': description or '',
            'created_at': datetime.now().isoformat(),
            'created_by': self.run_git_command('git config user.name') or 'Unknown'
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(branch_info, f, indent=2, ensure_ascii=False)
    
    def list_branches(self, branch_type=None):
        """列出分支"""
        logger.info(f"🌿 分支列表:")
        
        # 获取所有分支
        local_branches = self.run_git_command('git branch --format="%(refname:short)"')
        remote_branches = self.run_git_command('git branch -r --format="%(refname:short)"')
        
        if not local_branches:
            logger.error(f"❌ 获取分支列表失败")
            return
        
        current_branch = self.get_current_branch()
        
        # 按类型分组显示
        for btype, config in self.branch_types.items():
            if branch_type and branch_type != btype:
                continue
                
            prefix = config['prefix']
            matching_branches = [b for b in local_branches.split('\n') if b.startswith(prefix)]
            
            if matching_branches:
                logger.info(f"\n📂 {config['description']}:")
                for branch in matching_branches:
                    marker = " 👈 当前" if branch == current_branch else ""
                    remote_marker = " 📤" if f"origin/{branch}" in remote_branches else " 📍本地"
                    logger.info(f"  - {branch}{marker}{remote_marker}")
    
    def switch_branch(self, branch_name):
        """切换分支"""
        if not self.check_git_status():
            return False
        
        logger.info(f"🔄 切换到分支: {branch_name}")
        
        # 检查分支是否存在
        if not self.branch_exists(branch_name):
            # 检查是否是远程分支
            if self.remote_branch_exists(branch_name):
                logger.info(f"📥 检出远程分支: {branch_name}")
                if not self.run_git_command(f'git checkout -b {branch_name} origin/{branch_name}'):
                    return False
            else:
                logger.error(f"❌ 分支 {branch_name} 不存在")
                return False
        else:
            if not self.run_git_command(f'git checkout {branch_name}'):
                return False
        
        logger.info(f"✅ 已切换到分支: {branch_name}")
        return True
    
    def delete_branch(self, branch_name, force=False):
        """删除分支"""
        current_branch = self.get_current_branch()
        
        if branch_name == current_branch:
            logger.error(f"❌ 不能删除当前分支: {branch_name}")
            return False
        
        if branch_name in ['main', 'develop']:
            logger.error(f"❌ 不能删除保护分支: {branch_name}")
            return False
        
        logger.info(f"🗑️  删除分支: {branch_name}")
        
        # 检查分支是否已合并
        merged = self.run_git_command(f'git branch --merged develop | grep {branch_name}')
        
        if not merged and not force:
            logger.warning(f"⚠️  分支尚未合并到develop")
            response = input("确定要删除吗？(y/N): ")
            if response.lower() != 'y':
                return False
        
        # 删除本地分支
        delete_flag = '-D' if force else '-d'
        if not self.run_git_command(f'git branch {delete_flag} {branch_name}'):
            return False
        
        # 删除远程分支
        if self.remote_branch_exists(branch_name):
            response = input("是否同时删除远程分支？(Y/n): ")
            if response.lower() != 'n':
                self.run_git_command(f'git push origin --delete {branch_name}')
        
        logger.info(f"✅ 分支 {branch_name} 删除成功")
        return True
    
    def cleanup_branches(self):
        """清理已合并的分支"""
        logger.info(f"🧹 清理已合并的分支...")
        
        # 获取已合并到develop的分支
        merged_branches = self.run_git_command('git branch --merged develop')
        if not merged_branches:
            logger.error(f"❌ 获取已合并分支失败")
            return
        
        branches_to_delete = []
        for branch in merged_branches.split('\n'):
            branch = branch.strip().replace('*', '').strip()
            if branch and branch not in ['main', 'develop']:
                branches_to_delete.append(branch)
        
        if not branches_to_delete:
            logger.info(f"✅ 没有需要清理的分支")
            return
        
        logger.info(f"📋 以下分支已合并到develop:")
        for branch in branches_to_delete:
            logger.info(f"  - {branch}")
        
        response = input("是否删除这些分支？(y/N): ")
        if response.lower() == 'y':
            for branch in branches_to_delete:
                self.run_git_command(f'git branch -d {branch}')
            logger.info(f"✅ 已删除 {len(branches_to_delete)} 个分支")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分支管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建分支
    create_parser = subparsers.add_parser('create', help='创建新分支')
    create_parser.add_argument('type', choices=['feature', 'enhancement', 'hotfix', 'release'], 
                              help='分支类型')
    create_parser.add_argument('name', help='分支名称')
    create_parser.add_argument('-d', '--description', help='分支描述')
    
    # 列出分支
    list_parser = subparsers.add_parser('list', help='列出分支')
    list_parser.add_argument('-t', '--type', choices=['feature', 'enhancement', 'hotfix', 'release'],
                            help='过滤分支类型')
    
    # 切换分支
    switch_parser = subparsers.add_parser('switch', help='切换分支')
    switch_parser.add_argument('name', help='分支名称')
    
    # 删除分支
    delete_parser = subparsers.add_parser('delete', help='删除分支')
    delete_parser.add_argument('name', help='分支名称')
    delete_parser.add_argument('-f', '--force', action='store_true', help='强制删除')
    
    # 清理分支
    subparsers.add_parser('cleanup', help='清理已合并的分支')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = BranchManager()
    
    if args.command == 'create':
        manager.create_branch(args.type, args.name, args.description)
    elif args.command == 'list':
        manager.list_branches(args.type)
    elif args.command == 'switch':
        manager.switch_branch(args.name)
    elif args.command == 'delete':
        manager.delete_branch(args.name, args.force)
    elif args.command == 'cleanup':
        manager.cleanup_branches()

if __name__ == "__main__":
    main()
