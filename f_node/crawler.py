#!/usr/bin/env python3
"""
FOFA爬虫 - 高级反反爬版
专门应对FOFA的反爬虫机制
"""

import requests
import json
import os
import sys
import csv
import re
import base64
import time
import random
from datetime import datetime
from urllib.parse import quote
import hashlib
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedFOFACrawler:
    def __init__(self, config_file="config.json"):
        """初始化高级爬虫"""
        self.config_file = config_file
        self.config = self.load_config()
        self.data_found = False
        self.extracted_data = []
        
        # 会话管理
        self.session = requests.Session()
        
        # 浏览器指纹
        self.browser_fingerprint = self.generate_browser_fingerprint()
        
        # 请求头池
        self.header_pool = self.generate_header_pool()
        
        # 代理设置
        self.proxy_pool = self.config.get('proxies', [])
        self.current_proxy_index = 0
        
        # 请求统计
        self.request_count = 0
        self.last_request_time = 0
        
        # 初始化Cookie
        self.init_cookies()
        
        # 反爬检测
        self.anti_anti_crawler_settings = {
            'min_delay': self.config.get('settings', {}).get('min_delay', 5),
            'max_delay': self.config.get('settings', {}).get('max_delay', 15),
            'random_mouse_movements': True,
            'random_scrolls': True,
            'human_typing_pattern': True
        }
        
        # 保存响应的目录
        self.debug_dir = "debug_responses"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def generate_browser_fingerprint(self):
        """生成浏览器指纹"""
        return {
            'screen_resolution': f"{random.randint(1280, 1920)}x{random.randint(720, 1080)}",
            'language': random.choice(['zh-CN', 'en-US', 'en-GB', 'zh-TW']),
            'timezone': random.choice(['Asia/Shanghai', 'America/New_York', 'Europe/London']),
            'platform': random.choice(['Win32', 'Win64', 'MacIntel', 'Linux x86_64']),
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16]),
            'pixel_ratio': random.choice([1, 1.25, 1.5, 2]),
            'webgl_vendor': random.choice(['NVIDIA Corporation', 'Intel Inc.', 'AMD']),
            'webgl_renderer': random.choice(['NVIDIA GeForce GTX', 'Intel HD Graphics', 'AMD Radeon'])
        }
    
    def generate_header_pool(self):
        """生成请求头池"""
        return [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
                'Connection': 'keep-alive'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        ]
    
    def get_random_headers(self):
        """获取随机请求头"""
        headers = random.choice(self.header_pool)
        
        # 添加浏览器指纹信息
        headers['X-Screen-Resolution'] = self.browser_fingerprint['screen_resolution']
        headers['Accept-Language'] = self.browser_fingerprint['language']
        
        return headers
    
    def get_proxy(self):
        """获取代理"""
        if not self.proxy_pool:
            return None
        
        proxy = self.proxy_pool[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_pool)
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def init_cookies(self):
        """初始化Cookie"""
        cookies_str = self.config.get('cookies', '')
        cookies_dict = self.parse_cookies_string(cookies_str)
        
        # 更新会话Cookie
        for key, value in cookies_dict.items():
            self.session.cookies.set(key, value)
    
    def parse_cookies_string(self, cookies_str):
        """解析Cookie字符串为字典"""
        cookies_dict = {}
        for cookie in cookies_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies_dict[key] = value
        return cookies_dict
    
    def human_like_delay(self):
        """模拟人类操作的延迟"""
        min_delay = self.anti_anti_crawler_settings['min_delay']
        max_delay = self.anti_anti_crawler_settings['max_delay']
        
        # 基础延迟
        base_delay = random.uniform(min_delay, max_delay)
        
        # 随机思考时间
        thinking_time = random.uniform(0.5, 3.0)
        
        # 鼠标移动时间
        if self.anti_anti_crawler_settings['random_mouse_movements']:
            mouse_movement_time = random.uniform(0.1, 1.5)
        else:
            mouse_movement_time = 0
        
        total_delay = base_delay + thinking_time + mouse_movement_time
        
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < total_delay:
            sleep_time = total_delay - time_since_last_request
            logger.info(f"⏳ 模拟人类延迟: 等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
    
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            logger.error(f"配置文件 {self.config_file} 不存在")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("✅ 配置文件加载成功")
            return config
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}
    
    def encode_query(self, query_string):
        """将查询字符串编码为base64格式"""
        try:
            query_bytes = query_string.encode('utf-8')
            base64_bytes = base64.b64encode(query_bytes)
            base64_string = base64_bytes.decode('utf-8')
            return base64_string
        except Exception as e:
            logger.error(f"Base64编码失败: {e}")
            return None
    
    def build_urls(self):
        """构建URL列表"""
        urls = []
        
        query_string = self.config.get('query_string', '')
        if not query_string:
            logger.error("❌ 配置文件中没有查询语句")
            return urls
        
        base64_query = self.encode_query(query_string)
        if not base64_query:
            return urls
        
        encoded_base64 = quote(base64_query, safe='')
        
        # 使用多个不同的URL模式
        url_templates = [
            f"https://en.fofa.info/result?qbase64={encoded_base64}",
            f"https://en.fofa.info/result?q={encoded_base64}&qbase64={encoded_base64}",
            f"https://en.fofa.info/result?qbase64={encoded_base64}&page=1&page_size=10"
        ]
        
        for i, template in enumerate(url_templates):
            urls.append({
                'name': f'尝试{i+1}',
                'url': template,
                'priority': i
            })
        
        logger.info(f"✅ 构建了 {len(urls)} 个URL")
        return urls
    
    def check_anti_crawler(self, response):
        """检查反爬虫机制"""
        anti_crawler_indicators = [
            '验证码', 'captcha', '请输入验证码', '访问过于频繁',
            '请先登录', '登录失效', 'Cookie过期', '人机验证',
            'Just a moment...', 'Checking your browser',
            'Security Check', 'Access Denied', 'robot'
        ]
        
        content_lower = response.text.lower()
        
        for indicator in anti_crawler_indicators:
            if indicator.lower() in content_lower:
                logger.warning(f"⚠️ 检测到反爬虫指示: {indicator}")
                return True
        
        # 检查响应长度
        if len(response.text) < 1000:
            logger.warning(f"⚠️ 响应内容过短 ({len(response.text)} 字节)，可能被拦截")
            return True
        
        return False
    
    def make_request(self, url_info, attempt=1):
        """发送HTTP请求"""
        self.request_count += 1
        
        logger.info(f"\n📡 发送请求 #{self.request_count}: {url_info['name']} (尝试 {attempt}/3)")
        
        # 人类延迟
        self.human_like_delay()
        
        try:
            # 准备请求参数
            headers = self.get_random_headers()
            proxy = self.get_proxy()
            
            # 添加Referer
            if random.random() > 0.5:
                headers['Referer'] = 'https://en.fofa.info/'
            
            request_kwargs = {
                'url': url_info['url'],
                'headers': headers,
                'timeout': self.config.get('settings', {}).get('timeout', 30),
                'allow_redirects': True,
                'verify': True  # 启用SSL验证
            }
            
            if proxy:
                request_kwargs['proxies'] = proxy
                logger.info(f"  使用代理: {proxy.get('https', proxy.get('http'))}")
            
            # 随机选择GET或POST（大多数情况是GET）
            if random.random() < 0.1:  # 10%的概率使用POST
                response = self.session.post(**request_kwargs)
                logger.info("  使用POST方法")
            else:
                response = self.session.get(**request_kwargs)
            
            self.last_request_time = time.time()
            
            logger.info(f"  ✅ 请求完成!")
            logger.info(f"    状态码: {response.status_code}")
            logger.info(f"    响应大小: {len(response.text)} 字节")
            
            # 检查反爬虫
            if self.check_anti_crawler(response):
                if attempt < 3:
                    logger.warning(f"  ⚠️ 检测到反爬虫，等待后重试...")
                    time.sleep(random.uniform(10, 30))
                    
                    # 切换User-Agent
                    self.session.headers.update(self.get_random_headers())
                    
                    return self.make_request(url_info, attempt + 1)
                return False, "反爬虫机制检测"
            
            if response.status_code == 200:
                return True, response
            elif response.status_code == 429:
                logger.warning(f"  ⚠️ 请求过于频繁 (429)，等待重试...")
                time.sleep(random.uniform(30, 60))
                if attempt < 3:
                    return self.make_request(url_info, attempt + 1)
                return False, "请求过于频繁"
            elif response.status_code == 403:
                logger.error(f"  ❌ 访问被拒绝 (403)")
                return False, "访问被拒绝"
            elif response.status_code == 401:
                logger.error(f"  ❌ 需要认证 (401)")
                return False, "需要认证"
            else:
                logger.error(f"  ❌ HTTP错误: {response.status_code}")
                return False, f"HTTP错误: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"  ⏰ 请求超时")
            if attempt < 3:
                time.sleep(random.uniform(5, 10))
                return self.make_request(url_info, attempt + 1)
            return False, "请求超时"
        except requests.exceptions.ConnectionError:
            logger.error(f"  🔌 连接错误")
            if attempt < 3:
                time.sleep(random.uniform(10, 20))
                return self.make_request(url_info, attempt + 1)
            return False, "连接错误"
        except Exception as e:
            logger.error(f"  ❌ 请求异常: {type(e).__name__}: {str(e)}")
            if attempt < 3:
                time.sleep(random.uniform(5, 15))
                return self.make_request(url_info, attempt + 1)
            return False, f"请求异常: {type(e).__name__}"
    
    def extract_data_from_response(self, response):
        """从响应中提取IP和端口数据"""
        logger.info("\n🔍 正在提取数据...")
        
        html_content = response.text
        
        # 保存响应用于分析
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"{self.debug_dir}/response_{timestamp}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"  响应已保存到: {debug_file}")
        
        # 多种提取方法
        extraction_methods = [
            self.extract_via_host_pattern,
            self.extract_via_clipboard,
            self.extract_via_ip_port_links,
            self.extract_via_regex
        ]
        
        all_pairs = []
        
        for method in extraction_methods:
            pairs = method(html_content)
            if pairs:
                logger.info(f"  方法 {method.__name__} 找到 {len(pairs)} 条数据")
                all_pairs.extend(pairs)
                if len(all_pairs) >= self.config.get('settings', {}).get('max_results', 10):
                    break
            else:
                logger.info(f"  方法 {method.__name__} 未找到数据")
        
        # 去重
        unique_pairs = []
        seen = set()
        
        for pair in all_pairs:
            key = tuple(pair)
            if key not in seen:
                seen.add(key)
                unique_pairs.append(pair)
        
        logger.info(f"  总共找到 {len(all_pairs)} 个IP端口对，去重后 {len(unique_pairs)} 个")
        
        # 限制最大结果数量
        max_results = self.config.get('settings', {}).get('max_results', 10)
        if len(unique_pairs) > max_results:
            unique_pairs = unique_pairs[:max_results]
            logger.info(f"  限制为前 {max_results} 条结果")
        
        # 显示结果
        if unique_pairs:
            logger.info(f"\n  数据预览:")
            for i, pair in enumerate(unique_pairs):
                logger.info(f"    {i+1:2d}. IP: {pair[0]:15s} 端口: {pair[1]}")
        else:
            logger.warning("  ⚠️  未提取到任何数据")
            # 尝试从保存的文件中分析
            self.analyze_html_structure(html_content)
        
        return unique_pairs
    
    def extract_via_host_pattern(self, html_content):
        """通过host模式提取"""
        pattern = r'<span class="hsxa-host"[^>]*>\s*<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html_content)
        
        pairs = []
        for match in matches:
            match = match.strip()
            if ':' in match:
                ip, port = match.split(':', 1)
                if self.is_valid_ip(ip):
                    pairs.append([ip, port])
        
        return pairs
    
    def extract_via_clipboard(self, html_content):
        """通过clipboard数据提取"""
        pattern = r'data-clipboard-text="([^"]+:\d+)"'
        matches = re.findall(pattern, html_content)
        
        pairs = []
        for match in matches:
            if ':' in match:
                ip, port = match.split(':', 1)
                if self.is_valid_ip(ip):
                    pairs.append([ip, port])
        
        return pairs
    
    def extract_via_ip_port_links(self, html_content):
        """通过独立的IP和端口链接提取"""
        # 提取IP
        ip_pattern = r'<a[^>]*class="hsxa-jump-a"[^>]*href="[^"]*qbase64=aXA=[^"]*"[^>]*>([^<]+)</a>'
        ip_matches = re.findall(ip_pattern, html_content)
        
        # 提取端口
        port_pattern = r'<a[^>]*class="hsxa-port"[^>]*href="[^"]*qbase64=cG9ydD=[^"]*"[^>]*>([^<]+)</a>'
        port_matches = re.findall(port_pattern, html_content)
        
        pairs = []
        min_count = min(len(ip_matches), len(port_matches))
        for i in range(min_count):
            ip = ip_matches[i].strip()
            port = port_matches[i].strip()
            
            if self.is_valid_ip(ip):
                if not port.isdigit():
                    port_match = re.search(r'(\d{1,5})', port)
                    port = port_match.group(1) if port_match else "443"
                
                pairs.append([ip, port])
        
        return pairs
    
    def extract_via_regex(self, html_content):
        """通过正则表达式提取"""
        # 匹配IP:端口格式
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
        matches = re.findall(pattern, html_content)
        
        pairs = []
        for ip, port in matches:
            if self.is_valid_ip(ip):
                pairs.append([ip, port])
        
        return pairs
    
    def analyze_html_structure(self, html_content):
        """分析HTML结构"""
        logger.info("  分析HTML结构...")
        
        # 查找关键元素
        elements = {
            'hsxa-meta-data-item': html_content.count('hsxa-meta-data-item'),
            'hsxa-host': html_content.count('hsxa-host'),
            'hsxa-jump-a': html_content.count('hsxa-jump-a'),
            'hsxa-port': html_content.count('hsxa-port'),
            'data-clipboard-text': html_content.count('data-clipboard-text'),
            '验证码': html_content.count('验证码'),
            'captcha': html_content.count('captcha')
        }
        
        for key, value in elements.items():
            if value > 0:
                logger.info(f"    找到 {value} 个 '{key}' 元素")
    
    def is_valid_ip(self, ip_str):
        """验证IP地址"""
        # 简化的IP验证
        pattern = r'^\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b$'
        if not re.match(pattern, ip_str):
            return False
        
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    
    def save_to_csv(self, data):
        """保存数据到CSV文件"""
        if not data:
            logger.error("❌ 没有数据可保存")
            return False
        
        output_file = "results.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['IP地址', '端口'])
                writer.writerows(data)
            
            logger.info(f"\n✅ 数据已保存到: {output_file}")
            logger.info(f"   共保存 {len(data)} 条记录")
            
            return True
        except Exception as e:
            logger.error(f"\n❌ 保存CSV失败: {e}")
            return False
    
    def run(self):
        """运行爬虫主逻辑"""
        logger.info("=" * 60)
        logger.info(f"FOFA高级爬虫 - 反反爬版")
        logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"浏览器指纹: {self.browser_fingerprint['platform']}")
        logger.info("=" * 60)
        
        # 检查配置
        if not self.config:
            logger.error("❌ 配置加载失败，请检查配置文件")
            return False
        
        # 显示查询语句
        query_string = self.config.get('query_string', '')
        logger.info(f"查询语句: {query_string}")
        
        # 构建URL列表
        urls = self.build_urls()
        if not urls:
            logger.error("❌ 无法构建URL，请检查查询语句")
            return False
        
        # 按优先级尝试URL
        for url_info in urls:
            logger.info(f"\n{'='*60}")
            logger.info(f"尝试: {url_info['name']}")
            logger.info(f"{'='*60}")
            
            success, response = self.make_request(url_info)
            
            if success:
                # 提取数据
                data = self.extract_data_from_response(response)
                
                if data:
                    logger.info(f"  ✅ 从 {url_info['name']} 成功提取到 {len(data)} 条数据")
                    self.data_found = True
                    self.extracted_data = data
                    
                    # 保存数据
                    if self.save_to_csv(data):
                        return True
                    else:
                        logger.warning(f"  ⚠️  数据提取成功但保存失败，尝试下一个URL")
                else:
                    logger.warning(f"  ⚠️  请求成功但未提取到数据，尝试下一个URL")
            else:
                logger.error(f"  ❌ 请求失败: {response}")
        
        # 总结
        if self.data_found:
            logger.info("\n🎉 爬虫执行成功!")
            return True
        else:
            logger.error("\n😞 所有URL尝试都未获取到数据")
            logger.info("💡 建议:")
            logger.info("  1. 检查Cookie是否有效")
            logger.info("  2. 增加请求延迟")
            logger.info("  3. 使用代理IP")
            logger.info("  4. 更换User-Agent")
            return False

def main():
    """主函数"""
    crawler = AdvancedFOFACrawler("config.json")
    
    try:
        success = crawler.run()
        
        if success:
            logger.info("\n✅ 程序执行成功")
            sys.exit(0)
        else:
            logger.error("\n❌ 程序执行失败")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  用户中断执行")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 程序执行异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()