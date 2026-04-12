#!/bin/bash
echo "=== 阶段2 API 端点测试 ==="
BASE_URL="http://localhost:8001/api/v1"
# 1. 健康检查
echo "1. 健康检查..."
curl -s "$BASE_URL/../health" | grep -q "ok" && echo "  通过" || echo "  失败"
# 2. 字典材质
echo "2. 字典材质..."
curl -s "$BASE_URL/dicts/materials" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 3. 器型
echo "3. 器型..."
curl -s "$BASE_URL/dicts/types" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 4. 标签
echo "4. 标签..."
curl -s "$BASE_URL/dicts/tags" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 5. 批次
echo "5. 批次..."
curl -s "$BASE_URL/batches" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 6. 货品
echo "6. 货品..."
curl -s "$BASE_URL/items" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 7. 销售
echo "7. 销售..."
curl -s "$BASE_URL/sales" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 8. 贵金属市价
echo "8. 贵金属市价..."
curl -s "$BASE_URL/metal-prices" | grep -q "code.*0" && echo "  通过" || echo "  失败"
# 9. 系统配置
echo "9. 系统配置..."
curl -s "$BASE_URL/dicts/config" | grep -q "code.*0" && echo "  通过" || echo "  失败"
echo "=== 测试完成 ==="
