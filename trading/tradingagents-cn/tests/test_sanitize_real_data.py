"""
测试真实导出数据的脱敏功能
"""
import json
from app.services.database.backups import _sanitize_document


def test_sanitize_real_export_file():
    """测试对真实导出文件的脱敏"""
    # 读取真实导出文件
    with open("install/database_export_config_2025-10-25.json", "r", encoding="utf-8") as f:
        export_data = json.load(f)
    
    # 对 data 部分进行脱敏
    sanitized_data = _sanitize_document(export_data["data"])
    
    # 验证 system_configs 中的 api_key 被清空
    for config in sanitized_data.get("system_configs", []):
        for llm_config in config.get("llm_configs", []):
            assert llm_config.get("api_key") == "", f"api_key 应该被清空，但实际值为: {llm_config.get('api_key')}"
        
        # 验证 system_settings 中的敏感字段被清空
        system_settings = config.get("system_settings", {})
        for key in ["finnhub_api_key", "tushare_token", "reddit_client_secret"]:
            if key in system_settings:
                assert system_settings[key] == "", f"{key} 应该被清空，但实际值为: {system_settings[key]}"
    
    # 验证 llm_providers 中的 api_key 被清空
    for provider in sanitized_data.get("llm_providers", []):
        assert provider.get("api_key") == "", f"llm_providers 的 api_key 应该被清空，但实际值为: {provider.get('api_key')}"
    
    # 输出统计信息
    print("\n✅ 脱敏测试通过！")
    print(f"- system_configs 数量: {len(sanitized_data.get('system_configs', []))}")
    print(f"- llm_providers 数量: {len(sanitized_data.get('llm_providers', []))}")
    print(f"- users 数量: {len(sanitized_data.get('users', []))}")
    
    # 保存脱敏后的文件用于对比
    sanitized_export = {
        "export_info": export_data["export_info"],
        "data": sanitized_data
    }
    
    with open("install/database_export_config_2025-10-25_SANITIZED.json", "w", encoding="utf-8") as f:
        json.dump(sanitized_export, f, ensure_ascii=False, indent=2)
    
    print("✅ 脱敏后的文件已保存到: install/database_export_config_2025-10-25_SANITIZED.json")


if __name__ == "__main__":
    test_sanitize_real_export_file()

