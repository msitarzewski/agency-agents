"""
OpenAI兼容适配器基类
为所有支持OpenAI接口的LLM提供商提供统一的基础实现
"""

import os
import time
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import CallbackManagerForLLMRun

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_llm_logging

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger, get_logger_manager
logger = get_logger('agents')
logger = setup_llm_logging()

# 导入token跟踪器
try:
    from tradingagents.config.config_manager import token_tracker
    TOKEN_TRACKING_ENABLED = True
    logger.info("✅ Token跟踪功能已启用")
except ImportError:
    TOKEN_TRACKING_ENABLED = False
    logger.warning("⚠️ Token跟踪功能未启用")


class OpenAICompatibleBase(ChatOpenAI):
    """
    OpenAI兼容适配器基类
    为所有支持OpenAI接口的LLM提供商提供统一实现
    """
    
    def __init__(
        self,
        provider_name: str,
        model: str,
        api_key_env_var: str,
        base_url: str,
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        初始化OpenAI兼容适配器
        
        Args:
            provider_name: 提供商名称 (如: "deepseek", "dashscope")
            model: 模型名称
            api_key_env_var: API密钥环境变量名
            base_url: API基础URL
            api_key: API密钥，如果不提供则从环境变量获取
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        """
        
        # 🔍 [DEBUG] 读取环境变量前的日志
        logger.info(f"🔍 [{provider_name}初始化] 开始初始化 OpenAI 兼容适配器")
        logger.info(f"🔍 [{provider_name}初始化] 模型: {model}")
        logger.info(f"🔍 [{provider_name}初始化] API Key 环境变量名: {api_key_env_var}")
        logger.info(f"🔍 [{provider_name}初始化] 是否传入 api_key 参数: {api_key is not None}")

        # 在父类初始化前先缓存元信息到私有属性（避免Pydantic字段限制）
        object.__setattr__(self, "_provider_name", provider_name)
        object.__setattr__(self, "_model_name_alias", model)

        # 获取API密钥
        if api_key is None:
            # 导入 API Key 验证工具
            try:
                from app.utils.api_key_utils import is_valid_api_key
            except ImportError:
                def is_valid_api_key(key):
                    if not key or len(key) <= 10:
                        return False
                    if key.startswith('your_') or key.startswith('your-'):
                        return False
                    if key.endswith('_here') or key.endswith('-here'):
                        return False
                    if '...' in key:
                        return False
                    return True

            # 从环境变量读取 API Key
            env_api_key = os.getenv(api_key_env_var)
            logger.info(f"🔍 [{provider_name}初始化] 从环境变量读取 {api_key_env_var}: {'有值' if env_api_key else '空'}")

            # 验证环境变量中的 API Key 是否有效（排除占位符）
            if env_api_key and is_valid_api_key(env_api_key):
                logger.info(f"✅ [{provider_name}初始化] 环境变量中的 API Key 有效，长度: {len(env_api_key)}, 前10位: {env_api_key[:10]}...")
                api_key = env_api_key
            elif env_api_key:
                logger.warning(f"⚠️ [{provider_name}初始化] 环境变量中的 API Key 无效（可能是占位符），将被忽略")
                api_key = None
            else:
                logger.warning(f"⚠️ [{provider_name}初始化] {api_key_env_var} 环境变量为空")
                api_key = None

            if not api_key:
                logger.error(f"❌ [{provider_name}初始化] API Key 检查失败，即将抛出异常")
                raise ValueError(
                    f"{provider_name} API密钥未找到。"
                    f"请在 Web 界面配置 API Key (设置 -> 大模型厂家) 或设置 {api_key_env_var} 环境变量。"
                )
        else:
            logger.info(f"✅ [{provider_name}初始化] 使用传入的 API Key（来自数据库配置），长度: {len(api_key)}")
        
        # 设置OpenAI兼容参数
        # 注意：model参数会被Pydantic映射到model_name字段
        openai_kwargs = {
            "model": model,  # 这会被映射到model_name字段
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # 根据LangChain版本使用不同的参数名
        try:
            # 新版本LangChain
            openai_kwargs.update({
                "api_key": api_key,
                "base_url": base_url
            })
        except:
            # 旧版本LangChain
            openai_kwargs.update({
                "openai_api_key": api_key,
                "openai_api_base": base_url
            })
        
        # 初始化父类
        super().__init__(**openai_kwargs)

        # 再次确保元信息存在（有些实现会在super()中重置__dict__）
        object.__setattr__(self, "_provider_name", provider_name)
        object.__setattr__(self, "_model_name_alias", model)

        logger.info(f"✅ {provider_name} OpenAI兼容适配器初始化成功")
        logger.info(f"   模型: {model}")
        logger.info(f"   API Base: {base_url}")

    @property
    def provider_name(self) -> Optional[str]:
        return getattr(self, "_provider_name", None)

    # 移除model_name property定义，使用Pydantic字段
    # model_name字段由ChatOpenAI基类的Pydantic字段提供
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成聊天响应，并记录token使用量
        """
        
        # 记录开始时间
        start_time = time.time()
        
        # 调用父类生成方法
        result = super()._generate(messages, stop, run_manager, **kwargs)
        
        # 记录token使用
        self._track_token_usage(result, kwargs, start_time)
        
        return result

    def _track_token_usage(self, result: ChatResult, kwargs: Dict, start_time: float):
        """记录token使用量并输出日志"""
        if not TOKEN_TRACKING_ENABLED:
            return
        try:
            # 统计token信息
            usage = getattr(result, "usage_metadata", None)
            total_tokens = usage.get("total_tokens") if usage else None
            prompt_tokens = usage.get("input_tokens") if usage else None
            completion_tokens = usage.get("output_tokens") if usage else None

            elapsed = time.time() - start_time
            logger.info(
                f"📊 Token使用 - Provider: {getattr(self, 'provider_name', 'unknown')}, Model: {getattr(self, 'model_name', 'unknown')}, "
                f"总tokens: {total_tokens}, 提示: {prompt_tokens}, 补全: {completion_tokens}, 用时: {elapsed:.2f}s"
            )
        except Exception as e:
            logger.warning(f"⚠️ Token跟踪记录失败: {e}")


class ChatDeepSeekOpenAI(OpenAICompatibleBase):
    """DeepSeek OpenAI兼容适配器"""
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            provider_name="deepseek",
            model=model,
            api_key_env_var="DEEPSEEK_API_KEY",
            base_url="https://api.deepseek.com",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


class ChatDashScopeOpenAIUnified(OpenAICompatibleBase):
    """阿里百炼 DashScope OpenAI兼容适配器"""
    
    def __init__(
        self,
        model: str = "qwen-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            provider_name="dashscope",
            model=model,
            api_key_env_var="DASHSCOPE_API_KEY",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


class ChatQianfanOpenAI(OpenAICompatibleBase):
    """文心一言千帆平台 OpenAI兼容适配器"""
    
    def __init__(
        self,
        model: str = "ernie-3.5-8k",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        # 千帆新一代API使用单一API Key认证
        # 格式: bce-v3/ALTAK-xxx/xxx

        # 如果没有传入 API Key，尝试从环境变量读取
        if not api_key:
            # 导入 API Key 验证工具
            try:
                from app.utils.api_key_utils import is_valid_api_key
            except ImportError:
                def is_valid_api_key(key):
                    if not key or len(key) <= 10:
                        return False
                    if key.startswith('your_') or key.startswith('your-'):
                        return False
                    if key.endswith('_here') or key.endswith('-here'):
                        return False
                    if '...' in key:
                        return False
                    return True

            env_api_key = os.getenv('QIANFAN_API_KEY')
            if env_api_key and is_valid_api_key(env_api_key):
                qianfan_api_key = env_api_key
            else:
                qianfan_api_key = None
        else:
            qianfan_api_key = api_key

        if not qianfan_api_key:
            raise ValueError(
                "千帆模型需要配置 API Key。"
                "请在 Web 界面配置 (设置 -> 大模型厂家) 或设置 QIANFAN_API_KEY 环境变量，"
                "格式为: bce-v3/ALTAK-xxx/xxx"
            )

        if not qianfan_api_key.startswith('bce-v3/'):
            raise ValueError(
                "QIANFAN_API_KEY格式错误，应为: bce-v3/ALTAK-xxx/xxx"
            )
        
        super().__init__(
            provider_name="qianfan",
            model=model,
            api_key_env_var="QIANFAN_API_KEY",
            base_url="https://qianfan.baidubce.com/v2",
            api_key=qianfan_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（千帆模型专用）"""
        # 千帆模型的token估算：中文约1.5字符/token，英文约4字符/token
        # 保守估算：2字符/token
        return max(1, len(text) // 2)
    
    def _truncate_messages(self, messages: List[BaseMessage], max_tokens: int = 4500) -> List[BaseMessage]:
        """截断消息以适应千帆模型的token限制"""
        # 为千帆模型预留一些token空间，使用4500而不是5120
        truncated_messages = []
        total_tokens = 0
        
        # 从最后一条消息开始，向前保留消息
        for message in reversed(messages):
            content = str(message.content) if hasattr(message, 'content') else str(message)
            message_tokens = self._estimate_tokens(content)
            
            if total_tokens + message_tokens <= max_tokens:
                truncated_messages.insert(0, message)
                total_tokens += message_tokens
            else:
                # 如果是第一条消息且超长，进行内容截断
                if not truncated_messages:
                    remaining_tokens = max_tokens - 100  # 预留100个token
                    max_chars = remaining_tokens * 2  # 2字符/token
                    truncated_content = content[:max_chars] + "...(内容已截断)"
                    
                    # 创建截断后的消息
                    if hasattr(message, 'content'):
                        message.content = truncated_content
                    truncated_messages.insert(0, message)
                break
        
        if len(truncated_messages) < len(messages):
            logger.warning(f"⚠️ 千帆模型输入过长，已截断 {len(messages) - len(truncated_messages)} 条消息")
        
        return truncated_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """生成聊天响应，包含千帆模型的token截断逻辑"""
        
        # 对千帆模型进行输入token截断
        truncated_messages = self._truncate_messages(messages)
        
        # 调用父类的_generate方法
        return super()._generate(truncated_messages, stop, run_manager, **kwargs)


class ChatZhipuOpenAI(OpenAICompatibleBase):
    """智谱AI GLM OpenAI兼容适配器"""
    
    def __init__(
        self,
        model: str = "glm-4.6",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        if base_url is None:
            env_base_url = os.getenv("ZHIPU_BASE_URL")
            # 只使用有效的环境变量值（不是占位符）
            if env_base_url and not env_base_url.startswith('your_') and not env_base_url.startswith('your-'):
                base_url = env_base_url
            else:
                base_url = "https://open.bigmodel.cn/api/paas/v4"
                
        super().__init__(
            provider_name="zhipu",
            model=model,
            api_key_env_var="ZHIPU_API_KEY",
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（GLM模型专用）"""
        # GLM模型的token估算：中文约1.5字符/token，英文约4字符/token
        # 保守估算：2字符/token
        return max(1, len(text) // 2)


class ChatCustomOpenAI(OpenAICompatibleBase):
    """自定义OpenAI端点适配器（代理/聚合平台）"""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        # 如果没有传入 base_url，尝试从环境变量读取
        if base_url is None:
            env_base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
            # 只使用有效的环境变量值（不是占位符）
            if env_base_url and not env_base_url.startswith('your_') and not env_base_url.startswith('your-'):
                base_url = env_base_url
            else:
                base_url = "https://api.openai.com/v1"

        super().__init__(
            provider_name="custom_openai",
            model=model,
            api_key_env_var="CUSTOM_OPENAI_API_KEY",
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


# 支持的OpenAI兼容模型配置
OPENAI_COMPATIBLE_PROVIDERS = {
    "deepseek": {
        "adapter_class": ChatDeepSeekOpenAI,
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "models": {
            "deepseek-chat": {"context_length": 32768, "supports_function_calling": True},
            "deepseek-coder": {"context_length": 16384, "supports_function_calling": True}
        }
    },
    "dashscope": {
        "adapter_class": ChatDashScopeOpenAIUnified,
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "models": {
            "qwen-turbo": {"context_length": 8192, "supports_function_calling": True},
            "qwen-plus": {"context_length": 32768, "supports_function_calling": True},
            "qwen-plus-latest": {"context_length": 32768, "supports_function_calling": True},
            "qwen-max": {"context_length": 32768, "supports_function_calling": True},
            "qwen-max-latest": {"context_length": 32768, "supports_function_calling": True}
        }
    },
    "qianfan": {
        "adapter_class": ChatQianfanOpenAI,
        "base_url": "https://qianfan.baidubce.com/v2",
        "api_key_env": "QIANFAN_API_KEY",
        "models": {
            "ernie-3.5-8k": {"context_length": 5120, "supports_function_calling": True},
            "ernie-4.0-turbo-8k": {"context_length": 5120, "supports_function_calling": True},
            "ERNIE-Speed-8K": {"context_length": 5120, "supports_function_calling": True},
            "ERNIE-Lite-8K": {"context_length": 5120, "supports_function_calling": True}
        }
    },
    "zhipu": {
        "adapter_class": ChatZhipuOpenAI,
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key_env": "ZHIPU_API_KEY",
        "models": {
            "glm-4.6": {"context_length": 200000, "supports_function_calling": True},
            "glm-4": {"context_length": 128000, "supports_function_calling": True},
            "glm-4-plus": {"context_length": 128000, "supports_function_calling": True},
            "glm-3-turbo": {"context_length": 128000, "supports_function_calling": True}
        }
    },
    "custom_openai": {
        "adapter_class": ChatCustomOpenAI,
        "base_url": None,  # 将由用户配置
        "api_key_env": "CUSTOM_OPENAI_API_KEY",
        "models": {
            "gpt-3.5-turbo": {"context_length": 16384, "supports_function_calling": True},
            "gpt-4": {"context_length": 8192, "supports_function_calling": True},
            "gpt-4-turbo": {"context_length": 128000, "supports_function_calling": True},
            "gpt-4o": {"context_length": 128000, "supports_function_calling": True},
            "gpt-4o-mini": {"context_length": 128000, "supports_function_calling": True},
            "claude-3-haiku": {"context_length": 200000, "supports_function_calling": True},
            "claude-3-sonnet": {"context_length": 200000, "supports_function_calling": True},
            "claude-3-opus": {"context_length": 200000, "supports_function_calling": True},
            "claude-3.5-sonnet": {"context_length": 200000, "supports_function_calling": True},
            "gemini-pro": {"context_length": 32768, "supports_function_calling": True},
            "gemini-1.5-pro": {"context_length": 1000000, "supports_function_calling": True},
            "llama-3.1-8b": {"context_length": 128000, "supports_function_calling": True},
            "llama-3.1-70b": {"context_length": 128000, "supports_function_calling": True},
            "llama-3.1-405b": {"context_length": 128000, "supports_function_calling": True},
            "custom-model": {"context_length": 32768, "supports_function_calling": True}
        }
    }
}


def create_openai_compatible_llm(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> OpenAICompatibleBase:
    """创建OpenAI兼容LLM实例的统一工厂函数"""
    provider_info = OPENAI_COMPATIBLE_PROVIDERS.get(provider)
    if not provider_info:
        raise ValueError(f"不支持的OpenAI兼容提供商: {provider}")

    adapter_class = provider_info["adapter_class"]

    # 如果调用未提供 base_url，则采用 provider 的默认值（可能为 None）
    if base_url is None:
        base_url = provider_info.get("base_url")

    # 仅当 provider 未内置 base_url（如 custom_openai）时，才将 base_url 传递给适配器，
    # 避免与适配器内部的 super().__init__(..., base_url=...) 冲突导致 "multiple values" 错误。
    init_kwargs = dict(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    if provider_info.get("base_url") is None and base_url:
        init_kwargs["base_url"] = base_url

    return adapter_class(**init_kwargs)


def test_openai_compatible_adapters():
    """快速测试所有适配器是否能被正确实例化（不发起真实请求）"""
    for provider, info in OPENAI_COMPATIBLE_PROVIDERS.items():
        cls = info["adapter_class"]
        try:
            if provider == "custom_openai":
                cls(model="gpt-3.5-turbo", api_key="test", base_url="https://api.openai.com/v1")
            elif provider == "qianfan":
                # 千帆新一代API仅需QIANFAN_API_KEY，格式: bce-v3/ALTAK-xxx/xxx
                cls(model="ernie-3.5-8k", api_key="bce-v3/test-key/test-secret")
            else:
                cls(model=list(info["models"].keys())[0], api_key="test")
            logger.info(f"✅ 适配器实例化成功: {provider}")
        except Exception as e:
            logger.warning(f"⚠️ 适配器实例化失败（预期或可忽略）: {provider} - {e}")


if __name__ == "__main__":
    test_openai_compatible_adapters()
