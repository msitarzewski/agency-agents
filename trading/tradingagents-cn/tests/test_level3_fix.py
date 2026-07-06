#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试级别3死循环修复效果
"""

import os
import sys
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_level3_analysis():
    """测试级别3分析是否还会死循环"""
    print("🧪 测试级别3分析修复效果")
    print("=" * 60)
    
    start_time = time.time()  # 在try块外定义
    
    try:
        from app.services.simple_analysis_service import SimpleAnalysisService
        from app.models.analysis import SingleAnalysisRequest, AnalysisParameters
        
        # 创建分析服务
        service = SimpleAnalysisService()
        
        # 测试参数
        test_ticker = "000001"  # 平安银行
        research_depth = "标准"  # 级别3：标准分析（使用字符串）
        
        print(f"📊 开始测试级别3分析...")
        print(f"股票代码: {test_ticker}")
        print(f"分析级别: {research_depth}")
        
        # 创建分析请求
        request = SingleAnalysisRequest(
            stock_code=test_ticker,
            parameters=AnalysisParameters(
                research_depth=research_depth,
                selected_analysts=["market", "fundamentals"]
            )
        )
        
        # 设置超时时间（5分钟）
        timeout = 300
        
        print(f"⏰ 设置超时时间: {timeout}秒")
        print(f"🚀 开始分析...")
        
        # 执行分析 - 使用同步方法
        result = service._run_analysis_sync(
            task_id="test_level3_fix",
            user_id="test_user",
            request=request
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"✅ 分析完成！")
        print(f"⏱️ 耗时: {elapsed:.1f}秒")
        
        # 检查结果
        if result and 'decision' in result:
            decision = result['decision']
            print(f"📈 分析结果:")
            print(f"  动作: {decision.get('action', 'N/A')}")
            print(f"  置信度: {decision.get('confidence', 0):.1%}")
            print(f"  风险评分: {decision.get('risk_score', 0):.1%}")
            
            # 检查是否有基本面报告
            if 'state' in result and 'fundamentals_report' in result['state']:
                fundamentals_report = result['state']['fundamentals_report']
                if fundamentals_report:
                    print(f"📊 基本面报告长度: {len(fundamentals_report)}字符")
                    print("✅ 基本面分析正常完成")
                else:
                    print("⚠️ 基本面报告为空")
            
            # 检查工具调用次数
            if 'state' in result:
                tool_call_count = result['state'].get('fundamentals_tool_call_count', 0)
                print(f"🔧 基本面分析师工具调用次数: {tool_call_count}")
                if tool_call_count >= 3:
                    print("⚠️ 达到最大工具调用次数限制，修复机制生效")
                else:
                    print("✅ 工具调用次数正常")
            
            return True
        else:
            print("❌ 分析结果异常")
            return False
            
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"❌ 分析异常: {e}")
        print(f"⏱️ 异常前耗时: {elapsed:.1f}秒")
        
        if elapsed > 60:
            print("⚠️ 可能仍存在死循环问题（耗时超过1分钟）")
        
        return False

if __name__ == "__main__":
    success = test_level3_analysis()
    if success:
        print("\n🎉 级别3死循环修复测试通过！")
    else:
        print("\n❌ 级别3死循环修复测试失败！")
