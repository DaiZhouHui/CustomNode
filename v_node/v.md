## 生成的文件说明

### 1. YXNode（无后缀文件）
- **格式**: 明文VLESS节点链接，每行一个
- **用途**: 可直接复制到V2RayN、Clash等客户端
- **内容示例**:
  ```
  vless://471a8e64-7b21-4703-b1d1-45a221098459@cf.130519.xyz:443?encryption=none&security=tls&sni=knny.dpdns.org&fp=chrome&insecure=1&allowInsecure=1&type=ws&host=knny.dpdns.org&path=/?ed=2048#综合优选-01-cf.130519.xyz
  ```

### 2. YXNode.yaml
- **格式**: 完整的Clash配置文件
- **用途**: 可直接作为Clash订阅链接使用
- **包含内容**:
  - 所有节点配置
  - 代理组（自动选择、手动选择、流媒体等）
  - 路由规则（智能分流）
  - 基础Clash配置

## 文件使用方法

### 方法一：直接复制链接（YXNode文件）
1. 打开 `YXNode` 文件
2. 复制任意节点链接
3. 在V2RayN等客户端中粘贴导入

### 方法二：Clash订阅（YXNode.yaml文件）
1. **本地使用**:
   - 下载 `YXNode.yaml` 文件
   - 在Clash客户端中导入本地文件

2. **在线订阅**:
   - 获取GitHub上的文件原始链接
   - 例如: `https://raw.githubusercontent.com/你的用户名/仓库名/main/YXNode.yaml`
   - 在Clash客户端中添加此订阅链接

## 节点配置详解

### 地址规则：
- **address**: 使用API返回的实际IP或域名
- **host**: 固定的伪装域名 `knny.dpdns.org`
- **sni**: 固定的SNI `knny.dpdns.org`
- **port**: 443
- **path**: `/?ed=2048`

### 节点名称格式：
```
运营商-序号-完整地址
```

示例：
```
综合优选-01-cf.130519.xyz
电信优选-01-172.64.41.110
联通优选-01-172.67.72.3
```

## Clash配置文件结构

`YXNode.yaml` 包含：

1. **基础配置**：
   - 监听端口: 7890 (HTTP) / 7891 (SOCKS5)
   - 运行模式: Rule (规则模式)
   - 日志级别: info

2. **代理组**：
   - 🚀 自动选择：自动测试选择最快节点
   - 📡 手动选择：按运营商分类手动选择
   - 🌍 国外网站：国外网站代理
   - 🎥 流媒体服务：Netflix/Disney+等流媒体
   - 🎯 全局代理：最终匹配规则

3. **路由规则**：
   - 国内网站直连
   - 流媒体服务特殊代理
   - 国外网站代理
   - 最终规则匹配

## 域名要求

确保 `knny.dpdns.org` 域名：
1. 已添加到Cloudflare
2. 开启代理（橙色云状态）
3. 可以解析到任意IP

## 更新频率

- **自动更新**: 每天北京时间07:40
- **手动触发**: 在GitHub Actions页面手动运行
- **配置更新**: 修改配置文件后自动触发
```

## 5. 优化总结

### 生成的两个文件：
1. **YXNode**（无后缀）
   - 纯文本文件，每行一个VLESS链接
   - 可直接复制导入各种客户端
   - 便于查看和分享

2. **YXNode.yaml**
   - 完整的Clash配置文件
   - 包含所有节点、代理组和规则
   - 可直接作为订阅链接使用