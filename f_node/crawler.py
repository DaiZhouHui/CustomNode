#!/usr/bin/env python3
"""
FOFA爬虫 - GitHub Actions优化版
支持命令行参数和环境变量
"""

import requests
import json
import os
import sys
import csv
import re
import base64
import time
import argparse
from datetime import datetime
from urllib.parse import quote

class FOFACrawler:
    def __init__(self, config_file=None):
        """初始化爬虫"""
        # 确定配置文件路径
        if config_file:
            self.config_file = config_file
        else:
            # 尝试在当前目录查找config.json
            self.config_file = "config.json"
            
        self.config = self.load_config()
        self.data_found = False
        self.extracted_data = []
        
        # 优先从环境变量读取Cookie
        env_cookie = os.getenv('FOFA_COOKIE')
        if env_cookie and 'cookies' in self.config:
            self.config['cookies'] = env_cookie
        elif env_cookie:
            self.config['cookies'] = env_cookie
        
        # 设置完整请求头（用于带Cookie的请求）
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
        
        # 设置简单请求头（用于不带Cookie的请求）
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
            print(f"   使用默认配置或环境变量")
            
            # 尝试从环境变量构建配置
            query_string = os.getenv('FOFA_QUERY', '')
            cookies = os.getenv('FOFA_COOKIE', '')
            
            if not query_string:
                print("❌ 未找到查询语句，请在环境变量中设置 FOFA_QUERY")
                return {}
            
            return {
                'query_string': query_string,
                'cookies': cookies,
                'settings': {
                    'timeout': 30,
                    'max_results': 10,  # 修改为10
                    'filter_common_ips': True,
                    'debug_mode': os.getenv('FOFA_DEBUG', 'false').lower() == 'true'
                }
            }
        
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
        
        # 按照新的优先级构建URL列表
        # 1. 带参数、带cookie和请求头的英文站（首选）
        urls.append({
            'name': '带参数和Cookie的英文站',
            'url': f"https://en.fofa.info/result?qbase64={encoded_base64}",
            'headers': self.full_headers,
            'has_cookie': True
        })
        
        # 2. 带参数的英文站，不带cookie和请求头
        urls.append({
            'name': '带参数不带Cookie的英文站',
            'url': f"https://en.fofa.info/result?qbase64={encoded_base64}",
            'headers': self.simple_headers,
            'has_cookie': False
        })
        
        # 3. 带参数的中文站，不带cookie和请求头
        urls.append({
            'name': '带参数不带Cookie的中文站',
            'url': f"https://fofa.info/result?qbase64={encoded_base64}",
            'headers': self.simple_headers,
            'has_cookie': False
        })
        
        print(f"✅ 构建了 {len(urls)} 个URL（按优先级排序）")
        for i, url_info in enumerate(urls):
            cookie_status = "有Cookie" if url_info['has_cookie'] else "无Cookie"
            print(f"  {i+1}. {url_info['name']} ({cookie_status})")
            print(f"     URL: {url_info['url'][:80]}...")
        
        return urls
    
    def make_request(self, url_info):
        """发送HTTP请求"""
        print(f"\n📡 发送请求到: {url_info['name']}")
        print(f"  URL: {url_info['url']}")
        print(f"  请求头: {'完整' if url_info['has_cookie'] else '简单'}")
        
        try:
            response = requests.get(
                url_info['url'], 
                headers=url_info['headers'], 
                timeout=self.config.get('settings', {}).get('timeout', 30),
                allow_redirects=True
            )
            
            print(f"  ✅ 请求完成!")
            print(f"    状态码: {response.status_code}")
            print(f"    响应大小: {len(response.content)} 字节")
            print(f"    内容类型: {response.headers.get('Content-Type', '未知')}")
            
            # 检查是否需要保存调试HTML
            if self.config.get('settings', {}).get('debug_mode', False):
                self.save_debug_html(response.text, url_info['name'])
            
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
    
    def save_debug_html(self, content, name):
        """保存调试HTML文件"""
        try:
            debug_dir = "debug"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = name.replace(" ", "_").replace("/", "_")[:30]
            filename = f"{debug_dir}/{timestamp}_{safe_name}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content[:10000])  # 只保存前10000字符
            
            print(f"    📁 调试HTML已保存: {filename}")
        except Exception as e:
            print(f"    ⚠️  保存调试HTML失败: {e}")
    
    def extract_table_data(self, html_content):
        """从表格中提取IP和端口数据（主要方法）"""
        print("  正在解析表格数据...")
        
        ip_port_pairs = []
        
        # 方法1: 直接匹配每个数据条目中的三个关键元素
        print("    方法1: 直接匹配数据条目...")
        
        # 首先找到所有的数据条目容器
        # 每个条目由<div class="hsxa-meta-data-item">开始
        item_pattern = r'<div class="hsxa-meta-data-item">(.*?)</div>\s*</div>\s*</div>\s*</div>'
        items = re.findall(item_pattern, html_content, re.DOTALL)
        
        print(f"      找到 {len(items)} 个数据条目")
        
        for item_index, item_html in enumerate(items):
            # 在每个条目中提取IP、端口和HOST
            
            # 1. 提取IP地址
            ip_pattern = r'<a[^>]*href="[^"]*qbase64=aXA=[^"]*"[^>]*class="hsxa-jump-a"[^>]*>([^<]+)</a>'
            ip_matches = re.findall(ip_pattern, item_html, re.DOTALL)
            
            if ip_matches:
                ip = ip_matches[0].strip()
                # 检查是否有隐藏的IP（display:none）
                if len(ip_matches) > 1:
                    for ip_candidate in ip_matches[1:]:
                        if 'display:none' not in ip_candidate and ip_candidate.strip():
                            ip = ip_candidate.strip()
                            break
            else:
                # 如果找不到hsxa-jump-a，尝试其他模式
                ip_pattern2 = r'>\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*<'
                ip_matches2 = re.findall(ip_pattern2, item_html)
                ip = ip_matches2[0].strip() if ip_matches2 else None
            
            # 2. 提取端口
            port_pattern = r'<a[^>]*href="[^"]*qbase64=cG9ydD=[^"]*"[^>]*class="hsxa-port"[^>]*>([^<]+)</a>'
            port_matches = re.findall(port_pattern, item_html, re.DOTALL)
            
            if port_matches:
                port = port_matches[0].strip()
            else:
                # 如果找不到hsxa-port，尝试其他模式
                port_pattern2 = r'port[^0-9]*(\d{1,5})'
                port_matches2 = re.search(port_pattern2, item_html, re.IGNORECASE)
                port = port_matches2.group(1) if port_matches2 else "443"
            
            # 3. 验证IP并添加到列表
            if ip and self.is_valid_ip(ip):
                # 确保端口是有效的数字
                if not port.isdigit():
                    # 尝试从端口中提取数字
                    port_match = re.search(r'(\d{1,5})', port)
                    port = port_match.group(1) if port_match else "443"
                
                ip_port_pairs.append([ip, port])
                print(f"      条目 {item_index+1}: IP={ip}, 端口={port}")
        
        # 方法2: 如果方法1没找到数据，尝试通用的结构化提取
        if not ip_port_pairs:
            print("    方法2: 尝试通用结构化提取...")
            
            # 查找所有包含IP的链接
            all_ip_links = re.findall(r'<a[^>]*href="[^"]*qbase64=aXA=[^"]*"[^>]*>([^<]+)</a>', html_content)
            all_port_links = re.findall(r'<a[^>]*href="[^"]*qbase64=cG9ydD=[^"]*"[^>]*>([^<]+)</a>', html_content)
            
            print(f"      找到 {len(all_ip_links)} 个IP链接, {len(all_port_links)} 个端口链接")
            
            # 假设IP和端口是按顺序对应的
            min_count = min(len(all_ip_links), len(all_port_links))
            for i in range(min_count):
                ip = all_ip_links[i].strip()
                port = all_port_links[i].strip()
                
                if self.is_valid_ip(ip):
                    if not port.isdigit():
                        port_match = re.search(r'(\d{1,5})', port)
                        port = port_match.group(1) if port_match else "443"
                    
                    ip_port_pairs.append([ip, port])
        
        # 方法3: 提取host链接中的IP
        if not ip_port_pairs:
            print("    方法3: 提取host链接...")
            
            # 查找host链接
            host_pattern = r'<a[^>]*href="(https?://[^"]*)"[^>]*target="_blank"[^>]*>[^<]*<i[^>]*class="[^"]*icon-link[^"]*"[^>]*>'
            host_matches = re.findall(host_pattern, html_content)
            
            for host_url in host_matches:
                # 从host URL中提取IP
                ip_match = re.search(r'https?://([^:/]+)', host_url)
                if ip_match:
                    host = ip_match.group(1)
                    # 检查是否是IP地址
                    if self.is_valid_ip(host):
                        # 从URL中提取端口
                        port_match = re.search(r':(\d+)/?', host_url)
                        port = port_match.group(1) if port_match else "443"
                        ip_port_pairs.append([host, port])
        
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
        
        # 方法1: 尝试表格解析（改进版）
        ip_port_pairs = self.extract_table_data(html_content)
        
        # 方法2: 如果表格解析失败，使用备用方法
        if not ip_port_pairs:
            print("  表格解析未找到数据，使用备用方法...")
            
            # 备用方法1: 直接查找所有IP和端口
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            all_ips = re.findall(ip_pattern, html_content)
            
            # 过滤和验证IP
            valid_ips = []
            for ip in all_ips:
                if self.is_valid_ip(ip):
                    if ip not in valid_ips:
                        valid_ips.append(ip)
            
            print(f"    找到 {len(all_ips)} 个IP，过滤后 {len(valid_ips)} 个有效IP")
            
            # 为每个IP分配端口
            for ip in valid_ips[:self.config.get('settings', {}).get('max_results', 10)]:
                # 在IP附近查找端口
                ip_index = html_content.find(ip)
                if ip_index != -1:
                    # 查看IP前后200字符
                    start = max(0, ip_index - 200)
                    end = min(len(html_content), ip_index + 200)
                    context = html_content[start:end]
                    
                    # 查找端口
                    port = "443"  # 默认端口
                    
                    # 尝试多种方式查找端口
                    port_patterns = [
                        r'port[^0-9]*(\d{1,5})',
                        r'端口[^0-9]*(\d{1,5})',
                        r':(\d{1,5})/',
                        r'>(\d{1,5})<'
                    ]
                    
                    for pattern in port_patterns:
                        port_match = re.search(pattern, context, re.IGNORECASE)
                        if port_match:
                            port_candidate = port_match.group(1)
                            if 1 <= int(port_candidate) <= 65535:
                                port = port_candidate
                                break
                    
                    ip_port_pairs.append([ip, port])
        
        # 去重
        unique_pairs = []
        seen = set()
        
        for pair in ip_port_pairs:
            key = tuple(pair)
            if key not in seen:
                seen.add(key)
                unique_pairs.append(pair)
        
        print(f"  找到 {len(ip_port_pairs)} 个IP端口对，去重后 {len(unique_pairs)} 个")
        
        # 显示前几个结果
        if unique_pairs:
            print(f"\n  数据预览 (前{min(10, len(unique_pairs))}条):")
            for i, pair in enumerate(unique_pairs[:10]):
                print(f"    {i+1:2d}. IP: {pair[0]:15s} 端口: {pair[1]}")
        
        return unique_pairs
    
    def save_to_csv(self, data, output_file=None):
        """保存数据到CSV文件"""
        if not data:
            print("❌ 没有数据可保存")
            return False
        
        if not output_file:
            output_file = "results.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['IP地址', '端口'])
                writer.writerows(data)
            
            print(f"\n✅ 数据已保存到: {output_file}")
            print(f"   共保存 {len(data)} 条记录")
            
            # 显示数据统计
            print(f"\n📊 数据统计:")
            print("-" * 40)
            print(f"总记录数: {len(data)}")
            if len(data) > 0:
                print(f"第一条: IP: {data[0][0]:15s} 端口: {data[0][1]}")
                print(f"最后一条: IP: {data[-1][0]:15s} 端口: {data[-1][1]}")
            print("-" * 40)
            
            return True
        except Exception as e:
            print(f"\n❌ 保存CSV失败: {e}")
            return False
    
    def run(self):
        """运行爬虫主逻辑"""
        print("=" * 60)
        print("FOFA爬虫 v3.0 - GitHub Actions优化版")
        print("=" * 60)
        
        # 检查配置
        if not self.config:
            print("❌ 配置加载失败，请检查配置文件或环境变量")
            return False
        
        if 'cookies' not in self.config or not self.config['cookies']:
            print("⚠️  没有找到Cookie，部分URL可能无法访问")
        
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
                    
                    # 获取到数据后立即停止
                    print(f"\n✅ 已成功获取数据，停止尝试后续URL")
                    break
                else:
                    print(f"  ⚠️  请求成功但未提取到数据，尝试下一个URL")
                    # 短暂延迟，避免请求过快
                    time.sleep(1)
            else:
                print(f"  ❌ 请求失败: {response}")
                # 短暂延迟
                time.sleep(1)
        
        # 总结
        if self.data_found:
            print("\n🎉 爬虫执行成功!")
            return True
        else:
            print("\n😞 所有URL尝试都未获取到数据")
            print("\n建议:")
            print("1. 检查Cookie是否过期")
            print("2. 尝试更新Cookie")
            print("3. 确认查询语句正确")
            print("4. 手动访问URL确认可访问性")
            
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FOFA爬虫工具')
    parser.add_argument('--config', default=None, help='配置文件路径')
    parser.add_argument('--output', default='results.csv', help='输出文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    crawler = FOFACrawler(args.config)
    
    # 如果指定了debug模式，调整配置
    if args.debug:
        if 'settings' not in crawler.config:
            crawler.config['settings'] = {}
        crawler.config['settings']['debug_mode'] = True
    
    try:
        success = crawler.run()
        
        if success and crawler.extracted_data:
            # 保存数据到指定文件
            crawler.save_to_csv(crawler.extracted_data, args.output)
            print("\n🎉 程序执行完成!")
            return 0
        else:
            print("\n❌ 程序执行失败")
            return 1
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断执行")
        return 1
    except Exception as e:
        print(f"\n❌ 程序执行异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())