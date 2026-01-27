"""
大乐透历史数据自动下载脚本
从阳光彩票网下载完整历史数据
"""
import requests
import re
import os
from datetime import datetime

def download_from_17500():
    """从17500.cn下载大乐透历史数据"""
    print("=" * 60)
    print("大乐透历史数据自动下载")
    print("=" * 60)
    
    url = "https://www.17500.cn/getData/dlt.TXT"
    
    print(f"\n正在从阳光彩票网下载数据...")
    print(f"URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'gbk'  # 17500网站使用GBK编码
        
        if response.status_code == 200:
            content = response.text
            
            # 保存原始数据
            output_file = 'daletou_history_full.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 统计数据
            lines = content.strip().split('\n')
            valid_lines = [l for l in lines if l.strip()]
            
            print(f"\n✅ 下载成功！")
            print(f"   文件保存为: {output_file}")
            print(f"   总期数: {len(valid_lines)}")
            
            # 显示前5期和后5期
            if len(valid_lines) > 0:
                print(f"\n最早期号（前5期）:")
                for line in valid_lines[:5]:
                    print(f"   {line[:50]}...")
                
                print(f"\n最新期号（后5期）:")
                for line in valid_lines[-5:]:
                    print(f"   {line[:50]}...")
            
            # 数据格式转换和验证
            print(f"\n正在验证数据格式...")
            validated_data = validate_and_format(content)
            
            if validated_data:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(validated_data)
                print(f"✅ 数据格式验证通过并已格式化")
            
            return True
            
        else:
            print(f"\n❌ 下载失败")
            print(f"   HTTP状态码: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 下载超时")
        print(f"   请检查网络连接或稍后重试")
        return False
        
    except Exception as e:
        print(f"\n❌ 下载出错: {str(e)}")
        return False

def validate_and_format(content):
    """验证和格式化数据"""
    lines = content.strip().split('\n')
    formatted_lines = []
    error_count = 0
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        try:
            # 解析17500格式：期号 日期 前区号码 后区号码
            # 示例：25150 2025-12-31 13 14 15 28 31 01 05
            parts = line.split()
            
            if len(parts) < 8:
                error_count += 1
                continue
            
            period = parts[0]
            date = parts[1]
            
            # 前区5个号码
            red_numbers = []
            # 后区2个号码
            blue_numbers = []
            
            # 尝试提取数字
            numbers = [p for p in parts[2:] if p.isdigit()]
            
            if len(numbers) >= 7:
                red_numbers = numbers[:5]
                blue_numbers = numbers[5:7]
            else:
                error_count += 1
                continue
            
            # 格式化输出
            red_str = ' '.join([f"{int(n):02d}" for n in red_numbers])
            blue_str = ' '.join([f"{int(n):02d}" for n in blue_numbers])
            formatted_line = f"{period}\t{date}\t{red_str}-{blue_str}"
            formatted_lines.append(formatted_line)
            
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # 只显示前5个错误
                print(f"   警告: 第{i}行格式错误: {line[:50]}")
    
    if error_count > 0:
        print(f"   共跳过 {error_count} 行格式错误的数据")
    
    print(f"   有效数据: {len(formatted_lines)} 期")
    
    return '\n'.join(formatted_lines)

def download_from_500():
    """备选方案：从500彩票网下载（需要爬虫）"""
    print("\n提示：500彩票网数据需要通过网页爬虫获取")
    print("建议使用17500.cn的直接下载功能")
    return False

def main():
    print("\n大乐透历史数据下载工具")
    print("支持的数据源：")
    print("  1. 阳光彩票网 (17500.cn) - 推荐")
    print("  2. 手动输入URL")
    print("  3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == '1':
        success = download_from_17500()
        if success:
            print("\n" + "=" * 60)
            print("下载完成！")
            print("文件位置：daletou_history_full.txt")
            print("现在可以运行导出功能了")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("下载失败，请尝试以下方案：")
            print("1. 检查网络连接")
            print("2. 手动访问 https://www.17500.cn/getData/dlt.TXT")
            print("3. 复制内容并保存为 daletou_history_full.txt")
            print("=" * 60)
    
    elif choice == '2':
        url = input("请输入数据URL: ").strip()
        print(f"\n尝试从 {url} 下载...")
        # 这里可以扩展其他数据源的下载逻辑
        print("暂不支持自定义URL，请使用方案1或手动下载")
    
    else:
        print("\n已退出")

if __name__ == '__main__':
    # 安装依赖提示
    try:
        import requests
    except ImportError:
        print("需要安装 requests 库")
        print("请运行: pip install requests")
        exit(1)
    
    main()
