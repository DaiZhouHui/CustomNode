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

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Git

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/DaiZhouHui/CustomNode.git
cd CustomNode
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量（可选）
创建 `.env` 文件：
```
REPO_OWNER=your_username
REPO_NAME=your_repo
GITHUB_TOKEN=your_token_here
```

4. 生成索引
```bash
python generate-index.py
```

---

## 📁 文件结构

```
CustomNode/
├── generate-index.py          # 主生成脚本
├── index.html                 # 主索引页面（自动生成）
├── update-index.html          # 更新控制台（自动生成）
├── update-index.yml           # GitHub Actions工作流
├── requirements.txt           # Python依赖
├── .github/workflows/         # 工作流配置
│   └── update-index.yml
└── 其他节点文件              # 你的节点和配置文件
```

---

## ⚙️ 配置说明

### 环境变量
- `REPO_OWNER`: GitHub用户名（默认：DaiZhouHui）
- `REPO_NAME`: 仓库名称（默认：CustomNode）
- `GITHUB_TOKEN`: GitHub个人访问令牌（用于删除功能）

### GitHub Token权限
如需使用删除功能，Token需要以下权限：
- `repo`（完整仓库权限）
- 或至少 `public_repo`（公开仓库）

---

## 🔄 自动化更新

### GitHub Actions
项目配置了自动化工作流：
- **定时更新**: 每日UTC 02:00自动运行
- **手动触发**: 通过GitHub Actions页面或更新控制台
- **文件变更触发**: 非生成文件变化时自动更新

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
   - 检查Python版本 ≥ 3.8
   - 确保安装了所有依赖

2. **删除功能失效**
   - 确认GitHub Token有仓库写入权限
   - 检查Token是否过期

3. **页面显示异常**
   - 清空浏览器缓存
   - 检查网络连接，确保能加载Font Awesome

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