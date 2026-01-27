# -*- coding: utf-8 -*-
"""
修复文档字符串
"""

with open('export_combinations.py', 'r', encoding='gbk', errors='ignore') as f:
    lines = f.readlines()

# 找到并修复所有有问题的文档字符串
fixes = []
for i, line in enumerate(lines):
    if '"""' in line and any(ord(c) > 127 for c in line):
        # 这是一个包含非ASCII字符的文档字符串，需要修复
        fixes.append(i)

print(f"找到 {len(fixes)} 个可能有问题的文档字符串")

# 简单方案：读取整个文件，替换所有损坏的文档字符串为英文
with open('export_combinations.py', 'r', encoding='gbk', errors='ignore') as f:
    content = f.read()

# 替换文档字符串
replacements = {
    '"""获取所有历史开奖号码组合': '"""Get all historical winning combinations',
    '"""解析历史数据字符串，返回号码组合集合"""': '"""Parse historical data"""',
    '"""获取所有四连号组合（包含4个或以上连续号码）""': '"""Get all four-consecutive combinations"""',
    '"""获取所有等差/等比数列组合"""': '"""Get all arithmetic/geometric combinations"""',
    '"""获取全奇数或全偶数组合"""': '"""Get all-odd or all-even combinations"""',
    '"""获取同一区域的号码组合"""': '"""Get same-zone combinations"""',
    '"""导出过滤后的号码组合"""': '"""Export filtered combinations"""',
    '"""大乐透号码组合导出器"""': '"""Daletou Exporter"""',
}

for old, new in replacements.items():
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        print(f"替换: {old[:20]}... ({count}次)")

# 确保有编码声明
if not content.startswith('# -*- coding: utf-8 -*-'):
    content = '# -*- coding: utf-8 -*-\n' + content

# 用UTF-8保存
with open('export_combinations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ 文件修复完成")
