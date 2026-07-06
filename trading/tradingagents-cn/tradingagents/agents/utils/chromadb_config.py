"""
ChromaDB 统一配置模块
支持 Windows 10/11 和其他操作系统的自动适配
"""
import os
import platform
import chromadb
from chromadb.config import Settings


def is_windows_11() -> bool:
    """
    检测是否为 Windows 11
    
    Returns:
        bool: 如果是 Windows 11 返回 True，否则返回 False
    """
    if platform.system() != "Windows":
        return False
    
    # Windows 11 的版本号通常是 10.0.22000 或更高
    version = platform.version()
    try:
        # 提取版本号，格式通常是 "10.0.26100"
        version_parts = version.split('.')
        if len(version_parts) >= 3:
            build_number = int(version_parts[2])
            # Windows 11 的构建号从 22000 开始
            return build_number >= 22000
    except (ValueError, IndexError):
        pass
    
    return False


def get_win10_chromadb_client():
    """
    获取 Windows 10 兼容的 ChromaDB 客户端
    
    Returns:
        chromadb.Client: ChromaDB 客户端实例
    """
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,
        is_persistent=False,
        # Windows 10 特定配置
        chroma_db_impl="duckdb+parquet",
        chroma_api_impl="chromadb.api.segment.SegmentAPI",
        # 使用临时目录避免权限问题
        persist_directory=None
    )
    
    try:
        client = chromadb.Client(settings)
        return client
    except Exception as e:
        # 降级到最基本配置
        basic_settings = Settings(
            allow_reset=True,
            is_persistent=False
        )
        return chromadb.Client(basic_settings)


def get_win11_chromadb_client():
    """
    获取 Windows 11 优化的 ChromaDB 客户端
    
    Returns:
        chromadb.Client: ChromaDB 客户端实例
    """
    # Windows 11 对 ChromaDB 支持更好，可以使用更现代的配置
    settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False,  # 禁用遥测避免 posthog 错误
        is_persistent=False,
        # Windows 11 可以使用默认实现，性能更好
        chroma_db_impl="duckdb+parquet",
        chroma_api_impl="chromadb.api.segment.SegmentAPI"
        # 移除 persist_directory=None，让它使用默认值
    )
    
    try:
        client = chromadb.Client(settings)
        return client
    except Exception as e:
        # 如果还有问题，使用最简配置
        minimal_settings = Settings(
            allow_reset=True,
            anonymized_telemetry=False,  # 关键：禁用遥测
            is_persistent=False
        )
        return chromadb.Client(minimal_settings)


def get_optimal_chromadb_client():
    """
    根据操作系统自动选择最优 ChromaDB 配置
    
    Returns:
        chromadb.Client: ChromaDB 客户端实例
    """
    system = platform.system()
    
    if system == "Windows":
        # 使用更准确的 Windows 11 检测
        if is_windows_11():
            # Windows 11 或更新版本
            return get_win11_chromadb_client()
        else:
            # Windows 10 或更老版本，使用兼容配置
            return get_win10_chromadb_client()
    else:
        # 非 Windows 系统，使用标准配置
        settings = Settings(
            allow_reset=True,
            anonymized_telemetry=False,
            is_persistent=False
        )
        return chromadb.Client(settings)


# 导出配置
__all__ = [
    'get_optimal_chromadb_client',
    'get_win10_chromadb_client',
    'get_win11_chromadb_client',
    'is_windows_11'
]

