# FOFA 爬虫工具

FOFA 爬虫工具是一个基于 FOFA 平台的自动化信息收集工具，用于根据指定的查询条件获取 IP 和端口数据。

## 项目结构

```
f_node/
├── config-example.json     # 配置文件示例
├── config.json            # 实际配置文件（被 .gitignore 忽略）
├── crawler.py             # 主爬虫脚本
├── tool.py                # 配置工具
├── verify_config.py       # 配置验证工具
├── f_node.md              # 项目文档
├── .gitignore             # Git 忽略规则
└── requirements.txt       # Python 依赖
```

## 功能特性

- **多平台兼容**：支持在不同环境下运行（包括 GitHub Actions）
- **智能查询**：支持复杂的 FOFA 查询语法
- **数据提取**：自动从 FOFA 结果页面提取 IP 和端口信息
- **配置管理**：灵活的配置系统，支持多种设置
- **IP 过滤**：内置过滤机制，排除常见无效 IP 地址
- **调试支持**：提供调试模式以帮助排查问题

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件

首先复制配置文件示例：

```bash
cp config-example.json config.json
```

然后编辑 [config.json](file:///c/Users/KNNY/Desktop/Code/CustomNode/f_node/config.json) 文件，填入你的 FOFA Cookie 和查询条件。

#### 配置项说明：

- `cookies`: FOFA 平台的登录 Cookie（必须）
- `query_string`: FOFA 查询语句
- `settings.timeout`: 请求超时时间（秒）
- [max_results](file:///c/Users/KNNY/Desktop/Code/CustomNode/f_node/crawler.py#L590-L590): 最大返回结果数量
- `filter_common_ips`: 是否过滤常见 IP（如 192.168.x.x 等）
- `debug_mode`: 是否开启调试模式

### 3. 获取 FOFA Cookie

1. 访问 FOFA 网站并登录
2. 按 F12 打开浏览器开发者工具
3. 切换到 Network（网络）标签页
4. 刷新页面
5. 复制任意请求的 Cookie 值并填入配置文件

## 使用方法

### 1. 使用配置工具

运行配置工具来交互式地修改配置：

```bash
python tool.py
```

### 2. 运行爬虫

直接运行爬虫脚本：

```bash
python crawler.py
```

或者使用自定义配置文件：

```bash
python crawler.py --config /path/to/config.json
```

其他可用参数：
- `--output`: 指定输出文件路径
- `--debug`: 启用调试模式

### 3. 验证配置

在运行爬虫前验证配置：

```bash
python verify_config.py
```

## 输出结果

爬虫运行后会将结果保存在 `results/` 目录下的 CSV 文件中，包含两列：
- `IP地址`: 提取到的 IP 地址
- `端口`: 对应的端口号

## 高级功能

### 环境变量支持

在 CI/CD 环境（如 GitHub Actions）中，可以通过环境变量设置配置：

- `FOFA_COOKIE`: FOFA Cookie
- `FOFA_QUERY`: 查询语句
- `FOFA_DEBUG`: 是否启用调试模式

### GitHub Actions 集成

该工具专为 GitHub Actions 优化，可以在定时任务中自动运行并收集数据。

## 注意事项

- 请确保遵守 FOFA 平台的使用条款
- 不要在公共仓库中提交包含敏感信息的 [config.json](file:///c/Users/KNNY/Desktop/Code/CustomNode/f_node/config.json) 文件
- 合理设置请求频率，避免对目标服务器造成压力
- Cookie 可能会过期，需要定期更新

## 故障排除

1. **无法获取数据**: 检查 Cookie 是否有效，查询语法是否正确
2. **请求被拒绝**: 可能是 IP 被限制，稍后再试
3. **超时**: 调整 [settings.timeout](file:///c/Users/KNNY/Desktop/Code/CustomNode/f_node/crawler.py#L589-L589) 参数

如遇问题，可以启用调试模式查看详细日志。