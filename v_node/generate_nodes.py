import json
import urllib.request
import time
import os
import re
from datetime import datetime
from urllib.parse import urlparse

def load_config():
    """加载配置文件"""
    try:
        with open('v_node/config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # 默认配置
        return {
            "vless_config": {
                "uuid": "471a8e64-7b21-4703-b1d1-45a221098459",
                "domain": "knny.dpdns.org",
                "port": 443,
                "path": "/?ed=2048",
                "encryption": "none",
                "security": "tls",
                "sni": "knny.dpdns.org",
                "fingerprint": "chrome",
                "network": "ws"
            },
            "api_config": {
                "top20_url": "https://vps789.com/openApi/cfIpTop20",
                "isp_url": "https://vps789.com/openApi/cfIpApi"
            },
            "naming_rules": {
                "top20_prefix": "综合优选",
                "ct_prefix": "电信优选",
                "cu_prefix": "联通优选",
                "cm_prefix": "移动优选",
                "allavg_prefix": "全网优选"
            }
        }

def fetch_api(url):
    """获取API数据"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"获取API失败 {url}: {e}")
        return None

def is_ip_address(host):
    """检查是否是IP地址"""
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    return re.match(ip_pattern, host) is not None

def extract_host_from_ip_field(ip_field):
    """从IP字段提取主机名或IP"""
    if not ip_field:
        return ""
    
    # 如果是IP地址，直接返回
    if is_ip_address(ip_field):
        return ip_field
    
    # 如果是域名，提取主机名
    try:
        # 如果包含http://或https://，解析URL
        if ip_field.startswith(('http://', 'https://')):
            parsed = urlparse(ip_field)
            return parsed.hostname or ip_field
        else:
            # 直接作为域名处理，移除可能的端口号
            host = ip_field.split(':')[0]
            return host
    except:
        return ip_field

def get_ip_or_host(ip_data):
    """从API数据中获取IP或主机名"""
    # 优先使用'ip'字段
    if 'ip' in ip_data:
        return extract_host_from_ip_field(ip_data['ip'])
    
    # 如果没有'ip'字段，尝试其他可能的字段
    for field in ['host', 'address', 'server']:
        if field in ip_data:
            return extract_host_from_ip_field(ip_data[field])
    
    # 如果都没有，返回空字符串
    return ""

def generate_vless_url(ip_data, provider, index):
    """生成VLESS节点链接"""
    config = load_config()
    vless_config = config['vless_config']
    naming_rules = config['naming_rules']
    
    # 获取address（从API数据中提取的IP或域名）
    address = get_ip_or_host(ip_data)
    if not address:
        print(f"警告: 无法从数据中提取地址: {ip_data}")
        return None
    
    # 运营商中文名称映射
    provider_names = {
        "top20": naming_rules.get('top20_prefix', '综合优选'),
        "CT": naming_rules.get('ct_prefix', '电信优选'),
        "CU": naming_rules.get('cu_prefix', '联通优选'),
        "CM": naming_rules.get('cm_prefix', '移动优选'),
        "AllAvg": naming_rules.get('allavg_prefix', '全网优选')
    }
    
    # 获取运营商名称
    provider_name = provider_names.get(provider, provider)
    
    # 生成中文描述 - 格式: 运营商-序号-完整地址
    description = f"{provider_name}-{index+1:02d}-{address}"
    
    # 使用配置中的参数
    uuid = vless_config['uuid']
    host_domain = vless_config['domain']  # 伪装域名: knny.dpdns.org
    port = vless_config['port']
    path = vless_config['path']
    sni = vless_config.get('sni', host_domain)  # SNI: knny.dpdns.org
    
    # 构建VLESS链接
    # address使用从API获取的IP或域名
    # host和SNI使用固定的knny.dpdns.org
    vless_url = f"vless://{uuid}@{address}:{port}"
    params = [
        f"encryption={vless_config['encryption']}",
        f"security={vless_config['security']}",
        f"sni={sni}",                     # SNI: knny.dpdns.org
        f"fp={vless_config['fingerprint']}",
        "insecure=1",
        "allowInsecure=1",
        f"type={vless_config['network']}",
        f"host={host_domain}",            # 伪装域名: knny.dpdns.org
        f"path={path}"
    ]
    
    return f"{vless_url}?{'&'.join(params)}#{description}"

def get_unique_nodes(nodes):
    """去重节点，基于address"""
    seen = set()
    unique_nodes = []
    
    for node in nodes:
        if not node:
            continue
            
        # 提取address部分用于去重
        try:
            # 格式: vless://uuid@address:port?...#
            node_url = node.split('#')[0]
            node_base = node_url.split('@')[1].split('?')[0]
            address = node_base.split(':')[0]
            
            if address not in seen:
                seen.add(address)
                unique_nodes.append(node)
            else:
                print(f"跳过重复地址: {address}")
        except Exception as e:
            print(f"解析节点失败: {e}")
            unique_nodes.append(node)  # 如果解析失败，保留节点
    
    return unique_nodes

def main():
    print("=" * 60)
    print("Cloudflare优选IP节点生成器")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print("=" * 60)
    
    config = load_config()
    api_config = config['api_config']
    vless_config = config['vless_config']
    
    print(f"\n配置信息:")
    print(f"  UUID: {vless_config['uuid'][:8]}...")
    print(f"  Address: 使用API获取的IP/域名")
    print(f"  Host: {vless_config['domain']}")
    print(f"  SNI: {vless_config.get('sni', vless_config['domain'])}")
    print(f"  Port: {vless_config['port']}")
    print(f"  Path: {vless_config['path']}")
    
    nodes = []
    
    # 获取综合排名前20的IP
    print(f"\n1. 获取综合排名前20的IP...")
    top20_data = fetch_api(api_config['top20_url'])
    if top20_data and top20_data.get("code") == 0:
        good_ips = top20_data.get("data", {}).get("good", [])
        print(f"   找到 {len(good_ips)} 个综合优选IP")
        
        for idx, ip_data in enumerate(good_ips[:20]):
            if isinstance(ip_data, dict) and "ip" in ip_data:
                vless_url = generate_vless_url(ip_data, "top20", idx)
                if vless_url:
                    nodes.append(vless_url)
                    # 显示地址和描述
                    address = get_ip_or_host(ip_data)
                    print(f"     {idx+1:2d}. {address}")
    
    # 获取运营商优选IP
    print(f"\n2. 获取运营商优选IP...")
    isp_data = fetch_api(api_config['isp_url'])
    if isp_data and isp_data.get("code") == 0:
        isp_ips = isp_data.get("data", {})
        
        # 电信线路
        ct_ips = isp_ips.get("CT", [])
        if ct_ips:
            print(f"   电信线路: {len(ct_ips)} 个IP")
            for idx, ip_data in enumerate(ct_ips[:5]):
                vless_url = generate_vless_url(ip_data, "CT", idx)
                if vless_url:
                    nodes.append(vless_url)
                    address = get_ip_or_host(ip_data)
                    print(f"     {idx+1:2d}. {address}")
        
        # 联通线路
        cu_ips = isp_ips.get("CU", [])
        if cu_ips:
            print(f"   联通线路: {len(cu_ips)} 个IP")
            for idx, ip_data in enumerate(cu_ips[:5]):
                vless_url = generate_vless_url(ip_data, "CU", idx)
                if vless_url:
                    nodes.append(vless_url)
                    address = get_ip_or_host(ip_data)
                    print(f"     {idx+1:2d}. {address}")
        
        # 移动线路
        cm_ips = isp_ips.get("CM", [])
        if cm_ips:
            print(f"   移动线路: {len(cm_ips)} 个IP")
            for idx, ip_data in enumerate(cm_ips[:5]):
                vless_url = generate_vless_url(ip_data, "CM", idx)
                if vless_url:
                    nodes.append(vless_url)
                    address = get_ip_or_host(ip_data)
                    print(f"     {idx+1:2d}. {address}")
        
        # AllAvg线路
        all_avg_ips = isp_ips.get("AllAvg", [])
        if all_avg_ips:
            print(f"   全网优选: {len(all_avg_ips)} 个IP")
            for idx, ip_data in enumerate(all_avg_ips[:5]):
                vless_url = generate_vless_url(ip_data, "AllAvg", idx)
                if vless_url:
                    nodes.append(vless_url)
                    address = get_ip_or_host(ip_data)
                    print(f"     {idx+1:2d}. {address}")
    
    # 去重
    unique_nodes = get_unique_nodes(nodes)
    print(f"\n3. 节点去重:")
    print(f"   原始节点数: {len(nodes)}")
    print(f"   去重后节点数: {len(unique_nodes)}")
    
    # 按运营商分类显示统计
    print(f"\n4. 节点分类统计:")
    category_count = {}
    for node in unique_nodes:
        try:
            description = node.split('#')[1]
            category = description.split('-')[0]
            category_count[category] = category_count.get(category, 0) + 1
        except:
            pass
    
    for category, count in category_count.items():
        print(f"   {category}: {count} 个")
    
    # 生成明文节点文件
    print(f"\n5. 生成节点文件...")
    with open("YXNode", "w", encoding="utf-8") as f:
        # f.write(f"# Cloudflare优选IP节点\n")
        # f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n")
        # f.write(f"# 配置说明: address=API获取IP, host=knny.dpdns.org, sni=knny.dpdns.org\n")
        # f.write(f"# 总数: {len(unique_nodes)} 个\n")
        # f.write("#" * 70 + "\n\n")
        for node in unique_nodes:
            f.write(node + "\n")
            
    # 生成Clash配置文件
    with open("YXNode.yaml", "w", encoding="utf-8") as f:
        # f.write(f"# Cloudflare优选IP Clash配置\n")
        # f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n")
        # f.write(f"# 配置说明: address=API获取IP, host=knny.dpdns.org, sni=knny.dpdns.org\n")
        # f.write(f"# 节点总数: {len(unique_nodes)} 个\n")
        f.write("port: 7890\n")
        f.write("socks-port: 7891\n")
        f.write("allow-lan: true\n")
        f.write("mode: rule\n")
        f.write("log-level: info\n")
        f.write("external-controller: 127.0.0.1:9090\n")
        f.write("proxies:\n")
        
        for node in unique_nodes:
            try:
                # 从VLESS链接中提取信息
                parts = node.split("#")
                description = parts[1]
                base_url = parts[0].replace("vless://", "")
                
                uuid_server = base_url.split("@")[0]
                server_port = base_url.split("@")[1].split("?")[0]
                server = server_port.split(":")[0]
                
                # 解析参数
                params_str = node.split("?")[1].split("#")[0]
                params = dict(param.split("=") for param in params_str.split("&"))
                
                # 写入Clash配置
                f.write(f"  - name: '{description}'\n")
                f.write(f"    type: vless\n")
                f.write(f"    server: {server}\n")
                f.write(f"    port: {vless_config['port']}\n")
                f.write(f"    uuid: {uuid_server}\n")
                f.write(f"    cipher: none\n")
                f.write(f"    tls: true\n")
                f.write(f"    servername: {params.get('sni', vless_config.get('sni', 'knny.dpdns.org'))}\n")
                f.write(f"    network: {params.get('type', 'ws')}\n")
                f.write(f"    ws-opts:\n")
                f.write(f"      path: \"{params.get('path', vless_config['path'])}\"\n")
                f.write(f"      headers:\n")
                f.write(f"        Host: {params.get('host', vless_config['domain'])}\n")
                f.write(f"    udp: true\n\n")
            except Exception as e:
                print(f"生成Clash配置时跳过节点: {e}")
                continue
        
        # 添加代理组
        f.write("\nproxy-groups:\n")
        f.write("  - name: 🚀 自动选择\n")
        f.write("    type: url-test\n")
        f.write("    url: http://www.gstatic.com/generate_204\n")
        f.write("    interval: 300\n")
        f.write("    tolerance: 50\n")
        f.write("    lazy: true\n")
        f.write("    proxies:\n")
        
        for node in unique_nodes:
            try:
                description = node.split("#")[1]
                f.write(f"      - '{description}'\n")
            except:
                continue
        
        # 添加手动选择组 - 移除分隔线
        f.write("\n  - name: 📡 手动选择\n")
        f.write("    type: select\n")
        f.write("    proxies:\n")
        f.write("      - 🚀 自动选择\n")
        f.write("      - DIRECT\n")
        
        # 按分类添加节点 - 不要添加分隔线
        categories = ["综合优选", "电信优选", "联通优选", "移动优选", "全网优选"]
        
        # 先统计每个分类有哪些节点
        category_nodes = {}
        for node in unique_nodes:
            try:
                description = node.split("#")[1]
                for category in categories:
                    if description.startswith(category):
                        if category not in category_nodes:
                            category_nodes[category] = []
                        category_nodes[category].append(description)
                        break
            except:
                continue
        
        # 为每个有节点的分类添加代理组
        for category in categories:
            if category in category_nodes and category_nodes[category]:
                # 为该分类创建一个专门的代理组
                f.write(f"\n  - name: {category}\n")
                f.write("    type: select\n")
                f.write("    proxies:\n")
                # 添加该分类下的所有节点
                for node_name in category_nodes[category]:
                    f.write(f"      - '{node_name}'\n")
                
                # 在手动手动选择组中添加这个分类组
                f.seek(0, 2)  # 移动到文件末尾
                pos = f.tell()
                # 我们需要重新定位到手动选择组的位置添加这个分类组
                # 更简单的方法：我们可以在后面再添加
                # 先写到这里，稍后我们再调整
        
        # 重新定位到手动选择组添加分类组引用
        # 由于文件已经写入，我们需要重新组织生成逻辑
        # 这里提供修复方案：先生成所有代理组，再生成手动选择组
        
    # 由于上面的代码已经写到文件，我们需要重新组织
    # 下面是完整的修复方案

# 更好的解决方案：重新设计生成逻辑
def generate_clash_config(unique_nodes, vless_config):
    """生成Clash配置文件"""
    
    # 按分类组织节点
    categories = ["综合优选", "电信优选", "联通优选", "移动优选", "全网优选"]
    category_nodes = {}
    
    for node in unique_nodes:
        try:
            description = node.split("#")[1]
            for category in categories:
                if description.startswith(category):
                    if category not in category_nodes:
                        category_nodes[category] = []
                    category_nodes[category].append(description)
                    break
        except:
            continue
    
    with open("YXNode.yaml", "w", encoding="utf-8") as f:
        f.write("port: 7890\n")
        f.write("socks-port: 7891\n")
        f.write("allow-lan: true\n")
        f.write("mode: rule\n")
        f.write("log-level: info\n")
        f.write("external-controller: 127.0.0.1:9090\n")
        f.write("proxies:\n")
        
        for node in unique_nodes:
            try:
                parts = node.split("#")
                description = parts[1]
                base_url = parts[0].replace("vless://", "")
                
                uuid_server = base_url.split("@")[0]
                server_port = base_url.split("@")[1].split("?")[0]
                server = server_port.split(":")[0]
                
                params_str = node.split("?")[1].split("#")[0]
                params = dict(param.split("=") for param in params_str.split("&"))
                
                f.write(f"  - name: '{description}'\n")
                f.write(f"    type: vless\n")
                f.write(f"    server: {server}\n")
                f.write(f"    port: {vless_config['port']}\n")
                f.write(f"    uuid: {uuid_server}\n")
                f.write(f"    cipher: none\n")
                f.write(f"    tls: true\n")
                f.write(f"    servername: {params.get('sni', vless_config.get('sni', 'knny.dpdns.org'))}\n")
                f.write(f"    network: {params.get('type', 'ws')}\n")
                f.write(f"    ws-opts:\n")
                f.write(f"      path: \"{params.get('path', vless_config['path'])}\"\n")
                f.write(f"      headers:\n")
                f.write(f"        Host: {params.get('host', vless_config['domain'])}\n")
                f.write(f"    udp: true\n\n")
            except Exception as e:
                print(f"生成Clash配置时跳过节点: {e}")
                continue
        
        # 添加代理组
        f.write("\nproxy-groups:\n")
        
        # 1. 自动选择组
        f.write("  - name: 🚀 自动选择\n")
        f.write("    type: url-test\n")
        f.write("    url: http://www.gstatic.com/generate_204\n")
        f.write("    interval: 300\n")
        f.write("    tolerance: 50\n")
        f.write("    lazy: true\n")
        f.write("    proxies:\n")
        for node in unique_nodes:
            try:
                description = node.split("#")[1]
                f.write(f"      - '{description}'\n")
            except:
                continue
        
        # 2. 手动选择组 - 只包含自动选择和直连
        f.write("\n  - name: 📡 手动选择\n")
        f.write("    type: select\n")
        f.write("    proxies:\n")
        f.write("      - 🚀 自动选择\n")
        f.write("      - DIRECT\n")
        
        # 3. 为每个分类创建单独的代理组
        for category in categories:
            if category in category_nodes and category_nodes[category]:
                f.write(f"\n  - name: {category}\n")
                f.write("    type: select\n")
                f.write("    proxies:\n")
                for node_name in category_nodes[category]:
                    f.write(f"      - '{node_name}'\n")
                
                # 把这个分类组添加到手动选择组中
                # 我们需要重新定位到手动选择组的位置
                # 更简单的方法：我们先创建分类组，然后在手动选择组中引用
        
        # 4. 国外网站组
        f.write("\n  - name: 🌍 国外网站\n")
        f.write("    type: select\n")
        f.write("    proxies:\n")
        f.write("      - 🚀 自动选择\n")
        f.write("      - 📡 手动选择\n")
        for category in categories:
            if category in category_nodes and category_nodes[category]:
                f.write(f"      - {category}\n")
        f.write("      - DIRECT\n")
        
        # 5. 全局代理组
        f.write("\n  - name: 🎯 全局代理\n")
        f.write("    type: select\n")
        f.write("    proxies:\n")
        f.write("      - 🚀 自动选择\n")
        f.write("      - 📡 手动选择\n")
        for category in categories:
            if category in category_nodes and category_nodes[category]:
                f.write(f"      - {category}\n")
        f.write("      - DIRECT\n")
        
        # 添加规则
        f.write("\nrules:\n")
        f.write("  - DOMAIN-SUFFIX,openai.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,chat.openai.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,google.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,youtube.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,github.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,twitter.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,facebook.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,instagram.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,telegram.org,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,netflix.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,disneyplus.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,hulu.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,hbo.com,🌍 国外网站\n")
        f.write("  - DOMAIN-SUFFIX,cn,DIRECT\n")
        f.write("  - DOMAIN-KEYWORD,china,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,taobao.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,baidu.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,qq.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,163.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,sina.com.cn,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,weibo.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,zhihu.com,DIRECT\n")
        f.write("  - DOMAIN-SUFFIX,bilibili.com,DIRECT\n")
        f.write("  - IP-CIDR,10.0.0.0/8,DIRECT\n")
        f.write("  - IP-CIDR,172.16.0.0/12,DIRECT\n")
        f.write("  - IP-CIDR,192.168.0.0/16,DIRECT\n")
        f.write("  - IP-CIDR,127.0.0.0/8,DIRECT\n")
        f.write("  - GEOIP,LAN,DIRECT\n")
        f.write("  - GEOIP,CN,DIRECT\n")
        f.write("  - MATCH,🎯 全局代理\n")

# 然后在 main 函数中调用这个函数
def main():
    # ... 前面的代码保持不变，直到生成节点文件 ...
    
    # 生成明文节点文件
    print(f"\n5. 生成节点文件...")
    with open("YXNode", "w", encoding="utf-8") as f:
        for node in unique_nodes:
            f.write(node + "\n")
    
    # 使用新的函数生成Clash配置
    generate_clash_config(unique_nodes, vless_config)
    
    print(f"\n6. 文件生成完成:")
    print(f"   ✅ YXNode - {len(unique_nodes)} 个明文节点链接")
    print(f"   ✅ YXNode.yaml - Clash配置文件")
    print(f"\n节点配置说明:")
    print(f"   • Address: 使用API获取的实际IP或域名")
    print(f"   • Host: {vless_config['domain']}")
    print(f"   • SNI: {vless_config.get('sni', vless_config['domain'])}")
    print(f"   • Port: {vless_config['port']}")
    print(f"   • Path: {vless_config['path']}")
    print(f"\n节点名称格式: 运营商-序号-地址")
    print(f"示例: 综合优选-01-cf.130519.xyz")
    print("=" * 60)

if __name__ == "__main__":
    main()