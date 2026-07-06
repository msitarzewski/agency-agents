#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据服务器配置功能
"""

import pytest
pytest.importorskip("enhanced_stock_list_fetcher")
pytestmark = pytest.mark.integration

from enhanced_stock_list_fetcher import load_tdx_servers_config, get_mainmarket_ip
import json

def test_server_config():
    """测试服务器配置加载功能"""
    print("=== 测试数据服务器配置功能 ===")

    # 测试加载服务器配置
    print("\n1. 测试加载服务器配置:")
    servers = load_tdx_servers_config()
    print(f"✅ 成功加载 {len(servers)} 个服务器配置")

    # 显示前5个服务器
    print("\n前5个服务器配置:")
    for i, server in enumerate(servers[:5]):
        print(f"  {i+1}. {server.get('name', '未命名')} - {server['ip']}:{server['port']}")

    # 测试获取主市场IP
    print("\n2. 测试获取主市场IP:")
    for i in range(3):
        ip, port = get_mainmarket_ip()
        print(f"  第{i+1}次随机选择: {ip}:{port}")

    # 测试指定IP和端口
    print("\n3. 测试指定IP和端口:")
    ip, port = get_mainmarket_ip('192.168.1.1', 8888)
    print(f"  指定IP和端口: {ip}:{port}")

    # 显示完整的服务器配置信息
    print("\n4. 完整服务器配置信息:")
    print(json.dumps(servers, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_server_config()