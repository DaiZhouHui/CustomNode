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
    vless_url = f"vless://{uuid}@{address}:{port}"
    params = [
        f"encryption={vless_config['encryption']}",
        f"security={vless_config['security']}",
        f"sni={sni}",
        f"fp={vless_config['fingerprint']}",
        "insecure=1",
        "allowInsecure=1",
        f"type={vless_config['network']}",
        f"host={host_domain}",
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
            node_url = node.split('#')[0]
            node_base = node_url.split('@')[1].split('?')[0]
            address = node_base.split(':')[0]
            
            if address not in seen:
                seen.add(address)
                unique_nodes.append(node)
        except:
            unique_nodes.append(node)
    
    return unique_nodes

def generate_clash_config(unique_nodes, config):
    """生成Clash配置文件"""
    vless_config = config['vless_config']
    
    clash_config = f"""# Cloudflare优选IP Clash配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)
# 配置说明: address=API获取IP, host=knny.dpdns.org, sni=knny.dpdns.org
# 节点总数: {len(unique_nodes)} 个

port: 7890
socks-port: 7891
allow-lan: true
mode: Rule
log-level: info
external-controller: 127.0.0.1:9090
secret: ""
ipv6: false

proxies:
"""
    
    # 添加所有节点
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
            
            clash_config += f"""  - name: '{description}'
    type: vless
    server: {server}
    port: {vless_config['port']}
    uuid: {uuid_server}
    cipher: none
    tls: true
    servername: {params.get('sni', vless_config.get('sni', 'knny.dpdns.org'))}
    network: {params.get('type', 'ws')}
    ws-opts:
      path: "{params.get('path', vless_config['path'])}"
      headers:
        Host: {params.get('host', vless_config['domain'])}
    udp: true
"""
        except Exception as e:
            print(f"生成Clash节点时跳过: {e}")
            continue
    
    # 按运营商分类统计
    categories = ["综合优选", "电信优选", "联通优选", "移动优选", "全网优选"]
    
    # 添加代理组
    clash_config += """
proxy-groups:
  - name: 🚀 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    lazy: true
    proxies:
"""
    
    # 自动选择组包含所有节点
    for node in unique_nodes:
        try:
            description = node.split("#")[1]
            clash_config += f"      - '{description}'\n"
        except:
            continue
    
    # 添加手动选择组（按分类）
    clash_config += """
  - name: 📡 手动选择
    type: select
    proxies:
      - 🚀 自动选择
      - DIRECT
"""
    
    for category in categories:
        # 检查是否有该分类的节点
        has_nodes = False
        for node in unique_nodes:
            try:
                description = node.split("#")[1]
                if description.startswith(category):
                    has_nodes = True
                    break
            except:
                continue
        
        if has_nodes:
            clash_config += f"      - '--- {category} ---'\n"
            for node in unique_nodes:
                try:
                    description = node.split("#")[1]
                    if description.startswith(category):
                        clash_config += f"      - '{description}'\n"
                except:
                    continue
    
    # 添加规则组
    clash_config += """
  - name: 🌍 国外网站
    type: select
    proxies:
      - 🚀 自动选择
      - 📡 手动选择
      - DIRECT

  - name: 🎥 流媒体服务
    type: select
    proxies:
      - 🚀 自动选择
      - 📡 手动选择
      - DIRECT

  - name: 🎯 全局代理
    type: select
    proxies:
      - 🚀 自动选择
      - 📡 手动选择
      - DIRECT

rules:
  # 直连规则
  - DOMAIN-SUFFIX,cn,DIRECT
  - DOMAIN-SUFFIX,qq.com,DIRECT
  - DOMAIN-SUFFIX,baidu.com,DIRECT
  - DOMAIN-SUFFIX,taobao.com,DIRECT
  - DOMAIN-SUFFIX,jd.com,DIRECT
  - DOMAIN-SUFFIX,weibo.com,DIRECT
  - DOMAIN-SUFFIX,zhihu.com,DIRECT
  - DOMAIN-SUFFIX,bilibili.com,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT
  - IP-CIDR,192.168.0.0/16,DIRECT
  - IP-CIDR,10.0.0.0/8,DIRECT
  - IP-CIDR,172.16.0.0/12,DIRECT
  - GEOIP,CN,DIRECT
  
  # 流媒体规则
  - DOMAIN-SUFFIX,netflix.com,🎥 流媒体服务
  - DOMAIN-SUFFIX,netflix.net,🎥 流媒体服务
  - DOMAIN-SUFFIX,nflxvideo.net,🎥 流媒体服务
  - DOMAIN-SUFFIX,nflxext.com,🎥 流媒体服务
  - DOMAIN-SUFFIX,disneyplus.com,🎥 流媒体服务
  - DOMAIN-SUFFIX,disney-plus.net,🎥 流媒体服务
  - DOMAIN-SUFFIX,hulu.com,🎥 流媒体服务
  - DOMAIN-SUFFIX,huluim.com,🎥 流媒体服务
  - DOMAIN-SUFFIX,hulustream.com,🎥 流媒体服务
  
  # 国外网站
  - DOMAIN-SUFFIX,google.com,🌍 国外网站
  - DOMAIN-SUFFIX,gstatic.com,🌍 国外网站
  - DOMAIN-SUFFIX,youtube.com,🌍 国外网站
  - DOMAIN-SUFFIX,ytimg.com,🌍 国外网站
  - DOMAIN-SUFFIX,twitter.com,🌍 国外网站
  - DOMAIN-SUFFIX,twimg.com,🌍 国外网站
  - DOMAIN-SUFFIX,facebook.com,🌍 国外网站
  - DOMAIN-SUFFIX,instagram.com,🌍 国外网站
  - DOMAIN-SUFFIX,whatsapp.com,🌍 国外网站
  - DOMAIN-SUFFIX,telegram.org,🌍 国外网站
  - DOMAIN-SUFFIX,wikipedia.org,🌍 国外网站
  - DOMAIN-SUFFIX,openai.com,🌍 国外网站
  - DOMAIN-SUFFIX,chatgpt.com,🌍 国外网站
  
  # 最终规则
  - MATCH,🎯 全局代理
"""
    
    return clash_config

def main():
    print("=" * 70)
    print("Cloudflare优选IP节点生成器")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print("=" * 70)
    
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
        
        # 联通线路
        cu_ips = isp_ips.get("CU", [])
        if cu_ips:
            print(f"   联通线路: {len(cu_ips)} 个IP")
            for idx, ip_data in enumerate(cu_ips[:5]):
                vless_url = generate_vless_url(ip_data, "CU", idx)
                if vless_url:
                    nodes.append(vless_url)
        
        # 移动线路
        cm_ips = isp_ips.get("CM", [])
        if cm_ips:
            print(f"   移动线路: {len(cm_ips)} 个IP")
            for idx, ip_data in enumerate(cm_ips[:5]):
                vless_url = generate_vless_url(ip_data, "CM", idx)
                if vless_url:
                    nodes.append(vless_url)
        
        # AllAvg线路
        all_avg_ips = isp_ips.get("AllAvg", [])
        if all_avg_ips:
            print(f"   全网优选: {len(all_avg_ips)} 个IP")
            for idx, ip_data in enumerate(all_avg_ips[:5]):
                vless_url = generate_vless_url(ip_data, "AllAvg", idx)
                if vless_url:
                    nodes.append(vless_url)
    
    # 去重
    unique_nodes = get_unique_nodes(nodes)
    print(f"\n3. 节点去重:")
    print(f"   原始节点数: {len(nodes)}")
    print(f"   去重后节点数: {len(unique_nodes)}")
    
    # 按运营商分类统计
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
    
    # 生成明文节点文件（无后缀）- 直接生成在根目录
    print(f"\n5. 生成节点文件...")
    print(f"   将在仓库根目录生成文件:")
    print(f"   - YXNode (明文节点链接)")
    print(f"   - YXNode.yaml (Clash配置文件)")
    
    # 生成明文节点文件
    with open("YXNode", "w", encoding="utf-8") as f:
        f.write(f"# Cloudflare优选IP节点\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n")
        f.write(f"# 配置说明: address=API获取IP, host=knny.dpdns.org, sni=knny.dpdns.org\n")
        f.write(f"# 节点总数: {len(unique_nodes)} 个\n")
        f.write("#" * 70 + "\n\n")
        for node in unique_nodes:
            f.write(node + "\n")
    
    # 生成Clash配置文件
    clash_config = generate_clash_config(unique_nodes, config)
    with open("YXNode.yaml", "w", encoding="utf-8") as f:
        f.write(clash_config)
    
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
    print("=" * 70)
    
    # 检查文件是否生成成功
    if os.path.exists("YXNode") and os.path.exists("YXNode.yaml"):
        print(f"\n✅ 文件已成功生成在根目录")
        print(f"   YXNode 文件大小: {os.path.getsize('YXNode')} 字节")
        print(f"   YXNode.yaml 文件大小: {os.path.getsize('YXNode.yaml')} 字节")
    else:
        print(f"\n❌ 文件生成失败，请检查错误信息")

if __name__ == "__main__":
    main()