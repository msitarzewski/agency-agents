#!/usr/bin/env python3
"""
用户活动记录管理工具
用于查看、分析和管理用户操作行为记录
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

def get_activity_dir():
    """获取活动记录目录"""
    return Path(__file__).parent.parent / "web" / "data" / "user_activities"

def load_activities(start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
    """加载活动记录"""
    activity_dir = get_activity_dir()
    activities = []
    
    if not activity_dir.exists():
        print("❌ 活动记录目录不存在")
        return activities
    
    # 确定日期范围
    if start_date is None:
        start_date = datetime.now() - timedelta(days=7)
    if end_date is None:
        end_date = datetime.now()
    
    # 遍历日期范围内的文件
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    while current_date <= end_date_only:
        date_str = current_date.strftime("%Y-%m-%d")
        activity_file = activity_dir / f"user_activities_{date_str}.jsonl"
        
        if activity_file.exists():
            try:
                with open(activity_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            activity = json.loads(line.strip())
                            activity_time = datetime.fromtimestamp(activity['timestamp'])
                            if start_date <= activity_time <= end_date:
                                activities.append(activity)
            except Exception as e:
                print(f"❌ 读取文件失败 {activity_file}: {e}")
        
        current_date += timedelta(days=1)
    
    return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

def list_activities(args):
    """列出用户活动"""
    print("📋 用户活动记录")
    print("=" * 80)
    
    # 解析日期参数
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    activities = load_activities(start_date, end_date)
    
    if not activities:
        print("📭 未找到活动记录")
        return
    
    # 应用过滤条件
    if args.username:
        activities = [a for a in activities if a.get('username') == args.username]
    
    if args.action_type:
        activities = [a for a in activities if a.get('action_type') == args.action_type]
    
    # 应用限制
    if args.limit:
        activities = activities[:args.limit]
    
    print(f"📊 找到 {len(activities)} 条记录")
    print()
    
    # 显示活动记录
    for i, activity in enumerate(activities, 1):
        timestamp = datetime.fromtimestamp(activity['timestamp'])
        success_icon = "✅" if activity.get('success', True) else "❌"
        
        print(f"{i:3d}. {success_icon} {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     👤 用户: {activity.get('username', 'unknown')} ({activity.get('user_role', 'unknown')})")
        print(f"     🔧 操作: {activity.get('action_type', 'unknown')} - {activity.get('action_name', 'unknown')}")
        
        if activity.get('details'):
            details_str = ", ".join([f"{k}={v}" for k, v in activity['details'].items()])
            print(f"     📝 详情: {details_str}")
        
        if activity.get('duration_ms'):
            print(f"     ⏱️ 耗时: {activity['duration_ms']}ms")
        
        if not activity.get('success', True) and activity.get('error_message'):
            print(f"     ❌ 错误: {activity['error_message']}")
        
        print()

def show_statistics(args):
    """显示统计信息"""
    print("📊 用户活动统计")
    print("=" * 80)
    
    # 解析日期参数
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    activities = load_activities(start_date, end_date)
    
    if not activities:
        print("📭 未找到活动记录")
        return
    
    # 基本统计
    total_activities = len(activities)
    unique_users = len(set(a['username'] for a in activities))
    successful_activities = sum(1 for a in activities if a.get('success', True))
    success_rate = (successful_activities / total_activities * 100) if total_activities > 0 else 0
    
    print(f"📈 总体统计:")
    print(f"   📊 总活动数: {total_activities}")
    print(f"   👥 活跃用户: {unique_users}")
    print(f"   ✅ 成功率: {success_rate:.1f}%")
    print()
    
    # 按活动类型统计
    activity_types = {}
    for activity in activities:
        action_type = activity.get('action_type', 'unknown')
        activity_types[action_type] = activity_types.get(action_type, 0) + 1
    
    print(f"📋 按活动类型统计:")
    for action_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_activities * 100) if total_activities > 0 else 0
        print(f"   {action_type:15s}: {count:4d} ({percentage:5.1f}%)")
    print()
    
    # 按用户统计
    user_activities = {}
    for activity in activities:
        username = activity.get('username', 'unknown')
        user_activities[username] = user_activities.get(username, 0) + 1
    
    print(f"👥 按用户统计:")
    for username, count in sorted(user_activities.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_activities * 100) if total_activities > 0 else 0
        print(f"   {username:15s}: {count:4d} ({percentage:5.1f}%)")
    print()
    
    # 按日期统计
    daily_activities = {}
    for activity in activities:
        date_str = datetime.fromtimestamp(activity['timestamp']).strftime('%Y-%m-%d')
        daily_activities[date_str] = daily_activities.get(date_str, 0) + 1
    
    print(f"📅 按日期统计:")
    for date_str in sorted(daily_activities.keys()):
        count = daily_activities[date_str]
        print(f"   {date_str}: {count:4d}")
    print()
    
    # 耗时统计
    durations = [a.get('duration_ms', 0) for a in activities if a.get('duration_ms')]
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        print(f"⏱️ 耗时统计:")
        print(f"   平均耗时: {avg_duration:.1f}ms")
        print(f"   最大耗时: {max_duration}ms")
        print(f"   最小耗时: {min_duration}ms")
        print()

def export_activities(args):
    """导出活动记录"""
    print("📤 导出用户活动记录")
    print("=" * 80)
    
    # 解析日期参数
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    activities = load_activities(start_date, end_date)
    
    if not activities:
        print("📭 未找到活动记录")
        return
    
    # 应用过滤条件
    if args.username:
        activities = [a for a in activities if a.get('username') == args.username]
    
    if args.action_type:
        activities = [a for a in activities if a.get('action_type') == args.action_type]
    
    # 确定输出文件
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"user_activities_export_{timestamp}.csv")
    
    try:
        # 转换为DataFrame并导出
        df_data = []
        for activity in activities:
            row = {
                'timestamp': activity['timestamp'],
                'datetime': datetime.fromtimestamp(activity['timestamp']).isoformat(),
                'username': activity.get('username', ''),
                'user_role': activity.get('user_role', ''),
                'action_type': activity.get('action_type', ''),
                'action_name': activity.get('action_name', ''),
                'session_id': activity.get('session_id', ''),
                'ip_address': activity.get('ip_address', ''),
                'page_url': activity.get('page_url', ''),
                'duration_ms': activity.get('duration_ms', ''),
                'success': activity.get('success', True),
                'error_message': activity.get('error_message', ''),
                'details': json.dumps(activity.get('details', {}), ensure_ascii=False)
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 成功导出 {len(activities)} 条记录到: {output_file}")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")

def cleanup_activities(args):
    """清理旧的活动记录"""
    print("🗑️ 清理旧的活动记录")
    print("=" * 80)
    
    activity_dir = get_activity_dir()
    if not activity_dir.exists():
        print("❌ 活动记录目录不存在")
        return
    
    days_to_keep = args.days or 90
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    print(f"🗓️ 将删除 {cutoff_date.strftime('%Y-%m-%d')} 之前的记录")
    
    if not args.force:
        confirm = input("⚠️ 确认删除吗? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return
    
    try:
        for activity_file in activity_dir.glob("user_activities_*.jsonl"):
            try:
                # 从文件名提取日期
                date_str = activity_file.stem.replace("user_activities_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    activity_file.unlink()
                    deleted_count += 1
                    print(f"🗑️ 删除: {activity_file.name}")
                    
            except ValueError:
                # 文件名格式不正确，跳过
                continue
                
        print(f"✅ 成功删除 {deleted_count} 个文件")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="用户活动记录管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出用户活动')
    list_parser.add_argument('--username', help='按用户名过滤')
    list_parser.add_argument('--action-type', help='按活动类型过滤')
    list_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    list_parser.add_argument('--limit', type=int, help='限制返回记录数')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    stats_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出活动记录')
    export_parser.add_argument('--username', help='按用户名过滤')
    export_parser.add_argument('--action-type', help='按活动类型过滤')
    export_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    export_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    export_parser.add_argument('--output', help='输出文件路径')
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧记录')
    cleanup_parser.add_argument('--days', type=int, default=90, help='保留天数 (默认90天)')
    cleanup_parser.add_argument('--force', action='store_true', help='强制删除，不询问确认')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_activities(args)
        elif args.command == 'stats':
            show_statistics(args)
        elif args.command == 'export':
            export_activities(args)
        elif args.command == 'cleanup':
            cleanup_activities(args)
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    main()