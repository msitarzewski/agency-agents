"""
测试字符串切片
"""

base_url = "https://generativelanguage.googleapis.com/v1beta"

print(f"原始字符串: {base_url}")
print(f"字符串长度: {len(base_url)}")
print()

print(f"/v1beta 的长度: {len('/v1beta')}")
print()

print(f"base_url[:-7] = {base_url[:-7]}")
print(f"base_url[:-8] = {base_url[:-8]}")
print()

# 正确的方法
suffix = "/v1beta"
if base_url.endswith(suffix):
    result = base_url[:-len(suffix)]
    print(f"使用 [:-len(suffix)] = {result}")

