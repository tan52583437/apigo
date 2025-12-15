# 使用PowerShell正确查看API响应
$response = Invoke-RestMethod "http://localhost:5000/api/v1/mobile-segments/query?mobile=18523266910"

Write-Host "=== 原始响应内容 ==="
# 使用ConvertTo-Json确保正确显示中文
$response | ConvertTo-Json -Depth 10

Write-Host "\n=== 解析后的内容 ==="
Write-Host "手机号: $($response.data.mobile)"
Write-Host "归属地: $($response.data.city)"
Write-Host "运营商: $($response.data.operator)"
Write-Host "前三位号段: $($response.data.three_segment)"
Write-Host "前七位号段: $($response.data.seven_segment)"