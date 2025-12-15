import requests

# 测试手机号查询API
url = "http://localhost:5000/api/v1/mobile-segments/query"
params = {"mobile": "18523266910"}

response = requests.get(url, params=params)

print("=== API响应原始内容 ===")
print(response.text)
print("\n=== API响应解析后内容 ===")
result = response.json()
print(f"查询结果：{result['success']}")
print(f"手机号：{result['data']['mobile']}")
print(f"归属地：{result['data']['city']}")
print(f"运营商：{result['data']['operator']}")
print(f"前三位号段：{result['data']['three_segment']}")
print(f"前七位号段：{result['data']['seven_segment']}")