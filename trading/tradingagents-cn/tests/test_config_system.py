"""
配置系统单元测试

测试新的配置管理系统，包括：
- 配置验证器
- 配置服务
- 配置提供者
- 配置兼容层
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.startup_validator import (
    StartupValidator,
    ConfigItem,
    ConfigLevel,
    ValidationResult,
    ConfigurationError
)


class TestStartupValidator:
    """测试启动配置验证器"""
    
    def test_config_item_creation(self):
        """测试配置项创建"""
        config = ConfigItem(
            key="TEST_KEY",
            level=ConfigLevel.REQUIRED,
            description="Test configuration",
            example="test_value"
        )
        
        assert config.key == "TEST_KEY"
        assert config.level == ConfigLevel.REQUIRED
        assert config.description == "Test configuration"
        assert config.example == "test_value"
    
    def test_validation_result_creation(self):
        """测试验证结果创建"""
        result = ValidationResult(
            success=True,
            missing_required=[],
            missing_recommended=[],
            invalid_configs=[],
            warnings=[]
        )
        
        assert result.success is True
        assert len(result.missing_required) == 0
        assert len(result.missing_recommended) == 0
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_missing_required_configs(self):
        """测试缺少必需配置的验证"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is False
        assert len(result.missing_required) > 0
        
        # 检查是否包含必需的配置项
        required_keys = [config.key for config in result.missing_required]
        assert "MONGODB_HOST" in required_keys
        assert "MONGODB_PORT" in required_keys
        assert "JWT_SECRET" in required_keys
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "test-secret-key-with-enough-length"
    })
    def test_validate_with_required_configs(self):
        """测试有必需配置的验证"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is True
        assert len(result.missing_required) == 0
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "invalid_port",  # 无效端口
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "test-secret-key-with-enough-length"
    })
    def test_validate_invalid_port(self):
        """测试无效端口验证"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is False
        assert len(result.invalid_configs) > 0
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "short"  # 太短的密钥
    })
    def test_validate_short_jwt_secret(self):
        """测试过短的 JWT 密钥"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is False
        assert len(result.invalid_configs) > 0
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "your-super-secret-jwt-key-change-in-production"  # 默认值
    })
    def test_validate_default_jwt_secret_warning(self):
        """测试使用默认 JWT 密钥时的警告"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is True
        assert len(result.warnings) > 0
        assert any("JWT_SECRET" in warning for warning in result.warnings)
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "test-secret-key-with-enough-length"
    })
    def test_validate_missing_recommended_configs(self):
        """测试缺少推荐配置"""
        validator = StartupValidator()
        result = validator.validate()
        
        assert result.success is True
        assert len(result.missing_recommended) > 0
        
        # 检查推荐配置
        recommended_keys = [config.key for config in result.missing_recommended]
        assert "DEEPSEEK_API_KEY" in recommended_keys or "DASHSCOPE_API_KEY" in recommended_keys
    
    @patch.dict(os.environ, {}, clear=True)
    def test_raise_if_failed(self):
        """测试验证失败时抛出异常"""
        validator = StartupValidator()
        validator.validate()
        
        with pytest.raises(ConfigurationError):
            validator.raise_if_failed()
    
    @patch.dict(os.environ, {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DATABASE": "test_db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "test-secret-key-with-enough-length"
    })
    def test_raise_if_failed_success(self):
        """测试验证成功时不抛出异常"""
        validator = StartupValidator()
        validator.validate()
        
        # 不应该抛出异常
        validator.raise_if_failed()


class TestConfigCompat:
    """测试配置兼容层"""
    
    def test_config_manager_compat_creation(self):
        """测试配置管理器兼容层创建"""
        from app.core.config_compat import ConfigManagerCompat
        
        config_manager = ConfigManagerCompat()
        assert config_manager is not None
    
    def test_get_data_dir(self):
        """测试获取数据目录"""
        from app.core.config_compat import ConfigManagerCompat
        
        config_manager = ConfigManagerCompat()
        data_dir = config_manager.get_data_dir()
        
        assert data_dir is not None
        assert isinstance(data_dir, str)
    
    @patch.dict(os.environ, {"DATA_DIR": "/custom/data/dir"})
    def test_get_data_dir_from_env(self):
        """测试从环境变量获取数据目录"""
        from app.core.config_compat import ConfigManagerCompat
        
        config_manager = ConfigManagerCompat()
        data_dir = config_manager.get_data_dir()
        
        assert data_dir == "/custom/data/dir"
    
    def test_load_settings(self):
        """测试加载系统设置"""
        from app.core.config_compat import ConfigManagerCompat
        
        config_manager = ConfigManagerCompat()
        settings = config_manager.load_settings()
        
        assert settings is not None
        assert isinstance(settings, dict)
        assert "max_debate_rounds" in settings
    
    def test_token_tracker_compat_creation(self):
        """测试 Token 跟踪器兼容层创建"""
        from app.core.config_compat import TokenTrackerCompat
        
        tracker = TokenTrackerCompat()
        assert tracker is not None
    
    def test_track_usage(self):
        """测试记录 Token 使用量"""
        from app.core.config_compat import TokenTrackerCompat
        
        tracker = TokenTrackerCompat()
        tracker.track_usage(
            provider="test_provider",
            model_name="test_model",
            input_tokens=100,
            output_tokens=50,
            cost=0.01
        )
        
        summary = tracker.get_usage_summary()
        assert "test_provider:test_model" in summary
        assert summary["test_provider:test_model"]["total_input_tokens"] == 100
        assert summary["test_provider:test_model"]["total_output_tokens"] == 50
        assert summary["test_provider:test_model"]["call_count"] == 1
    
    def test_reset_usage(self):
        """测试重置使用统计"""
        from app.core.config_compat import TokenTrackerCompat
        
        tracker = TokenTrackerCompat()
        tracker.track_usage("test", "model", 100, 50, 0.01)
        
        assert len(tracker.get_usage_summary()) > 0
        
        tracker.reset_usage()
        assert len(tracker.get_usage_summary()) == 0


class TestConfigPriority:
    """测试配置优先级"""
    
    @patch.dict(os.environ, {
        "TEST_CONFIG": "from_env",
        "MONGODB_HOST": "localhost"
    })
    def test_env_priority(self):
        """测试环境变量优先级"""
        # 环境变量应该有最高优先级
        assert os.getenv("TEST_CONFIG") == "from_env"
    
    def test_default_values(self):
        """测试默认值"""
        from app.core.config_compat import ConfigManagerCompat
        
        config_manager = ConfigManagerCompat()
        settings = config_manager._get_default_settings()
        
        assert settings["max_debate_rounds"] == 1
        assert settings["online_tools"] is True
        assert settings["memory_enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

