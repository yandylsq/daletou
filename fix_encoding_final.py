# -*- coding: utf-8 -*-
"""
终极编码修复方案
"""

# 尝试多种编码读取文件
encodings = ['gbk', 'gb18030', 'gb2312', 'utf-8', 'latin1']
content = None

print("尝试读取文件...")
for enc in encodings:
    try:
        with open('export_combinations.py', 'r', encoding=enc, errors='ignore') as f:
            content = f.read()
        
        # 检查是否包含关键内容
        if 'DaletouExporter' in content and 'get_consecutive_combinations' in content:
            print(f"✓ 成功用 {enc} 编码读取文件")
            break
    except:
        continue

if not content:
    print("✗ 无法读取文件")
    exit(1)

# 确保包含编码声明
if not content.startswith('# -*- coding: utf-8 -*-'):
    if content.startswith('#'):
        # 如果有其他开头，替换第一行
        lines = content.split('\n')
        lines[0] = '# -*- coding: utf-8 -*-'
        content = '\n'.join(lines)
    else:
        # 否则在开头添加
        content = '# -*- coding: utf-8 -*-\n' + content

# 确保"四连号"而不是"顺子号"
content = content.replace('顺子号', '四连号')

# 用UTF-8编码写回，使用Unix换行符
with open('export_combinations.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✓ 文件修复完成")

# 验证
try:
    compile(content, 'export_combinations.py', 'exec')
    print("✓ 文件语法正确")
except Exception as e:
    print(f"✗ 语法错误: {e}")
