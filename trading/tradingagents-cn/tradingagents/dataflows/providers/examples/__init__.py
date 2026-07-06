"""
示例数据提供器

展示如何创建新的数据源提供器
"""

from .example_sdk import ExampleSDKProvider

__all__ = [
    'ExampleSDKProvider',
]


def get_example_sdk_provider(**kwargs):
    """获取示例SDK提供器实例"""
    return ExampleSDKProvider(**kwargs)

