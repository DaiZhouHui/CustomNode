#!/usr/bin/env python3
"""
FOFA爬虫 - GitHub Actions优化版
专为CI环境优化，去除交互式输入
"""

import requests
import json
import os
import sys
import csv
import re
import base64
import time
from datetime import datetime
from urllib.parse import quote

class FOFACrawler:
    def __init__(self, config_file="config.json"):
        """初始化爬虫"""
        self.config_file = config_file
        self.config = self.load_config()
        self.data_found = False
        self.extracted_data = []
        
        # 设置完整请求头
        self.full_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Referer': 'https://en.fofa.info/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cookie': self.config.get('cookies', '') if 'cookies' in self.config else ''
        }
        
        # 设置简单请求头
        self.simple_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        # 常见的无效IP列表
        self.invalid_ips = [
            '1.1.1.1', '8.8.8.8', '8.8.4.4', '127.0.0.1', '0.0.0.0', 
            '255.255.255.255', '192.168.0.1', '192.168.1.1', '10.0.0.1',
            '172.16.0.1', '100.64.0.1', '169.254.0.1'
        ]
    
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            print(f"❌ 配置文件 {self.config_file} 不存在")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功")
            return config
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return {}
    
    def encode_query(self, query_string):
        """将查询字符串编码为base64格式"""
        try:
            query_bytes = query_string.encode('utf-8')
            base64_bytes = base64.b64encode(query_bytes)
            base64_string = base64_bytes.decode('utf-8')
            return base64_string
        except Exception as e:
            print(f"❌ Base64编码失败: {e}")
            return None
    
    def build_urls(self):
        """构建URL列表（按优先级排序）"""
        urls = []
        
        # 获取查询字符串并编码
        query_string = self.config.get('query_string', '')
        if not query_string:
            print("❌ 配置文件中没有查询语句")
            return urls
        
        base64_query = self.encode_query(query_string)
        if not base64_query:
            return urls
        
        # URL编码base64字符串
        encoded_base64 = quote(base64_query, safe='')
        
        # 构建URL列表
        urls.append({
            'name': '带参数和Cookie的英文站',
            'url': f"https://en.fofa.info/result?qbase64={encoded_base64}",
            'headers': self.full_headers,
            'has_cookie': True
        })
        
        urls.append({
            'name': '带参数不带Cookie的英文站',
            'url': f"https://en.fofa.info/result?qbase64={encoded_base64}",
            'headers': self.simple_headers,
            'has_cookie': False
        })
        
        urls.append({
            'name': '带参数不带Cookie的中文站',
            'url': f"https://fofa.info/result?qbase64={encoded_base64}",
            'headers': self.simple_headers,
            'has_cookie': False
        })
        
        print(f"✅ 构建了 {len(urls)} 个URL")
        return urls
    
    def make_request(self, url_info):
        """发送HTTP请求"""
        print(f"\n📡 发送请求到: {url_info['name']}")
        
        try:
            response = requests.get(
                url_info['url'], 
                headers=url_info['headers'], 
                timeout=self.config.get('settings', {}).get('timeout', 30),
                allow_redirects=True
            )
            
            print(f"  ✅ 请求完成!")
            print(f"    状态码: {response.status_code}")
            
            if response.status_code == 200:
                return True, response
            elif response.status_code == 403:
                return False, "访问被拒绝 (403)"
            elif response.status_code == 401:
                return False, "需要认证 (401)"
            else:
                return False, f"HTTP错误: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, "连接错误"
        except Exception as e:
            return False, f"请求异常: {type(e).__name__}: {str(e)}"
    
    def extract_data_from_new_structure(self, html_content):
        """从新的HTML结构中提取数据"""
        print("    使用新结构解析...")
        
        ip_port_pairs = []
        
        # 方法1: 直接查找所有 hsxa-host 中的链接
        host_pattern = r'<span class="hsxa-host"[^>]*>\s*<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        host_matches = re.findall(host_pattern, html_content)
        
        print(f"      从hsxa-host找到 {len(host_matches)} 个匹配")
        
        for host_text in host_matches:
            host_text = host_text.strip()
            if ':' in host_text:
                ip, port = host_text.split(':', 1)
                if self.is_valid_ip(ip):
                    ip_port_pairs.append([ip, port])
        
        # 方法2: 从clipboard数据提取
        if not ip_port_pairs:
            print("      从clipboard数据提取...")
            copy_pattern = r'data-clipboard-text="([^"]+:\d+)"'
            copy_matches = re.findall(copy_pattern, html_content)
            
            for copy_text in copy_matches:
                if ':' in copy_text:
                    ip, port = copy_text.split(':', 1)
                    if self.is_valid_ip(ip):
                        ip_port_pairs.append([ip, port])
        
        # 方法3: 分别提取IP和端口
        if not ip_port_pairs:
            print("      分别提取IP和端口...")
            
            # 提取IP
            ip_pattern = r'<a[^>]*class="hsxa-jump-a"[^>]*href="[^"]*qbase64=aXA=[^"]*"[^>]*>([^<]+)</a>'
            ip_matches = re.findall(ip_pattern, html_content)
            
            # 提取端口
            port_pattern = r'<a[^>]*class="hsxa-port"[^>]*href="[^"]*qbase64=cG9ydD=[^"]*"[^>]*>([^<]+)</a>'
            port_matches = re.findall(port_pattern, html_content)
            
            # 假设IP和端口是按顺序对应的
            min_count = min(len(ip_matches), len(port_matches))
            for i in range(min_count):
                ip = ip_matches[i].strip()
                port = port_matches[i].strip()
                
                if self.is_valid_ip(ip):
                    # 确保端口是有效的数字
                    if not port.isdigit():
                        port_match = re.search(r'(\d{1,5})', port)
                        port = port_match.group(1) if port_match else "443"
                    
                    ip_port_pairs.append([ip, port])
        
        return ip_port_pairs
    
    def extract_data_from_old_structure(self, html_content):
        """从旧的HTML结构中提取数据"""
        print("    使用旧结构解析...")
        
        ip_port_pairs = []
        
        # 查找所有的数据条目容器
        item_pattern = r'<div class="hsxa-meta-data-item">(.*?)</div>\s*</div>\s*</div>\s*</div>'
        items = re.findall(item_pattern, html_content, re.DOTALL)
        
        print(f"      找到 {len(items)} 个数据条目")
        
        for item_index, item_html in enumerate(items):
            # 提取IP地址
            ip_pattern = r'<a[^>]*href="[^"]*qbase64=aXA=[^"]*"[^>]*class="hsxa-jump-a"[^>]*>([^<]+)</a>'
            ip_matches = re.findall(ip_pattern, item_html, re.DOTALL)
            
            if ip_matches:
                ip = ip_matches[0].strip()
            else:
                # 如果找不到hsxa-jump-a，尝试其他模式
                ip_pattern2 = r'>\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*<'
                ip_matches2 = re.findall(ip_pattern2, item_html)
                ip = ip_matches2[0].strip() if ip_matches2 else None
            
            # 提取端口
            port_pattern = r'<a[^>]*href="[^"]*qbase64=cG9ydD=[^"]*"[^>]*class="hsxa-port"[^>]*>([^<]+)</a>'
            port_matches = re.findall(port_pattern, item_html, re.DOTALL)
            
            if port_matches:
                port = port_matches[0].strip()
            else:
                # 如果找不到hsxa-port，尝试其他模式
                port_pattern2 = r'port[^0-9]*(\d{1,5})'
                port_matches2 = re.search(port_pattern2, item_html, re.IGNORECASE)
                port = port_matches2.group(1) if port_matches2 else "443"
            
            # 验证IP并添加到列表
            if ip and self.is_valid_ip(ip):
                # 确保端口是有效的数字
                if not port.isdigit():
                    port_match = re.search(r'(\d{1,5})', port)
                    port = port_match.group(1) if port_match else "443"
                
                ip_port_pairs.append([ip, port])
        
        return ip_port_pairs
    
    def extract_table_data(self, html_content):
        """从表格中提取IP和端口数据"""
        print("  正在解析表格数据...")
        
        # 首先尝试新结构
        ip_port_pairs = self.extract_data_from_new_structure(html_content)
        
        # 如果没找到，尝试旧的解析方法
        if not ip_port_pairs:
            ip_port_pairs = self.extract_data_from_old_structure(html_content)
        
        return ip_port_pairs
    
    def is_valid_ip(self, ip_str):
        """验证IP地址是否有效且不是常见无效IP"""
        # 基本IP格式验证
        ip_pattern = r'^\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b$'
        if not re.match(ip_pattern, ip_str):
            return False
        
        # 检查是否在无效IP列表中
        if self.config.get('settings', {}).get('filter_common_ips', True):
            if ip_str in self.invalid_ips:
                return False
        
        # 检查每个部分是否在有效范围内
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        # 排除一些特殊IP段
        first_octet = int(parts[0])
        if first_octet == 0:  # 0.x.x.x
            return False
        if first_octet == 10:  # 10.x.x.x (内网)
            return False
        if first_octet == 100 and 64 <= int(parts[1]) <= 127:  # 100.64.x.x-100.127.x.x (运营商NAT)
            return False
        if first_octet == 127:  # 127.x.x.x (环回)
            return False
        if first_octet == 169 and int(parts[1]) == 254:  # 169.254.x.x (链路本地)
            return False
        if first_octet == 172 and 16 <= int(parts[1]) <= 31:  # 172.16.x.x-172.31.x.x (内网)
            return False
        if first_octet == 192 and int(parts[1]) == 168:  # 192.168.x.x (内网)
            return False
        if first_octet == 198 and 18 <= int(parts[1]) <= 19:  # 198.18.x.x-198.19.x.x (测试)
            return False
        
        return True
    
    def extract_data_from_response(self, response):
        """从响应中提取IP和端口数据"""
        print("\n🔍 正在提取数据...")
        
        html_content = response.text
        
        # 尝试表格解析
        ip_port_pairs = self.extract_table_data(html_content)
        
        # 去重
        unique_pairs = []
        seen = set()
        
        for pair in ip_port_pairs:
            key = tuple(pair)
            if key not in seen:
                seen.add(key)
                unique_pairs.append(pair)
        
        print(f"  找到 {len(ip_port_pairs)} 个IP端口对，去重后 {len(unique_pairs)} 个")
        
        # 限制最大结果数量
        max_results = self.config.get('settings', {}).get('max_results', 10)
        if len(unique_pairs) > max_results:
            unique_pairs = unique_pairs[:max_results]
            print(f"  限制为前 {max_results} 条结果")
        
        # 显示结果
        if unique_pairs:
            print(f"\n  数据预览:")
            for i, pair in enumerate(unique_pairs):
                print(f"    {i+1:2d}. IP: {pair[0]:15s} 端口: {pair[1]}")
        
        return unique_pairs
    
    def save_to_csv(self, data):
        """保存数据到CSV文件"""
        if not data:
            print("❌ 没有数据可保存")
            return False
        
        output_file = "results.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['IP地址', '端口'])
                writer.writerows(data)
            
            print(f"\n✅ 数据已保存到: {output_file}")
            print(f"   共保存 {len(data)} 条记录")
            
            return True
        except Exception as e:
            print(f"\n❌ 保存CSV失败: {e}")
            return False
    
    def run(self):
        """运行爬虫主逻辑"""
        print("=" * 60)
        print(f"FOFA爬虫 - GitHub Actions版")
        print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 检查配置
        if not self.config:
            print("❌ 配置加载失败，请检查配置文件")
            return False
        
        # 显示查询语句
        query_string = self.config.get('query_string', '')
        print(f"查询语句: {query_string}")
        
        # 构建URL列表
        urls = self.build_urls()
        if not urls:
            print("❌ 无法构建URL，请检查查询语句")
            return False
        
        # 按优先级尝试URL
        for url_info in urls:
            print(f"\n{'='*60}")
            print(f"尝试: {url_info['name']}")
            print(f"{'='*60}")
            
            success, response = self.make_request(url_info)
            
            if success:
                # 提取数据
                data = self.extract_data_from_response(response)
                
                if data:
                    print(f"  ✅ 从 {url_info['name']} 成功提取到 {len(data)} 条数据")
                    self.data_found = True
                    self.extracted_data = data
                    
                    # 保存数据
                    if self.save_to_csv(data):
                        return True
                    else:
                        print(f"  ⚠️  数据提取成功但保存失败，尝试下一个URL")
                else:
                    print(f"  ⚠️  请求成功但未提取到数据，尝试下一个URL")
                    time.sleep(2)
            else:
                print(f"  ❌ 请求失败: {response}")
                time.sleep(2)
        
        # 总结
        if self.data_found:
            print("\n🎉 爬虫执行成功!")
            return True
        else:
            print("\n😞 所有URL尝试都未获取到数据")
            return False

def main():
    """主函数 - 针对CI环境优化"""
    crawler = FOFACrawler("config.json")
    
    try:
        success = crawler.run()
        
        if success:
            print("\n✅ 程序执行成功")
            sys.exit(0)  # 成功退出码
        else:
            print("\n❌ 程序执行失败")
            sys.exit(1)  # 失败退出码
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()