#!/usr/bin/env python3
"""
TradingAgents 运行时配置适配器（弱依赖）

- 优先尝试从后端 app.services.config_provider 读取动态 system_settings（若可用）
- 若不可用或在异步事件循环中无法同步等待，则回退到环境变量与默认值
- 保持 TradingAgents 包独立性：不可用时静默回退，不引入硬依赖
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Optional, Callable

import logging
_logger = logging.getLogger("tradingagents.config")


def _get_event_loop_running() -> bool:
    """检测是否有事件循环正在运行"""
    try:
        # get_running_loop 在无事件循环时会抛 RuntimeError（更安静，不触发警告）
        loop = asyncio.get_running_loop()
        return loop is not None and loop.is_running()
    except RuntimeError:
        return False
    except Exception:
        # 其他异常也认为没有事件循环
        return False


def _get_system_settings_sync() -> dict:
    """最佳努力获取后端动态 system_settings。
    - 若后端不可用/未安装，返回空 dict
    - 若当前有事件循环在运行，为避免死锁/嵌套，直接返回空 dict

    注意：为了避免事件循环冲突，当前实现总是返回空字典，
    依赖环境变量和默认值进行配置。
    """
    # 临时解决方案：完全禁用动态配置获取，避免事件循环冲突
    # TODO: 未来可以考虑使用线程池或其他方式来安全获取动态配置
    _logger.debug("动态配置获取已禁用，使用环境变量和默认值")
    return {}

    # 以下代码暂时注释，避免事件循环冲突
    # # 第一次检查
    # if _get_event_loop_running():
    #     _logger.debug("事件循环正在运行，跳过动态配置获取")
    #     return {}

    # try:
    #     # 延迟导入，避免硬依赖
    #     from app.services.config_provider import provider as config_provider  # type: ignore

    #     # 第二次检查：确保导入过程中没有启动事件循环
    #     if _get_event_loop_running():
    #         _logger.debug("导入后检测到事件循环，跳过动态配置获取")
    #         return {}

    #     # 第三次检查：在调用asyncio.run之前再次确认
    #     try:
    #         # 尝试获取当前事件循环，如果成功说明有循环在运行
    #         current_loop = asyncio.get_running_loop()
    #         if current_loop and current_loop.is_running():
    #             _logger.debug("asyncio.run调用前检测到运行中的事件循环，跳过")
    #             return {}
    #     except RuntimeError:
    #         # 没有运行中的事件循环，可以安全调用asyncio.run
    #         pass

    #     # 使用 asyncio.run 进行一次性同步调用
    #     return asyncio.run(config_provider.get_effective_system_settings()) or {}

    # except RuntimeError as e:
    #     error_msg = str(e).lower()
    #     if any(keyword in error_msg for keyword in [
    #         "cannot be called from a running event loop",
    #         "got future attached to a different loop",
    #         "task was destroyed but it is pending"
    #     ]):
    #         _logger.debug(f"检测到事件循环冲突，跳过动态配置获取: {e}")
    #         return {}
    #     _logger.debug(f"获取动态配置失败（RuntimeError）: {e}")
    #     return {}
    # except Exception as e:
    #     _logger.debug(f"获取动态配置失败: {e}")
    #     return {}


def _coerce(value: Any, caster: Callable[[Any], Any], default: Any) -> Any:
    try:
        if value is None:
            return default
        return caster(value)
    except Exception:
        return default


def get_number(env_var: str, system_key: Optional[str], default: float | int, caster: Callable[[Any], Any]) -> float | int:
    """按优先级获取数值配置：DB(system_settings) > ENV > default
    - env_var: 环境变量名，例如 "TA_US_MIN_API_INTERVAL_SECONDS"
    - system_key: 动态系统设置键名，例如 "ta_us_min_api_interval_seconds"（可为 None）
    - default: 默认值
    - caster: 类型转换函数，如 float 或 int
    """
    # 1) DB 动态设置
    if system_key:
        eff = _get_system_settings_sync()
        if isinstance(eff, dict) and system_key in eff:
            return _coerce(eff.get(system_key), caster, default)

    # 2) 环境变量
    env_val = os.getenv(env_var)
    if env_val is not None and str(env_val).strip() != "":
        return _coerce(env_val, caster, default)

    # 3) 代码默认
    return default


def get_float(env_var: str, system_key: Optional[str], default: float) -> float:
    return get_number(env_var, system_key, default, float)  # type: ignore[arg-type]


def get_int(env_var: str, system_key: Optional[str], default: int) -> int:
    return get_number(env_var, system_key, default, int)  # type: ignore[arg-type]


# --- Boolean access helper ---------------------------------------------------

def get_bool(env_var: str, system_key: Optional[str], default: bool) -> bool:
    """按优先级获取布尔配置：DB(system_settings) > ENV > default"""
    # 1) DB 动态设置
    if system_key:
        eff = _get_system_settings_sync()
        if isinstance(eff, dict) and system_key in eff:
            v = eff.get(system_key)
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                return str(v).strip().lower() in ("1", "true", "yes", "on")
    # 2) 环境变量
    env_val = os.getenv(env_var)
    if env_val is not None and str(env_val).strip() != "":
        return str(env_val).strip().lower() in ("1", "true", "yes", "on")
    # 3) 代码默认
    return default


def use_app_cache_enabled(default: bool = False) -> bool:
    """是否启用从 app 缓存（Mongo 集合）优先读取。ENV: TA_USE_APP_CACHE; DB: ta_use_app_cache
    会记录一次评估日志，包含来源与原始ENV值，便于排查生效路径。
    """
    # 推断来源（DB/ENV/DEFAULT）
    src = "default"
    env_val = os.getenv("TA_USE_APP_CACHE")
    try:
        eff = _get_system_settings_sync()
    except Exception:
        eff = {}
    if isinstance(eff, dict) and "ta_use_app_cache" in eff:
        src = "db"
    elif env_val is not None and str(env_val).strip() != "":
        src = "env"

    # 最终值（遵循 DB > ENV > DEFAULT）
    val = get_bool("TA_USE_APP_CACHE", "ta_use_app_cache", default)

    try:
        _logger.info(f"[runtime_settings] TA_USE_APP_CACHE evaluated -> {val} (source={src}, env={env_val})")
    except Exception:
        pass
    return val


# --- Timezone access helpers -------------------------------------------------
from typing import Optional as _Optional
from zoneinfo import ZoneInfo as _ZoneInfo


def get_timezone_name(default: str = "Asia/Shanghai") -> str:
    """Return configured timezone name with priority: DB(system_settings) > ENV > default.
    - DB key: app_timezone (preferred) or APP_TIMEZONE
    - ENV vars checked in order: APP_TIMEZONE, TIMEZONE, TA_TIMEZONE
    """
    try:
        eff = _get_system_settings_sync()
        if isinstance(eff, dict):
            tz = eff.get("app_timezone") or eff.get("APP_TIMEZONE")
            if isinstance(tz, str) and tz.strip():
                return tz.strip()
    except Exception:
        pass

    for env_key in ("APP_TIMEZONE", "TIMEZONE", "TA_TIMEZONE"):
        val = os.getenv(env_key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    return default


def get_zoneinfo(default: str = "Asia/Shanghai") -> _ZoneInfo:
    """Convenience: return ZoneInfo for the configured timezone name."""
    name = get_timezone_name(default)
    try:
        return _ZoneInfo(name)
    except Exception:
        # Fallback to UTC if invalid
        return _ZoneInfo("UTC")


__all__ = [
    "get_float",
    "get_int",
    "get_bool",
    "use_app_cache_enabled",
    "get_timezone_name",
    "get_zoneinfo",
]
