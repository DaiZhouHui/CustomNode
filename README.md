# 🚀 CustomNode 仓库及节点索引生成器

一个自动生成节点文件索引页面的工具，支持文件扫描、分组展示、复制链接和删除管理，内置GitHub Actions自动化更新。![Update Index](https://github.com/DaiZhouHui/CustomNode/actions/workflows/update-index.yml/badge.svg)

---
默认示例 GitHub Pages 发布页（基于默认仓库设置 `DaiZhouHui/CustomNode`）：

- 网页首页：https://daizhouhui.github.io/CustomNode/

节点仓库（基于默认仓库设置 `DaiZhouHui/CustomNode`）：

- 仓库首页 ：https://github.com/DaiZhouHui/CustomNode

节点生成页 一个Web工具，用于将CSV数据转换为Vless节点链接，生成Base64订阅，并与GitHub仓库同步。

- 节点生成网站首页 ：https://daizhouhui.github.io/NodeWeb


默认三个节点订阅文件（Pages 版本示例）：

- 主要订阅（Pages）: https://daizhouhui.github.io/CustomNode/MainNode
- 优选订阅（Pages）: https://daizhouhui.github.io/CustomNode/OptimalNode
- 明文订阅（Pages）: https://daizhouhui.github.io/CustomNode/PlainNode


默认三个节点订阅文件（Raw 版本示例）：

- 主要订阅（Raw）: https://raw.githubusercontent.com/DaiZhouHui/CustomNode/main/MainNode
- 优选订阅（Raw）: https://raw.githubusercontent.com/DaiZhouHui/CustomNode/main/OptimalNode
- 明文订阅（Raw）: https://raw.githubusercontent.com/DaiZhouHui/CustomNode/main/PlainNode


## ✨ 核心功能

- 📂 **智能文件扫描** - 自动配对节点文件与配置文件（.yaml）
- 🎨 **现代美观界面** - 响应式设计，支持移动端，按日期分组展示
- 📋 **一键复制链接** - 快速复制Pages/Raw链接，支持批量操作
- 🗑️ **安全删除功能** - 通过GitHub API安全删除文件
- 🔄 **自动更新系统** - 支持定时更新和手动触发
- 📱 **移动端优化** - 完善的响应式布局
- 🕷️ **FOFA爬虫** - 自动从FOFA平台抓取可用节点信息
- ⚡ **VLESS节点生成** - 自动生成V2Ray/VLESS协议节点配置
- 📁 **双重节点系统** - 支持f_node和v_node两种节点生成方式

---

## 📁 项目结构

```
CustomNode/
├── f_node/                    # FOFA节点相关文件夹
│   ├── config-example.json    # FOFA配置示例文件
│   ├── config.json            # FOFA配置文件（需要自行创建）
│   ├── crawler.py             # FOFA爬虫脚本，用于抓取节点
│   └── tool.py                # FOFA配置工具，用于生成配置
├── v_node/                    # VLESS节点相关文件夹
│   ├── config.json            # VLESS节点配置文件
│   ├── generate_nodes.py      # VLESS节点生成脚本
│   └── v.md                   # VLESS节点说明文档
├── scripts/                   # 系统脚本文件夹
│   ├── generate-index.py      # 主索引页面生成脚本
│   └── update-index.js        # 索引更新辅助脚本
├── .github/
│   └── workflows/
│       └── generate-nodes.yml # GitHub Actions工作流配置（节点生成）
│       └── update-index.yml   # GitHub Actions工作流配置（索引更新）
├── *.yaml                     # 节点配置文件（Clash格式）
├── files_info.json            # 文件信息JSON文件（自动生成）
├── index.html                 # 主索引页面（自动生成）
├── update-index.html          # 更新控制台（自动生成）
└── README.md                  # 项目说明文档
```

---

## 🛠️ 功能详解

### FOFA节点系统 ([f_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/f_node))

FOFA节点系统用于从FOFA平台获取可用的代理节点信息。

#### 配置FOFA账户
1. 在FOFA网站注册账户并获得查询权限
2. 登录后获取浏览器请求中的Cookie信息
3. 在[f_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/f_node)目录下创建[config.json](file:///c:/Users/KNNY/Desktop/Code/CustomNode/f_node/config.json)文件：

```json
{
  "cookies": "your_fofa_cookies_here",
  "query_string": "asn!=\\"13335\\" && server==\\"cloudflare\\" && region=\\"HK\\" && port=\\"443\\"",
  "settings": {
    "timeout": 30,
    "max_results": 50,
    "debug_mode": false,
    "filter_common_ips": true
  }
}
```

#### 使用FOFA工具
运行FOFA配置工具来管理配置：
```bash
python f_node/tool.py
```

#### 运行FOFA爬虫
运行爬虫脚本来获取节点信息：
```bash
python f_node/crawler.py
```

### VLESS节点系统 ([v_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/v_node))

VLESS节点系统用于生成V2Ray/VLESS协议的节点配置。

#### 配置VLESS参数
在[v_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/v_node)目录下配置[config.json](file:///c:/Users/KNNY/Desktop/Code/CustomNode/v_node/config.json)文件：

```json
{
  "vless_config": {
    "uuid": "your_uuid_here",
    "domain": "your_domain_here",
    "port": 443,
    "path": "/?ed=2048",
    "encryption": "none",
    "security": "tls",
    "sni": "your_sni_here",
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
```

#### 生成VLESS节点
运行VLESS节点生成脚本：
```bash
python v_node/generate_nodes.py
```

### 索引生成系统

索引生成系统用于创建网页界面，方便管理和访问节点文件。

#### 手动生成索引
```bash
python scripts/generate-index.py
```

#### 配置说明

##### 环境变量
- `REPO_OWNER`: GitHub用户名（默认：DaiZhouHui）
- `REPO_NAME`: 仓库名称（默认：CustomNode）
- `GITHUB_TOKEN`: GitHub个人访问令牌（用于删除功能）

##### GitHub Token权限
如需使用删除功能，Token需要以下权限：
- `repo`（完整仓库权限）
- 或至少 `public_repo`（公开仓库）

---

## 🔄 自动化更新

### GitHub Actions
项目配置了多种自动化工作流：

- **定时更新**: 每日UTC 02:00自动运行`update-index.yml`
- **节点生成**: 定期运行`generate-nodes.yml`生成新节点
- **手动触发**: 通过GitHub Actions页面或更新控制台
- **文件变更触发**: 非生成文件变化时自动更新索引

### 工作流配置
- `generate-nodes.yml`: 用于定期生成节点配置
- `update-index.yml`: 用于更新索引页面

### 手动触发更新
1. 访问 `update-index.html`
2. 点击"快速更新"、"完整更新"或"强制更新"
3. 查看实时日志

---

## 📱 使用技巧

### 快速操作
- **搜索**: 页面顶部搜索框，支持实时筛选
- **复制全部**: 一键复制所有Pages或Raw链接
- **删除文件**: 点击"操作"显示删除按钮，需要GitHub Token
- **键盘快捷键**:
  - `Ctrl/Cmd + F`: 聚焦搜索
  - `Ctrl/Cmd + P`: 复制全部Pages
  - `Ctrl/Cmd + R`: 复制全部Raw
  - `Esc`: 清空搜索/关闭弹窗

### 移动端适配
- 平板：隐藏状态列
- 手机：进一步隐藏时间列，垂直布局操作按钮
- 触摸优化：增大点击区域

---

## 🔧 故障排除

### 常见问题
1. **无法生成索引**
   - 检查Python版本 ≥ 3.11
   - 确保安装了所有依赖

2. **删除功能失效**
   - 确认GitHub Token有仓库写入权限
   - 检查Token是否过期

3. **页面显示异常**
   - 清空浏览器缓存
   - 检查网络连接，确保能加载Font Awesome

4. **节点生成失败**
   - 检查[f_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/f_node)和[v_node](file:///c:/Users/KNNY/Desktop/Code/CustomNode/v_node)文件夹中的配置文件
   - 确保生成脚本具有正确的权限

5. **FOFA爬虫无法运行**
   - 确认FOFA账户有效并有足够的查询积分
   - 检查[config.json](file:///c:/Users/KNNY/Desktop/Code/CustomNode/f_node/config.json)中的Cookie是否正确
   - 确认查询语句语法正确

6. **VLESS节点生成失败**
   - 检查[v_node/config.json](file:///c:/Users/KNNY/Desktop/Code/CustomNode/v_node/config.json)配置是否正确
   - 确认API接口可以正常访问

### 日志查看
- 更新过程日志在 `update-index.html`
- 详细错误信息在浏览器控制台（F12）

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！
- 报告Bug
- 提出新功能建议
- 改进文档
- 提交代码改进

---

## 🔗 相关链接

- 📂 [GitHub仓库](https://github.com/DaiZhouHui/CustomNode)
- 📖 [GitHub Pages页面](https://daizhouhui.github.io/CustomNode/)
- ⚙️ [GitHub Actions状态](https://github.com/DaiZhouHui/CustomNode/actions)

---

**提示**: 首次使用建议先运行测试更新，确保所有功能正常。如遇问题，请查看控制台日志或提交Issue。
