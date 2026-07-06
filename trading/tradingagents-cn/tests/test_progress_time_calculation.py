"""
测试进度时间计算逻辑
验证修复后的时间计算是否正确
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta
from app.services.memory_state_manager import TaskState, TaskStatus


def test_progress_time_calculation_basic():
    """测试基本的时间计算逻辑 - 使用预估总时长"""
    # 创建一个任务，预估总时长5分钟，已运行5秒，进度1%
    task = TaskState(
        task_id="test_task_1",
        user_id="test_user",
        stock_code="000001",
        status=TaskStatus.RUNNING,
        progress=1,  # 1%
        start_time=datetime.now() - timedelta(seconds=5),
        estimated_duration=300  # 预估5分钟
    )

    data = task.to_dict()

    # 验证时间计算
    assert data['elapsed_time'] == pytest.approx(5, abs=0.5), "已用时间应该约为5秒"

    # 预计总时长 = 预估值（固定）= 300秒（5分钟）
    assert data['estimated_total_time'] == 300, "预计总时长应该为预估的300秒（5分钟）"

    # 预计剩余 = 预估总时长 - 已用时间 = 300 - 5 = 295秒
    expected_remaining = 300 - 5
    assert data['remaining_time'] == pytest.approx(expected_remaining, abs=1), \
        f"预计剩余应该约为{expected_remaining}秒（{expected_remaining/60:.1f}分钟）"

    print(f"✅ 测试通过：")
    print(f"   已用时间: {data['elapsed_time']:.1f}秒")
    print(f"   预计总时长: {data['estimated_total_time']:.1f}秒 ({data['estimated_total_time']/60:.1f}分钟)")
    print(f"   预计剩余: {data['remaining_time']:.1f}秒 ({data['remaining_time']/60:.1f}分钟)")


def test_progress_time_calculation_10_percent():
    """测试10%进度的时间计算"""
    # 创建一个任务，预估总时长5分钟，已运行30秒，进度10%
    task = TaskState(
        task_id="test_task_2",
        user_id="test_user",
        stock_code="000001",
        status=TaskStatus.RUNNING,
        progress=10,  # 10%
        start_time=datetime.now() - timedelta(seconds=30),
        estimated_duration=300  # 预估5分钟
    )

    data = task.to_dict()

    # 验证时间计算
    assert data['elapsed_time'] == pytest.approx(30, abs=0.5), "已用时间应该约为30秒"

    # 预计总时长 = 预估值（固定）= 300秒（5分钟）
    assert data['estimated_total_time'] == 300, "预计总时长应该为预估的300秒（5分钟）"

    # 预计剩余 = 预估总时长 - 已用时间 = 300 - 30 = 270秒（4.5分钟）
    expected_remaining = 300 - 30
    assert data['remaining_time'] == pytest.approx(expected_remaining, abs=1), \
        f"预计剩余应该约为{expected_remaining}秒（{expected_remaining/60:.1f}分钟）"

    print(f"✅ 测试通过：")
    print(f"   已用时间: {data['elapsed_time']:.1f}秒")
    print(f"   预计总时长: {data['estimated_total_time']:.1f}秒 ({data['estimated_total_time']/60:.1f}分钟)")
    print(f"   预计剩余: {data['remaining_time']:.1f}秒 ({data['remaining_time']/60:.1f}分钟)")


def test_progress_time_calculation_50_percent():
    """测试50%进度的时间计算"""
    # 创建一个任务，预估总时长5分钟，已运行150秒，进度50%
    task = TaskState(
        task_id="test_task_3",
        user_id="test_user",
        stock_code="000001",
        status=TaskStatus.RUNNING,
        progress=50,  # 50%
        start_time=datetime.now() - timedelta(seconds=150),
        estimated_duration=300  # 预估5分钟
    )

    data = task.to_dict()

    # 验证时间计算
    assert data['elapsed_time'] == pytest.approx(150, abs=0.5), "已用时间应该约为150秒"

    # 预计总时长 = 预估值（固定）= 300秒（5分钟）
    assert data['estimated_total_time'] == 300, "预计总时长应该为预估的300秒（5分钟）"

    # 预计剩余 = 预估总时长 - 已用时间 = 300 - 150 = 150秒（2.5分钟）
    expected_remaining = 300 - 150
    assert data['remaining_time'] == pytest.approx(expected_remaining, abs=1), \
        f"预计剩余应该约为{expected_remaining}秒（{expected_remaining/60:.1f}分钟）"

    print(f"✅ 测试通过：")
    print(f"   已用时间: {data['elapsed_time']:.1f}秒")
    print(f"   预计总时长: {data['estimated_total_time']:.1f}秒 ({data['estimated_total_time']/60:.1f}分钟)")
    print(f"   预计剩余: {data['remaining_time']:.1f}秒 ({data['remaining_time']/60:.1f}分钟)")


def test_progress_time_calculation_zero_progress():
    """测试0%进度的时间计算（使用默认预估）"""
    # 创建一个任务，已运行5秒，进度0%
    task = TaskState(
        task_id="test_task_4",
        user_id="test_user",
        stock_code="000001",
        status=TaskStatus.RUNNING,
        progress=0,  # 0%
        start_time=datetime.now() - timedelta(seconds=5)
    )

    data = task.to_dict()

    # 验证时间计算
    assert data['elapsed_time'] == pytest.approx(5, abs=0.5), "已用时间应该约为5秒"

    # 进度为0时，使用默认预估时间（5分钟）
    assert data['estimated_total_time'] == 300, "预计总时长应该为默认的300秒（5分钟）"
    # 预计剩余 = 预估总时长 - 已用时间 = 300 - 5 = 295秒
    expected_remaining = 300 - 5
    assert data['remaining_time'] == pytest.approx(expected_remaining, abs=1), \
        f"预计剩余应该约为{expected_remaining}秒（{expected_remaining/60:.1f}分钟）"

    print(f"✅ 测试通过：")
    print(f"   已用时间: {data['elapsed_time']:.1f}秒")
    print(f"   预计总时长: {data['estimated_total_time']:.1f}秒 ({data['estimated_total_time']/60:.1f}分钟)")
    print(f"   预计剩余: {data['remaining_time']:.1f}秒 ({data['remaining_time']/60:.1f}分钟)")


def test_progress_time_calculation_completed():
    """测试100%进度的时间计算"""
    start_time = datetime.now() - timedelta(seconds=300)
    end_time = datetime.now()
    
    task = TaskState(
        task_id="test_task_5",
        user_id="test_user",
        stock_code="000001",
        status=TaskStatus.COMPLETED,
        progress=100,  # 100%
        start_time=start_time,
        end_time=end_time,
        execution_time=300
    )
    
    data = task.to_dict()
    
    # 验证时间计算
    assert data['elapsed_time'] == 300, "已用时间应该为300秒"
    assert data['estimated_total_time'] == 300, "预计总时长应该等于已用时间"
    assert data['remaining_time'] == 0, "预计剩余应该为0"
    
    print(f"✅ 测试通过：")
    print(f"   已用时间: {data['elapsed_time']:.1f}秒")
    print(f"   预计总时长: {data['estimated_total_time']:.1f}秒 ({data['estimated_total_time']/60:.1f}分钟)")
    print(f"   预计剩余: {data['remaining_time']:.1f}秒")


if __name__ == "__main__":
    print("=" * 60)
    print("测试进度时间计算逻辑")
    print("=" * 60)
    
    print("\n1. 测试1%进度（已运行5秒）")
    print("-" * 60)
    test_progress_time_calculation_basic()
    
    print("\n2. 测试10%进度（已运行30秒）")
    print("-" * 60)
    test_progress_time_calculation_10_percent()
    
    print("\n3. 测试50%进度（已运行150秒）")
    print("-" * 60)
    test_progress_time_calculation_50_percent()
    
    print("\n4. 测试0%进度（已运行5秒）")
    print("-" * 60)
    test_progress_time_calculation_zero_progress()
    
    print("\n5. 测试100%进度（已完成）")
    print("-" * 60)
    test_progress_time_calculation_completed()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)

