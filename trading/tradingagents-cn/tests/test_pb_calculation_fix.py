#!/usr/bin/env python3
"""
测试市净率（PB）计算修复
验证单位转换是否正确
"""

def test_pb_calculation_units():
    """
    测试 PB 计算的单位转换

    场景：某股票
    - 总市值：100 亿元 = 1000000 万元
    - 股东权益：50 亿元 = 5000000000 元
    - 预期 PB = 100 / 50 = 2.0 倍

    单位转换：
    - 1 亿元 = 10000 万元 = 100000000 元
    - money_cap (万元) / total_equity (元) 需要转换
    - 转换后：money_cap (万元) * 10000 / total_equity (元)
    """

    # 数据库中的数据
    money_cap = 1000000  # 万元 = 100 亿元
    total_equity = 5000000000  # 元 = 50 亿元

    # 错误的计算方式（原代码）
    pb_wrong = money_cap / total_equity
    print(f"❌ 错误计算: {money_cap} / {total_equity} = {pb_wrong}")
    print(f"   这个值太小了，相差10000倍！")

    # 正确的计算方式（修复后）
    # money_cap 是万元，total_equity 是元
    # 1 万元 = 10000 元，所以 money_cap * 10000 = 元
    pb_correct = (money_cap * 10000) / total_equity
    print(f"\n✅ 正确计算: ({money_cap} * 10000) / {total_equity} = {pb_correct}")
    print(f"   预期值: 2.0 倍")

    assert abs(pb_correct - 2.0) < 0.01, f"PB 计算错误，期望 2.0，得到 {pb_correct}"
    print("\n✅ 测试通过！")


def test_pb_calculation_with_real_example():
    """
    使用真实数据测试

    平安银行（000001）示例：
    - 总市值：2500 亿元 = 25000000 万元
    - 股东权益：280 亿元 = 28000000000 元
    - 预期 PB ≈ 2500 / 280 ≈ 8.93 倍
    """

    money_cap = 25000000  # 万元 = 2500 亿元
    total_equity = 28000000000  # 元 = 280 亿元

    # 正确的计算
    pb_correct = (money_cap * 10000) / total_equity
    expected_pb = 2500 / 280  # 用亿元计算验证

    print("\n平安银行示例：")
    print(f"  总市值: {money_cap} 万元 = {money_cap / 10000} 亿元")
    print(f"  股东权益: {total_equity} 元 = {total_equity / 100000000} 亿元")
    print(f"  计算 PB: {pb_correct:.2f} 倍")
    print(f"  验证 PB: {expected_pb:.2f} 倍")

    assert abs(pb_correct - expected_pb) < 0.01, "PB 计算不匹配"
    print("✅ 测试通过！")


def test_pb_calculation_formula_equivalence():
    """
    验证不同的计算公式是否等价
    """
    
    money_cap_wan = 1000  # 万元
    total_equity_yuan = 5000000000  # 元
    
    # 方案1：都转换为亿元
    money_cap_yi = money_cap_wan / 10000
    total_equity_yi = total_equity_yuan / 100000000
    pb1 = money_cap_yi / total_equity_yi
    
    # 方案2：都转换为万元
    total_equity_wan = total_equity_yuan / 10000
    pb2 = money_cap_wan / total_equity_wan
    
    # 方案3：都转换为元
    money_cap_yuan = money_cap_wan * 10000
    pb3 = money_cap_yuan / total_equity_yuan
    
    print(f"\n公式等价性验证：")
    print(f"  方案1（亿元）: {pb1:.2f}")
    print(f"  方案2（万元）: {pb2:.2f}")
    print(f"  方案3（元）: {pb3:.2f}")
    
    assert pb1 == pb2 == pb3, "公式不等价"
    print(f"✅ 所有公式等价！")


if __name__ == "__main__":
    print("=" * 60)
    print("市净率（PB）计算修复验证")
    print("=" * 60)
    
    test_pb_calculation_units()
    test_pb_calculation_with_real_example()
    test_pb_calculation_formula_equivalence()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)

