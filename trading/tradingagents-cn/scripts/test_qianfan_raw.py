#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
千帆API原生测试脚本
直接使用千帆官方SDK测试连通性，不依赖项目集成代码
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_qianfan_with_sdk():
    """使用千帆官方SDK测试"""
    try:
        import qianfan
        
        # 优先使用新的API Key
        api_key = os.getenv('QIANFAN_API_KEY')
        access_key = os.getenv('QIANFAN_ACCESS_KEY')
        secret_key = os.getenv('QIANFAN_SECRET_KEY')
        
        print("==== 千帆SDK测试 ====")
        print(f"API_KEY: {'已设置' if api_key else '未设置'}")
        print(f"ACCESS_KEY: {'已设置' if access_key else '未设置'}")
        print(f"SECRET_KEY: {'已设置' if secret_key else '未设置'}")
        
        if api_key:
            # 使用新的API Key方式
            print("使用新的API Key认证方式")
            os.environ["QIANFAN_API_KEY"] = api_key
        elif access_key and secret_key:
            # 使用旧的AK/SK方式
            print("使用传统的AK/SK认证方式")
            os.environ["QIANFAN_ACCESS_KEY"] = access_key
            os.environ["QIANFAN_SECRET_KEY"] = secret_key
        else:
            print("❌ 请在.env文件中设置QIANFAN_API_KEY或QIANFAN_ACCESS_KEY+QIANFAN_SECRET_KEY")
            return False
        
        # 创建聊天完成客户端
        chat_comp = qianfan.ChatCompletion(model="ERNIE-Speed-8K")
        
        # 发送测试消息
        print("\n发送测试消息...")
        resp = chat_comp.do(
            messages=[
                {
                    "role": "user",
                    "content": "你好，请简单介绍一下你自己"
                }
            ],
            temperature=0.1
        )
        
        print("✅ 千帆API调用成功！")
        print(f"响应: {resp.get('result', '无响应内容')}")
        return True
        
    except ImportError:
        print("❌ 千帆SDK未安装，请运行: pip install qianfan")
        return False
    except Exception as e:
        print(f"❌ 千帆SDK调用失败: {e}")
        return False

def test_qianfan_with_requests():
    """使用requests直接调用千帆API"""
    try:
        import requests
        import json
        
        api_key = os.getenv('QIANFAN_API_KEY')
        access_key = os.getenv('QIANFAN_ACCESS_KEY')
        secret_key = os.getenv('QIANFAN_SECRET_KEY')
        
        print("\n==== 千帆HTTP API测试 ====")
        
        # 方法1: 尝试v2 API (OpenAI兼容)
        print("\n测试千帆v2 API (OpenAI兼容)...")
        
        # 构造Bearer token
        if api_key:
            print("使用新的API Key认证")
            bearer_token = api_key
        elif access_key and secret_key:
            print("使用传统的AK/SK认证")
            bearer_token = f"bce-v3/{access_key}/{secret_key}"
        else:
            print("❌ 请在.env文件中设置QIANFAN_API_KEY或QIANFAN_ACCESS_KEY+QIANFAN_SECRET_KEY")
            return False
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }
        
        data = {
            "model": "ernie-3.5-8k",
            "messages": [
                {
                    "role": "user",
                    "content": "你好，请简单介绍一下你自己"
                }
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                "https://qianfan.baidubce.com/v2/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 千帆v2 API调用成功！")
                print(f"响应: {result.get('choices', [{}])[0].get('message', {}).get('content', '无响应内容')}")
                return True
            else:
                print(f"❌ 千帆v2 API调用失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 千帆v2 API请求异常: {e}")
            
        # 方法2: 尝试传统API (需要获取access_token)
        if not api_key and access_key and secret_key:
            print("\n测试千帆传统API...")
            
            # 获取access_token
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_params = {
                "grant_type": "client_credentials",
                "client_id": access_key,
                "client_secret": secret_key
            }
            
            try:
                token_response = requests.post(token_url, params=token_params, timeout=30)
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    access_token = token_data.get("access_token")
                    
                    if access_token:
                        print("✅ 获取access_token成功")
                        
                        # 调用聊天API
                        chat_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-8k?access_token={access_token}"
                        
                        chat_data = {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "你好，请简单介绍一下你自己"
                                }
                            ],
                            "temperature": 0.1
                        }
                        
                        chat_response = requests.post(
                            chat_url,
                            headers={"Content-Type": "application/json"},
                            json=chat_data,
                            timeout=30
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            print("✅ 千帆传统API调用成功！")
                            print(f"响应: {chat_result.get('result', '无响应内容')}")
                            return True
                        else:
                            print(f"❌ 千帆传统API调用失败: {chat_response.status_code}")
                            print(f"错误信息: {chat_response.text}")
                    else:
                        print("❌ 未能获取access_token")
                        print(f"响应: {token_data}")
                else:
                    print(f"❌ 获取access_token失败: {token_response.status_code}")
                    print(f"错误信息: {token_response.text}")
                    
            except Exception as e:
                print(f"❌ 千帆传统API请求异常: {e}")
        else:
            print("\n跳过传统API测试（使用新API Key或缺少AK/SK）")
            
        return False
        
    except ImportError:
        print("❌ requests库未安装")
        return False
    except Exception as e:
        print(f"❌ HTTP请求测试失败: {e}")
        return False

def main():
    """主函数"""
    print("千帆API原生连通性测试")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv('QIANFAN_API_KEY')
    access_key = os.getenv('QIANFAN_ACCESS_KEY')
    secret_key = os.getenv('QIANFAN_SECRET_KEY')
    
    if not api_key and (not access_key or not secret_key):
        print("❌ 请确保在.env文件中设置了以下环境变量之一:")
        print("   方式1 (推荐): QIANFAN_API_KEY=your_api_key")
        print("   方式2 (传统): QIANFAN_ACCESS_KEY=your_access_key + QIANFAN_SECRET_KEY=your_secret_key")
        return
    
    # 测试方法1: 使用千帆官方SDK
    sdk_success = test_qianfan_with_sdk()
    
    # 测试方法2: 使用HTTP请求
    http_success = test_qianfan_with_requests()
    
    print("\n=== 测试结果汇总 ===")
    print(f"千帆SDK测试: {'✅ 成功' if sdk_success else '❌ 失败'}")
    print(f"HTTP API测试: {'✅ 成功' if http_success else '❌ 失败'}")
    
    if sdk_success or http_success:
        print("\n🎉 千帆API连通性正常！")
    else:
        print("\n❌ 千帆API连通性测试失败，请检查密钥配置")

if __name__ == "__main__":
    main()