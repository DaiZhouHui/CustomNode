#!/usr/bin/env python3
"""
FOFA配置工具
用于创建和更新配置文件
"""

import json
import os
import base64
from datetime import datetime

def create_default_config():
    """创建默认配置模板"""
    config = {
        "cookies": "",
        "query_string": 'asn!="13335" && server=="cloudflare" && region="HK" && port="443"',
        "settings": {
            "timeout": 30,
            "max_results": 50,
            "debug_mode": False,
            "filter_common_ips": True
        }
    }
    return config

def encode_query(query_string):
    """编码查询语句为base64"""
    try:
        query_bytes = query_string.encode('utf-8')
        base64_bytes = base64.b64encode(query_bytes)
        base64_string = base64_bytes.decode('utf-8')
        return base64_string
    except Exception as e:
        print(f"编码失败: {e}")
        return None

def show_current_config(config):
    """显示当前配置"""
    print("\n📋 当前配置:")
    print("-" * 60)
    
    cookies = config.get('cookies', '')
    if cookies:
        print(f"✅ Cookie: 已设置 ({len(cookies)} 字符)")
        if 'fofa_token' in cookies:
            print(f"   ✅ 包含 fofa_token")
    else:
        print("❌ Cookie: 未设置")
    
    query = config.get('query_string', '')
    if query:
        print(f"✅ 查询语句: {query}")
        encoded = encode_query(query)
        if encoded:
            print(f"   Base64编码: {encoded[:50]}...")
    else:
        print("❌ 查询语句: 未设置")
    
    settings = config.get('settings', {})
    print(f"✅ 超时时间: {settings.get('timeout', 30)}秒")
    print(f"✅ 最大结果数: {settings.get('max_results', 50)}")
    print(f"✅ 调试模式: {settings.get('debug_mode', False)}")
    print(f"✅ 过滤常见IP: {settings.get('filter_common_ips', True)}")
    print("-" * 60)

def update_config():
    """更新配置"""
    config_file = "config.json"
    
    # 加载现有配置或创建新配置
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 已加载现有配置")
    else:
        config = create_default_config()
        print(f"📝 创建新配置")
    
    while True:
        show_current_config(config)
        
        print("\n📝 配置选项:")
        print("  1. 更新Cookie")
        print("  2. 更新查询语句")
        print("  3. 更新设置")
        print("  4. 测试查询语句编码")
        print("  5. 保存并退出")
        print("  6. 退出不保存")
        
        try:
            choice = input("\n请选择操作 (1-6): ").strip()
        except EOFError:
            choice = '6'
        
        if choice == '1':
            print("\n📝 更新Cookie:")
            print("请从浏览器开发者工具复制Cookie:")
            print("1. 打开FOFA网站并登录")
            print("2. 按F12打开开发者工具")
            print("3. 切换到Network标签")
            print("4. 刷新页面")
            print("5. 找到任意请求，复制Cookie请求头的值")
            print("\n粘贴Cookie字符串（格式: name1=value1; name2=value2; ...）:")
            cookies = input("Cookie: ").strip()
            if cookies:
                config['cookies'] = cookies
                print("✅ Cookie已更新")
        
        elif choice == '2':
            print("\n📝 更新查询语句:")
            print("示例: asn!=\"13335\" && server==\"cloudflare\" && region=\"HK\" && port=\"443\"")
            print("支持的语法:")
            print("  - asn!=\"13335\"  (ASN不是13335)")
            print("  - server==\"cloudflare\"  (服务器是cloudflare)")
            print("  - region=\"HK\"  (地区是香港)")
            print("  - port=\"443\"  (端口是443)")
            print("\n输入新的查询语句:")
            query = input("查询语句: ").strip()
            if query:
                config['query_string'] = query
                print("✅ 查询语句已更新")
        
        elif choice == '3':
            print("\n📝 更新设置:")
            settings = config.get('settings', {})
            
            try:
                timeout = input(f"超时时间 (当前: {settings.get('timeout', 30)}) [秒]: ").strip()
                if timeout.isdigit():
                    settings['timeout'] = int(timeout)
                
                max_results = input(f"最大结果数 (当前: {settings.get('max_results', 50)}): ").strip()
                if max_results.isdigit():
                    settings['max_results'] = int(max_results)
                
                debug_mode = input(f"调试模式 (当前: {settings.get('debug_mode', False)}) [y/n]: ").strip().lower()
                if debug_mode in ['y', 'yes']:
                    settings['debug_mode'] = True
                elif debug_mode in ['n', 'no']:
                    settings['debug_mode'] = False
                
                filter_ips = input(f"过滤常见IP (当前: {settings.get('filter_common_ips', True)}) [y/n]: ").strip().lower()
                if filter_ips in ['y', 'yes']:
                    settings['filter_common_ips'] = True
                elif filter_ips in ['n', 'no']:
                    settings['filter_common_ips'] = False
                
                config['settings'] = settings
                print("✅ 设置已更新")
            except Exception as e:
                print(f"❌ 输入错误: {e}")
        
        elif choice == '4':
            print("\n🔧 测试查询语句编码:")
            query = config.get('query_string', '')
            if query:
                encoded = encode_query(query)
                if encoded:
                    print(f"查询语句: {query}")
                    print(f"Base64编码: {encoded}")
                    print(f"编码长度: {len(encoded)} 字符")
                    
                    # 显示构建的URL示例
                    import urllib.parse
                    encoded_url = urllib.parse.quote(encoded, safe='')
                    url = f"https://en.fofa.info/result?qbase64={encoded_url}"
                    print(f"\n示例URL: {url[:80]}...")
                else:
                    print("❌ 编码失败")
            else:
                print("❌ 请先设置查询语句")
        
        elif choice == '5':
            # 保存配置
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                print(f"✅ 配置已保存到: {config_file}")
                
                # 备份旧配置
                if os.path.exists(config_file):
                    backup_file = f"{config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    import shutil
                    shutil.copy2(config_file, backup_file)
                    print(f"📁 配置已备份到: {backup_file}")
                
                break
            except Exception as e:
                print(f"❌ 保存配置失败: {e}")
        
        elif choice == '6':
            print("\n👋 退出配置工具")
            break
        
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    print("=" * 60)
    print("FOFA配置工具")
    print("=" * 60)
    
    update_config()
    
    print("\n📚 使用说明:")
    print("1. 运行 'python crawler.py' 启动爬虫")
    print("2. 需要更新配置时运行 'python tool.py'")
    print("3. 查看结果: results.csv")
    print("4. 调试文件: debug/ 目录（如果启用调试模式）")
    
    input("\n按回车键退出...")