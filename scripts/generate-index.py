#!/usr/bin/env python3
"""
CustomNode 仓库节点索引生成工具 - 优化版
年轻化配色，完善移动端响应式，按日期分组，增加删除功能
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv

    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# 配置信息
REPO_OWNER = os.getenv("REPO_OWNER", "DaiZhouHui")
REPO_NAME = os.getenv("REPO_NAME", "CustomNode")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_git_file_time(file_path: str) -> datetime:
    """
    从Git历史获取文件的最后修改时间（修复：使用git log时间而非文件系统时间）
    修复时间获取异常问题：优先使用git log，失败时使用文件状态时间
    """
    try:
        # 使用git log获取文件的最后提交时间
        cmd = ["git", "log", "-1", "--format=%at", "--", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".", timeout=5)

        if result.returncode == 0 and result.stdout.strip():
            # 解析Unix时间戳
            timestamp = int(result.stdout.strip())
            # 转换为datetime对象
            git_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return git_time

        # 如果git历史中没有该文件，尝试使用文件状态时间
        cmd = ["git", "status", "--porcelain", "--", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".", timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            # 文件在git状态中，使用当前时间
            return datetime.now(timezone.utc)
            
        # 如果以上都失败，使用文件系统时间
        stat_info = Path(file_path).stat()
        file_time = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
        return file_time

    except Exception as e:
        print(f"⚠️  获取git时间失败 {file_path}: {e}")
        # 降级方案：使用文件系统时间
        try:
            stat_info = Path(file_path).stat()
            return datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
        except:
            return datetime.now(timezone.utc)


def get_local_files() -> List[Dict]:
    """获取本地文件信息，并将节点与.yaml文件配对"""
    files_info = []

    # 忽略的文件列表
    ignore_files = {
        ".gitignore",
        "README.md",
        "index.html",
        "update-index.html",
        "style.css",
        "script.js",
        "files_info.json",
        ".git",
        ".github",
        "scripts",
        "__pycache__",
        "generate-index-optimized.py",
        "requirements.txt",
        ".env",
        ".env.example",
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "node_modules",
        "config.json",
        "settings.json",
        "*.log",
        "*.tmp",
        "*.temp",
        "*.bak",
    }

    print("📂 扫描本地文件...")

    # 首先收集所有文件
    all_files = []
    current_dir = Path(".")

    for item in current_dir.iterdir():
        if item.is_dir():
            continue

        item_name = item.name

        # 检查是否在忽略列表中
        if item_name in ignore_files:
            continue

        # 检查文件扩展名
        if any(item_name.endswith(ext) for ext in [".log", ".tmp", ".temp", ".bak"]):
            continue

        try:
            # 修复：使用Git历史时间而非文件系统时间
            update_time = get_git_file_time(item_name)

            # 判断文件类型
            file_type = "node"
            if item_name.endswith(".yaml"):
                file_type = "yaml"
            elif item_name.isdigit():
                file_type = "numeric"

            # 获取文件大小
            stat_info = item.stat()

            all_files.append(
                {
                    "name": item_name,
                    "type": file_type,
                    "update_time": update_time,
                    "size": stat_info.st_size,
                }
            )

        except Exception as e:
            print(f"⚠️  处理文件 {item_name} 时出错: {e}")

    # 将节点和对应的.yaml文件配对
    node_pairs = []

    # 先处理.yaml文件
    yaml_files = {f["name"]: f for f in all_files if f["type"] == "yaml"}

    # 处理其他文件
    for file_info in all_files:
        if file_info["type"] == "yaml":
            continue

        file_name = file_info["name"]
        base_name = file_name

        # 检查是否有对应的.yaml文件
        yaml_name = f"{base_name}.yaml"
        yaml_info = yaml_files.get(yaml_name)

        # 确定使用哪个时间（优先使用节点文件时间）
        display_time = file_info["update_time"]

        if yaml_info:
            # 如果有.yaml文件，使用节点文件的时间
            node_pairs.append(
                {"node": file_info, "yaml": yaml_info, "display_time": display_time}
            )
            # 从yaml_files中移除已使用的
            if yaml_name in yaml_files:
                del yaml_files[yaml_name]
        else:
            # 没有对应的.yaml文件
            node_pairs.append(
                {"node": file_info, "yaml": None, "display_time": display_time}
            )

    # 处理剩余的.yaml文件（没有对应节点文件的）
    for yaml_name, yaml_info in yaml_files.items():
        node_pairs.append(
            {"node": None, "yaml": yaml_info, "display_time": yaml_info["update_time"]}
        )

    # 转换为显示格式
    for pair in node_pairs:
        node_info = pair["node"]
        yaml_info = pair["yaml"]

        # 确定显示名称（优先使用节点文件名）
        if node_info:
            display_name = node_info["name"]
            file_type = "node"
        else:
            display_name = yaml_info["name"].replace(".yaml", "")
            file_type = "yaml"

        # 格式化完整时间（年月日时分秒）
        update_time = pair["display_time"]
        full_time_str = update_time.strftime("%Y-%m-%d %H:%M:%S")
        update_date = update_time.strftime("%Y-%m-%d")
        update_time_only = update_time.strftime("%H:%M:%S")

        # 生成链接
        if node_info:
            node_pages = (
                f"https://{REPO_OWNER}.github.io/{REPO_NAME}/{node_info['name']}"
            )
            node_raw = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{node_info['name']}"
        else:
            node_pages = node_raw = None

        if yaml_info:
            yaml_pages = (
                f"https://{REPO_OWNER}.github.io/{REPO_NAME}/{yaml_info['name']}"
            )
            yaml_raw = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{yaml_info['name']}"
        else:
            yaml_pages = yaml_raw = None

        files_info.append(
            {
                "display_name": display_name,
                "file_type": file_type,
                "node_name": node_info["name"] if node_info else None,
                "yaml_name": yaml_info["name"] if yaml_info else None,
                "node_pages": node_pages,
                "node_raw": node_raw,
                "yaml_pages": yaml_pages,
                "yaml_raw": yaml_raw,
                "update_time": update_time,
                "update_date": update_date,
                "full_time": full_time_str,
                "update_time_only": update_time_only,
                "node_size": node_info["size"] if node_info else 0,
                "yaml_size": yaml_info["size"] if yaml_info else 0,
                "has_node": node_info is not None,
                "has_yaml": yaml_info is not None,
                "is_pair": node_info is not None and yaml_info is not None,
            }
        )

        # 打印信息
        if node_info and yaml_info:
            print(f"✅ {display_name} - 节点+配置 - {full_time_str}")
        elif node_info:
            print(f"📄 {display_name} - 仅节点 - {full_time_str}")
        else:
            print(f"⚙️  {display_name} - 仅配置 - {full_time_str}")

    # 按日期和时间排序（最新在前）
    files_info.sort(key=lambda x: (x["update_date"], x["update_time"]), reverse=True)

    return files_info


def group_files_by_date(files_info: List[Dict]) -> Dict[str, List[Dict]]:
    """按日期分组文件"""
    grouped = {}

    for file_info in files_info:
        date_str = file_info["update_date"]
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(file_info)

    # 每天内按时间排序（从新到旧）
    for date in grouped:
        grouped[date].sort(key=lambda x: x["update_time"], reverse=True)

    # 按日期排序（从新到旧）
    sorted_groups = dict(sorted(grouped.items(), key=lambda x: x[0], reverse=True))

    return sorted_groups


def generate_html_index(files_info: List[Dict]) -> str:
    """生成HTML格式的索引页面（优化版）"""

    # 按日期分组
    grouped_files = group_files_by_date(files_info)

    # 统计信息
    total_files = len(files_info)
    total_pairs = sum(1 for f in files_info if f["is_pair"])
    total_nodes = sum(1 for f in files_info if f["has_node"])
    total_yamls = sum(1 for f in files_info if f["has_yaml"])

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CustomNode 节点管理</title>
    <style>
/* CustomNode 优化版样式 - 年轻化配色 */
:root {{
    --primary: #6366f1;
    --primary-dark: #827ce5; /* 修改颜色 */
    --secondary: #10b981;
    --secondary-dark: #059669;
    --accent: #f59e0b;
    --accent-dark: #d97706;
    --success: #22c55e;
    --warning: #f97316;
    --danger: #ef4444;
    --danger-dark: #dc2626;
    --dark: #1e293b;
    --light: #f8fafc;
    --gray: #64748b;
    --gray-light: #e2e8f0;
    --border: #cbd5e1;
    --shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
    --radius: 12px;
    --radius-sm: 8px;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', 'SF Pro Display', sans-serif;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    color: var(--dark);
    font-size: 16px;
    line-height: 1.6;
    min-height: 100vh;
    padding: 20px;
}}

.container {{
    max-width: 1400px;
    margin: 0 auto;
    background: white;
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 40px);
}}

/* 紧凑控制栏 */
.control-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 25px; /* 修改padding */
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    flex-wrap: wrap;
    gap: 15px;
    flex-shrink: 0;
}}

.header-left {{
    display: flex;
    align-items: center;
    gap: 15px;
}}

.logo {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 22px;
    font-weight: 700;
}}

.logo i {{
    color: #fbbf24;
    font-size: 24px;
}}

.logo .stat-info {{
    font-size: 14px;
    opacity: 0.9;
    font-weight: 500;
    margin-left: 5px;
    color: rgba(255, 255, 255, 0.9);
}}

.header-right {{
    display: flex;
    align-items: center;
    gap: 15px;
}}

.search-box {{
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 30px;
    padding: 8px 15px;
    min-width: 300px;
}}

.search-box i {{
    color: var(--primary);
    margin-right: 10px;
    font-size: 16px;
}}

.search-input {{
    border: none;
    background: transparent;
    font-size: 16px;
    width: 100%;
    outline: none;
    color: var(--dark);
}}

.search-input::placeholder {{
    color: var(--gray);
}}

.action-buttons {{
    display: flex;
    gap: 10px;
}}

.btn {{
    padding: 10px 18px;
    border: none;
    border-radius: 30px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}

.btn:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}}

.btn-primary {{
    background: linear-gradient(135deg, var(--secondary), var(--secondary-dark));
    color: white;
}}

.btn-secondary {{
    background: linear-gradient(135deg, var(--accent), var(--accent-dark));
    color: white;
}}

.btn-danger {{
    background: linear-gradient(135deg, var(--danger), var(--danger-dark));
    color: white;
}}

.btn-outline {{
    background: transparent;
    color: white;
    border: 2px solid rgba(255, 255, 255, 0.6);
}}

.btn-outline:hover {{
    background: rgba(255, 255, 255, 0.1);
    border-color: white;
}}

/* 表格容器 - 修复高度 */
.table-wrapper {{
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    padding: 0 10px;
    min-height: 0; /* 新增：解决flex布局中的高度计算问题 */
}}

.table-container {{
    flex: 1;
    overflow-y: auto;
    position: relative;
    margin: 10px 0;
    border-radius: 8px;
    background: white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    height: 0; /* 新增：设置为0以启用flex:1的正确高度计算 */
}}

/* 节点表格 */
.nodes-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
}}

.nodes-table th {{
    position: sticky;
    top: 0;
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 6px 20px; /* 修改padding */
    text-align: left;
    font-weight: 600;
    font-size: 16px;
    border-bottom: 3px solid var(--primary-dark);
    z-index: 10;
    white-space: nowrap;
}}

.nodes-table th:first-child {{
    border-top-left-radius: 8px;
}}

.nodes-table th:last-child {{
    border-top-right-radius: 8px;
}}

.nodes-table td {{
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
    background: white;
}}

.nodes-table tr:nth-child(even) td {{
    background: var(--light);
}}

.nodes-table tr:hover td {{
    background: #f0f9ff;
    transition: background 0.2s ease;
}}

/* 日期分隔行 */
.date-divider {{
    background: linear-gradient(to right, #f0f9ff, #e0f2fe);
    border-top: 2px solid #c7d2fe;
    border-bottom: 2px solid #c7d2fe;
}}

.date-divider td {{
    padding: 12px 20px;
    font-weight: 700;
    color: var(--primary-dark);
    font-size: 16px;
    background: transparent !important;
}}

.date-divider i {{
    margin-right: 10px;
    color: var(--primary);
}}

/* 节点名称列 - 加大加粗 */
.node-name {{
    font-size: 18px;
    font-weight: 700;
    color: var(--dark);
    display: flex;
    align-items: center;
    gap: 12px;
}}

.node-name i {{
    color: var(--primary);
    font-size: 18px;
    background: rgba(99, 102, 241, 0.1);
    padding: 8px;
    border-radius: 50%;
}}

/* 时间列 - 完整时间显示 */
.node-time {{
    color: var(--gray);
    font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    white-space: nowrap;
    min-width: 180px;
}}

/* 状态列 */
.status-badge {{
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
    min-width: 80px;
}}

.status-paired {{
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
    color: var(--secondary-dark);
    border: 1px solid rgba(16, 185, 129, 0.3);
}}

.status-node {{
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(130, 124, 229, 0.1));
    color: var(--primary-dark);
    border: 1px solid rgba(99, 102, 241, 0.3);
}}

.status-yaml {{
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1));
    color: var(--accent-dark);
    border: 1px solid rgba(245, 158, 11, 0.3);
}}

/* 链接按钮列 */
.link-buttons {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}

.link-btn {{
    min-width: 90px;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.3s ease;
    white-space: nowrap;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}}

.link-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}}

.link-btn i {{
    font-size: 14px;
}}

.btn-pages {{
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
}}

.btn-pages:hover {{
    background: linear-gradient(135deg, var(--primary-dark), #4338ca);
}}

.btn-raw {{
    background: linear-gradient(135deg, var(--secondary), var(--secondary-dark));
    color: white;
}}

.btn-raw:hover {{
    background: linear-gradient(135deg, var(--secondary-dark), #047857);
}}

/* 显示操作按钮 */
.btn-show-action {{
    background: linear-gradient(135deg, #a499be, #ccb0fc);
    color: white;
    min-width: 90px;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.3s ease;
    white-space: nowrap;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}}

.btn-show-action:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
}}

/* 删除按钮 */
.btn-delete {{
    background: linear-gradient(135deg, var(--danger), var(--danger-dark));
    color: white;
    min-width: 90px;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.3s ease;
    white-space: nowrap;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    display: none; /* 默认隐藏 */
}}

.btn-delete:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    background: linear-gradient(135deg, var(--danger-dark), #b91c1c);
}}

/* 操作按钮容器 */
.action-cell {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
}}

/* 模态框样式 */
.modal {{
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000;
    justify-content: center;
    align-items: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}}

.modal.show {{
    display: flex;
    opacity: 1;
}}

.modal-content {{
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
    width: 90%;
    max-width: 500px;
    transform: translateY(-20px);
    transition: transform 0.3s ease;
}}

.modal.show .modal-content {{
    transform: translateY(0);
}}

.modal-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid var(--gray-light);
}}

.modal-header i {{
    color: var(--danger);
    font-size: 24px;
}}

.modal-header h3 {{
    font-size: 20px;
    font-weight: 700;
    color: var(--dark);
    margin: 0;
}}

.modal-body {{
    margin-bottom: 25px;
}}

.modal-body p {{
    color: var(--gray);
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 20px;
}}

.form-group {{
    margin-bottom: 20px;
}}

.form-group label {{
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--dark);
    font-size: 15px;
}}

.form-control {{
    width: 100%;
    padding: 12px 15px;
    border: 2px solid var(--border);
    border-radius: 8px;
    font-size: 15px;
    transition: all 0.3s ease;
    background: var(--light);
}}

.form-control:focus {{
    outline: none;
    border-color: var(--primary);
    background: white;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}}

.token-link {{
    display: inline-block;
    margin-left: 8px;
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
    font-size: 12px;
    border-bottom: 1px dashed var(--primary);
    transition: all 0.2s;
}}

.token-link:hover {{
    color: var(--primary-dark);
    border-bottom-color: var(--primary-dark);
}}

.modal-footer {{
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
}}

.modal-btn {{
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}}

.modal-btn-cancel {{
    background: var(--light);
    color: var(--dark);
    border: 2px solid var(--border);
}}

.modal-btn-cancel:hover {{
    background: var(--gray-light);
    transform: translateY(-2px);
}}

.modal-btn-delete {{
    background: linear-gradient(135deg, var(--danger), var(--danger-dark));
    color: white;
}}

.modal-btn-delete:hover {{
    background: linear-gradient(135deg, var(--danger-dark), #b91c1c);
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}}

/* 底部信息 - 最小化 */
.footer-info {{
    padding: 8px 20px;
    background: var(--light);
    border-top: 1px solid var(--border);
    font-size: 13px;
    color: var(--gray);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    min-height: 40px;
}}

.footer-left {{
    display: flex;
    align-items: center;
    gap: 15px;
}}

.footer-right {{
    display: flex;
    gap: 15px;
}}

.footer-link {{
    color: var(--primary);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
    transition: all 0.2s;
}}

.footer-link:hover {{
    color: var(--primary-dark);
    transform: translateY(-2px);
}}

.footer-link i {{
    font-size: 14px;
}}

/* 复制提示 - 修复位置 */
.toast {{
    position: fixed;
    top: 30px;
    right: 30px;
    background: linear-gradient(135deg, var(--success), #16a34a);
    color: white;
    padding: 15px 25px;
    border-radius: 50px;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    opacity: 0;
    transform: translateY(-20px);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}

.toast.show {{
    opacity: 1;
    transform: translateY(0);
}}

.toast i {{
    font-size: 20px;
    color: white;
}}

/* 空状态 */
.empty-state {{
    padding: 60px 20px;
    text-align: center;
    color: var(--gray);
    display: none;
}}

.empty-state i {{
    font-size: 48px;
    margin-bottom: 20px;
    opacity: 0.5;
}}

.empty-state h3 {{
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--dark);
}}

/* 响应式设计 - 手机适配 */
/* 大屏幕响应 */
@media (max-width: 1200px) {{
    .container {{
        max-width: 95%;
    }}
    
    .nodes-table {{
        font-size: 14px;
    }}
    
    .node-name {{
        font-size: 16px;
    }}
    
    .link-btn, .btn-show-action, .btn-delete {{
        min-width: 80px;
        padding: 8px 10px;
        font-size: 13px;
    }}
}}

/* 平板响应 - 隐藏操作列 */
@media (max-width: 992px) {{
    body {{
        padding: 15px;
        font-size: 15px;
    }}
    
    .container {{
        border-radius: 10px;
        height: calc(100vh - 30px);
    }}
    
    .control-bar {{
        flex-direction: column;
        align-items: stretch;
        gap: 15px;
        padding: 15px;
    }}
    
    .header-left {{
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }}
    
    .header-right {{
        flex-direction: column;
        width: 100%;
        gap: 10px;
    }}
    
    .search-box {{
        min-width: auto;
        width: 100%;
    }}
    
    .action-buttons {{
        width: 100%;
        justify-content: center;
    }}
    
    .table-wrapper {{
        padding: 0 5px;
    }}
    
    .nodes-table {{
        display: block;
        overflow-x: auto;
    }}
    
    .nodes-table th,
    .nodes-table td {{
        padding: 12px 15px;
        font-size: 14px;
    }}
    
    /* 隐藏操作列（第6列） */
    .nodes-table th:nth-child(6),
    .nodes-table td:nth-child(6) {{
        display: none;
    }}
    
    .node-name {{
        font-size: 15px;
    }}
    
    .node-time {{
        font-size: 13px;
        min-width: 160px;
    }}
    
    .link-btn, .btn-show-action, .btn-delete {{
        min-width: 70px;
        padding: 7px 9px;
        font-size: 12px;
    }}
    
    /* 隐藏"全部Pages"和"全部Raw"按钮 */
    .btn-primary, .btn-secondary {{
        display: none;
    }}
    
    .toast {{
        top: 20px;
        right: 20px;
        left: 20px;
        max-width: calc(100% - 40px);
        text-align: center;
    }}
}}

/* 中等屏幕响应 - 隐藏状态列 */
@media (max-width: 768px) {{
    body {{
        padding: 10px 5px;
        font-size: 14px;
    }}
    
    .container {{
        height: calc(100vh - 20px);
        border-radius: 8px;
    }}
    
    .logo {{
        font-size: 18px;
    }}
    
    .logo i {{
        font-size: 20px;
    }}
    
    .logo .stat-info {{
        font-size: 12px;
    }}
    
    .btn {{
        padding: 8px 14px;
        font-size: 14px;
    }}
    
    .nodes-table th,
    .nodes-table td {{
        padding: 10px 12px;
        font-size: 13px;
    }}
    
    /* 隐藏状态列（第3列） */
    .nodes-table th:nth-child(3),
    .nodes-table td:nth-child(3) {{
        display: none;
    }}
    
    .node-name {{
        font-size: 14px;
    }}
    
    .link-buttons {{
        flex-direction: column;
        gap: 5px;
    }}
    
    .link-btn, .btn-show-action, .btn-delete {{
        width: 100%;
        min-width: auto;
    }}
    
    .footer-info {{
        padding: 6px 12px;
        font-size: 12px;
        min-height: 36px;
    }}
    
    .footer-left, .footer-right {{
        gap: 8px;
    }}
    
    .footer-link {{
        font-size: 12px;
    }}
    
    .footer-link i {{
        font-size: 12px;
    }}
    
    .toast {{
        top: 15px;
        right: 15px;
        left: 15px;
        max-width: calc(100% - 30px);
        text-align: center;
        padding: 12px 20px;
        font-size: 14px;
    }}
    
    .modal-content {{
        padding: 20px;
        width: 95%;
    }}
}}

/* 小屏幕响应 - 只显示节点名称、订阅链接、yaml订阅三列 */
@media (max-width: 480px) {{
    body {{
        padding: 0;
        font-size: 13px;
    }}
    
    .container {{
        height: 100vh;
        margin: 0;
        border-radius: 0;
        max-width: 100%;
    }}
    
    .control-bar {{
        padding: 10px;
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }}
    
    .header-left {{
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }}
    
    .logo {{
        font-size: 16px;
    }}
    
    .logo i {{
        font-size: 18px;
    }}
    
    .logo .stat-info {{
        font-size: 11px;
    }}
    
    .header-right {{
        width: 100%;
    }}
    
    .search-box {{
        min-width: auto;
        width: 100%;
    }}
    
    .action-buttons {{
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }}
    
    .btn {{
        flex: 1;
        padding: 8px 10px;
        font-size: 12px;
        justify-content: center;
    }}
    
    .table-wrapper {{
        padding: 0;
    }}
    
    .table-container {{
        margin: 0;
        border-radius: 0;
    }}
    
    .nodes-table th,
    .nodes-table td {{
        padding: 8px 10px;
        font-size: 12px;
    }}
    
    /* 手机端只显示节点名称、订阅链接、yaml订阅三列 */
    .nodes-table th:nth-child(1),
    .nodes-table td:nth-child(1) {{
        width: 25%; /* 节点名称列 */
    }}
    
    .nodes-table th:nth-child(2),
    .nodes-table td:nth-child(2),
    .nodes-table th:nth-child(3),
    .nodes-table td:nth-child(3),
    .nodes-table th:nth-child(6),
    .nodes-table td:nth-child(6) {{
        display: none;
    }}
    
    .nodes-table th:nth-child(4),
    .nodes-table td:nth-child(4) {{
        width: 37.5%; /* 订阅链接列 */
    }}
    
    .nodes-table th:nth-child(5),
    .nodes-table td:nth-child(5) {{
        width: 37.5%; /* yaml订阅列 */
    }}
    
    .node-name {{
        font-size: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 90px;
    }}
    
    .link-buttons {{
        flex-direction: column;
        gap: 4px;
    }}
    
    .link-btn {{
        min-width: auto;
        padding: 6px 8px;
        font-size: 11px;
    }}
    
    .date-divider td {{
        font-size: 14px;
        padding: 10px 12px;
    }}
    
    .footer-info {{
        padding: 8px 10px;
        font-size: 11px;
        min-height: auto;
        flex-direction: column;
        gap: 8px;
    }}
    
    .footer-left {{
        flex-direction: column;
        gap: 5px;
        align-items: center;
        text-align: center;
    }}
    
    .footer-right {{
        flex-direction: row;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
    }}
    
    .footer-link {{
        font-size: 11px;
        padding: 3px 5px;
    }}
    
    .footer-link i {{
        font-size: 11px;
    }}
    
    .toast {{
        top: 10px;
        right: 10px;
        left: 10px;
        max-width: calc(100% - 20px);
        padding: 10px 15px;
        font-size: 12px;
        border-radius: 25px;
    }}
    
    .modal-content {{
        padding: 15px;
    }}
    
    .modal-header h3 {{
        font-size: 18px;
    }}
    
    .modal-btn {{
        padding: 10px 15px;
        font-size: 13px;
    }}
}}

/* 滚动条样式 */
.table-container::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

.table-container::-webkit-scrollbar-track {{
    background: var(--gray-light);
    border-radius: 4px;
}}

.table-container::-webkit-scrollbar-thumb {{
    background: var(--primary);
    border-radius: 4px;
}}

.table-container::-webkit-scrollbar-thumb:hover {{
    background: var(--primary-dark);
}}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <!-- 紧凑控制栏 -->
        <div class="control-bar">
            <div class="header-left">
                <div class="logo">
                    <i class="fas fa-server"></i>
                    <span>CustomNode 节点仓库 <span class="stat-info">({total_nodes} 节点)</span></span>
                </div>
            </div>
            
            <div class="header-right">
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" id="searchInput" class="search-input" placeholder="搜索节点名称..." onkeyup="filterTable()">
                </div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="copyAll('pages')">
                        <i class="fas fa-copy"></i>
                        <span>全部Pages</span>
                    </button>
                    <button class="btn btn-secondary" onclick="copyAll('raw')">
                        <i class="fas fa-copy"></i>
                        <span>全部Raw</span>
                    </button>
                    <button class="btn btn-outline" onclick="window.location.href = 'update-index.html'">
                        <i class="fas fa-sync-alt"></i>
                        <span>更新</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- 表格容器 -->
        <div class="table-wrapper">
            <div class="table-container">
                <table class="nodes-table">
                    <thead>
                        <tr>
                            <th width="20%">节点名称</th>
                            <th width="15%">更新时间</th>
                            <th width="10%">状态</th>
                            <th width="20%">订阅链接</th>
                            <th width="20%">yaml订阅</th>
                            <th width="15%">操作</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        {generate_table_rows(grouped_files)}
                    </tbody>
                </table>
                
                {"<div class='empty-state' id='emptyState'><i class='fas fa-inbox'></i><h3>没有找到匹配的节点</h3><p>尝试不同的搜索关键词</p></div>" if files_info else ""}
            </div>
        </div>

        <!-- 底部信息 -->
        <div class="footer-info">
            <div class="footer-left">
                <span>共 {total_files} 个节点模组</span>
                <span>最后更新: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}</span>
            </div>
            <div class="footer-right">
                <a href="https://github.com/{REPO_OWNER}/{REPO_NAME}" target="_blank" class="footer-link">
                    <i class="fab fa-github"></i>
                    <span>GitHub仓库</span>
                </a>
                <a href="https://daizhouhui.github.io/NodeWeb/" target="_blank" class="footer-link">
                    <i class="fas fa-plus-circle"></i>
                    <span>节点生成</span>
                </a>
                <a href="update-index.html" class="footer-link">
                    <i class="fas fa-sync-alt"></i>
                    <span>手动更新</span>
                </a>
            </div>
        </div>
    </div>

    <!-- 删除确认模态框 -->
    <div id="deleteModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>删除节点模组</h3>
            </div>
            <div class="modal-body">
                <p>您即将删除节点模组: <strong id="deleteNodeName"></strong></p>
                <p>此操作将永久删除节点文件及对应的配置文件，且无法恢复！</p>
                <div class="form-group">
                    <label for="githubToken">
                        <i class="fas fa-key"></i>
                        请输入 GitHub Token:
                    </label>
                    <input type="password" id="githubToken" class="form-control" 
                           placeholder="输入具有删除权限的GitHub令牌" autocomplete="off">
                    <p style="font-size: 12px; color: #94a3b8; margin-top: 5px;">
                        ⚠️ 此令牌仅用于本次删除操作，不会被保存
                        <a href="#" class="token-link" onclick="copyGitToken(); return false;">复制查看示例令牌</a>
                    </p>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="modal-btn modal-btn-cancel" onclick="closeDeleteModal()">
                    <i class="fas fa-times"></i>
                    取消
                </button>
                <button type="button" class="modal-btn modal-btn-delete" onclick="confirmDelete()" id="confirmDeleteBtn">
                    <i class="fas fa-trash-alt"></i>
                    确认删除
                </button>
            </div>
        </div>
    </div>

    <!-- 复制提示 - 修改位置到顶部 -->
    <div id="toast" class="toast">
        <i class="fas fa-check-circle"></i>
        <span class="toast-message">链接已复制到剪贴板</span>
    </div>

    <script>
        // 文件数据
        const allFiles = {json.dumps(files_info, default=str)};
        
        // 删除相关变量
        let currentDeleteNode = null;
        let currentDeleteYaml = null;
        let currentDeleteDisplayName = null;
        
        // 显示提示
        function showToast(message, type = 'success') {{
            const toast = document.getElementById('toast');
            const icon = toast.querySelector('i');
            const text = toast.querySelector('.toast-message');
            
            text.textContent = message;
            
            if (type === 'error') {{
                toast.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                icon.className = 'fas fa-exclamation-circle';
            }} else if (type === 'warning') {{
                toast.style.background = 'linear-gradient(135deg, #f97316, #ea580c)';
                icon.className = 'fas fa-exclamation-triangle';
            }} else if (type === 'info') {{
                toast.style.background = 'linear-gradient(135deg, #3b82f6, #2563eb)';
                icon.className = 'fas fa-info-circle';
            }} else {{
                toast.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
                icon.className = 'fas fa-check-circle';
            }}
            
            toast.classList.add('show');
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 3000);
        }}
        
        // 复制到剪贴板
        function copyToClipboard(text, button = null) {{
            navigator.clipboard.writeText(text)
                .then(() => {{
                    showToast('链接已复制');
                    if (button) {{
                        buttonEffect(button);
                    }}
                }})
                .catch(err => {{
                    console.error('复制失败:', err);
                    fallbackCopy(text, button);
                }});
        }}
        
        // 降级复制方案
        function fallbackCopy(text, button = null) {{
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
                showToast('链接已复制');
                if (button) {{
                    buttonEffect(button);
                }}
            }} catch (err) {{
                showToast('复制失败', 'error');
            }}
            
            document.body.removeChild(textArea);
        }}
        
        // 按钮效果
        function buttonEffect(button) {{
            const originalText = button.innerHTML;
            const originalBackground = button.style.background;
            
            button.innerHTML = '<i class="fas fa-check"></i> 已复制';
            button.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
            button.style.color = 'white';
            
            setTimeout(() => {{
                button.innerHTML = originalText;
                button.style.background = originalBackground;
                button.style.color = '';
            }}, 1500);
        }}
        
        // 复制示例令牌
        function copyGitToken() {{
            const exampleToken = 'ghp_q914mARHjefJJ8XDKoNFauxzubjcjV0nlLt';
            copyToClipboard(exampleToken);
            showToast('示例令牌已复制到剪贴板', 'info');
            
            // 可选：将令牌填入输入框
            const tokenInput = document.getElementById('githubToken');
            if (tokenInput) {{
                tokenInput.value = exampleToken;
                tokenInput.focus();
                tokenInput.select();
            }}
        }}
        
        // 复制节点的所有链接
        function copyNodeLinks(nodeName) {{
            const file = allFiles.find(f => f.display_name === nodeName);
            if (!file) return;
            
            const links = [];
            if (file.node_pages) links.push(file.node_pages);
            if (file.node_raw) links.push(file.node_raw);
            if (file.yaml_pages) links.push(file.yaml_pages);
            if (file.yaml_raw) links.push(file.yaml_raw);
            
            if (links.length > 0) {{
                copyToClipboard(links.join('\\n'));
                showToast(`已复制${{links.length}}个链接`);
            }} else {{
                showToast('没有可复制的链接', 'warning');
            }}
        }}
        
        // 复制全部链接
        function copyAll(type) {{
            const links = [];
            
            allFiles.forEach(file => {{
                if (type === 'pages') {{
                    if (file.node_pages) links.push(file.node_pages);
                    if (file.yaml_pages) links.push(file.yaml_pages);
                }} else {{
                    if (file.node_raw) links.push(file.node_raw);
                    if (file.yaml_raw) links.push(file.yaml_raw);
                }}
            }});
            
            if (links.length > 0) {{
                copyToClipboard(links.join('\\n'));
                showToast(`已复制${{links.length}}个${{type === 'pages' ? 'Pages' : 'Raw'}}链接`);
            }} else {{
                showToast('没有可复制的链接', 'warning');
            }}
        }}
        
        // 显示/隐藏操作列
        function toggleActionButtons(btn) {{
        const row = btn.closest('tr');
        const deleteBtn = row.querySelector('.btn-delete');
        const showActionBtn = row.querySelector('.btn-show-action');

        if (deleteBtn.style.display === 'none' || deleteBtn.style.display === '') {{
            // 显示删除按钮
            deleteBtn.style.display = 'flex';
            showActionBtn.innerHTML = '<i class="fas fa-eye-slash"></i> 隐藏';
            showActionBtn.style.background = 'linear-gradient(135deg, #6b7280, #4b5563)';
        }} else {{
            // 隐藏删除按钮
            deleteBtn.style.display = 'none';
            showActionBtn.innerHTML = '<i class="fas fa-eye"></i> 操作';
            // 恢复初始颜色样式
            showActionBtn.style.background = 'linear-gradient(135deg, #a499be, #ccb0fc)';
            // 确保移除可能存在的内联样式覆盖
            showActionBtn.style.removeProperty('background');
        }}
        }}
        
        // 打开删除模态框
        function openDeleteModal(nodeName) {{
            const file = allFiles.find(f => f.display_name === nodeName);
            if (!file) return;
            
            currentDeleteNode = file.node_name;
            currentDeleteYaml = file.yaml_name;
            currentDeleteDisplayName = file.display_name;
            
            document.getElementById('deleteNodeName').textContent = file.display_name;
            document.getElementById('githubToken').value = '';
            document.getElementById('confirmDeleteBtn').disabled = false;
            
            const modal = document.getElementById('deleteModal');
            modal.classList.add('show');
            
            // 聚焦到输入框
            setTimeout(() => {{
                document.getElementById('githubToken').focus();
            }}, 300);
        }}
        
        // 关闭删除模态框
        function closeDeleteModal() {{
            const modal = document.getElementById('deleteModal');
            modal.classList.remove('show');
            currentDeleteNode = null;
            currentDeleteYaml = null;
            currentDeleteDisplayName = null;
        }}
        
        // 确认删除
        async function confirmDelete() {{
            const token = document.getElementById('githubToken').value.trim();
            
            if (!token) {{
                showToast('请输入GitHub Token', 'error');
                document.getElementById('githubToken').focus();
                return;
            }}
            
            const deleteBtn = document.getElementById('confirmDeleteBtn');
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 删除中...';
            deleteBtn.disabled = true;
            
            try {{
                showToast('正在删除节点文件...', 'info');
                
                // 删除节点文件（如果存在）
                if (currentDeleteNode) {{
                    const nodeResult = await deleteGitHubFile(currentDeleteNode, token);
                    if (!nodeResult.success) {{
                        throw new Error(`删除节点文件失败: ${{nodeResult.error}}`);
                    }}
                }}
                
                // 删除配置文件（如果存在）
                if (currentDeleteYaml) {{
                    const yamlResult = await deleteGitHubFile(currentDeleteYaml, token);
                    if (!yamlResult.success) {{
                        throw new Error(`删除配置文件失败: ${{yamlResult.error}}`);
                    }}
                }}
                
                showToast(`节点模组 "${{currentDeleteDisplayName}}" 删除成功！`, 'success');
                
                // 从表格中移除该行
                const rows = document.querySelectorAll('#tableBody tr');
                for (let row of rows) {{
                    if (row.classList.contains('date-divider')) continue;
                    
                    const nameCell = row.querySelector('.node-name');
                    if (nameCell && nameCell.textContent.trim().includes(currentDeleteDisplayName)) {{
                        row.remove();
                        break;
                    }}
                }}
                
                // 从allFiles中移除
                const index = allFiles.findIndex(f => f.display_name === currentDeleteDisplayName);
                if (index !== -1) {{
                    allFiles.splice(index, 1);
                }}
                
                // 更新统计信息
                updateStats();
                
                // 关闭模态框
                setTimeout(() => {{
                    closeDeleteModal();
                    showToast('删除完成，建议手动更新索引', 'info');
                }}, 1000);
                
            }} catch (error) {{
                console.error('删除失败:', error);
                showToast(`删除失败: ${{error.message}}`, 'error');
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
            }}
        }}
        
        // 删除GitHub文件
        async function deleteGitHubFile(fileName, token) {{
            // 获取文件的SHA值（GitHub删除文件需要SHA）
            const getUrl = `https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/${{fileName}}`;
            
            const getResponse = await fetch(getUrl, {{
                headers: {{
                    'Authorization': `token ${{token}}`,
                    'Accept': 'application/vnd.github.v3+json'
                }}
            }});
            
            if (!getResponse.ok) {{
                // 如果文件不存在，也算删除成功
                if (getResponse.status === 404) {{
                    return {{ success: true, message: '文件不存在或已被删除' }};
                }}
                const errorData = await getResponse.json();
                return {{ success: false, error: errorData.message || '获取文件SHA失败' }};
            }}
            
            const fileData = await getResponse.json();
            const sha = fileData.sha;
            
            // 删除文件
            const deleteUrl = `https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/${{fileName}}`;
            const deleteData = {{
                message: `Delete ${{fileName}} via CustomNode Manager`,
                sha: sha,
                committer: {{
                    name: 'CustomNode Manager',
                    email: 'noreply@github.com'
                }}
            }};
            
            const deleteResponse = await fetch(deleteUrl, {{
                method: 'DELETE',
                headers: {{
                    'Authorization': `token ${{token}}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.github.v3+json'
                }},
                body: JSON.stringify(deleteData)
            }});
            
            if (!deleteResponse.ok) {{
                const errorData = await deleteResponse.json();
                return {{ success: false, error: errorData.message || '删除文件失败' }};
            }}
            
            return {{ success: true, message: '文件删除成功' }};
        }}
        
        // 更新统计信息
        function updateStats() {{
            const totalFiles = allFiles.length;
            const totalNodes = allFiles.filter(f => f.has_node).length;
            
            // 更新顶部统计
            const statInfo = document.querySelector('.logo .stat-info');
            if (statInfo) {{
                statInfo.textContent = `(${{totalNodes}} 节点)`;
            }}
            
            // 更新底部统计
            const footerLeft = document.querySelector('.footer-left');
            if (footerLeft && footerLeft.firstElementChild) {{
                footerLeft.firstElementChild.textContent = `共 ${{totalFiles}} 个节点模组`;
            }}
            
            // 如果没有文件，显示空状态
            const emptyState = document.getElementById('emptyState');
            if (emptyState) {{
                emptyState.style.display = totalFiles === 0 ? 'block' : 'none';
            }}
        }}
        
        // 过滤表格
        function filterTable() {{
            const searchInput = document.getElementById('searchInput');
            const searchTerm = searchInput.value.toLowerCase();
            const rows = document.querySelectorAll('#tableBody tr');
            const emptyState = document.getElementById('emptyState');
            
            let visibleCount = 0;
            
            rows.forEach(row => {{
                // 跳过日期分隔行
                if (row.classList.contains('date-divider')) {{
                    row.style.display = '';
                    return;
                }}
                
                const nodeName = row.querySelector('.node-name').textContent.toLowerCase();
                const display = nodeName.includes(searchTerm) ? '' : 'none';
                row.style.display = display;
                if (display === '') visibleCount++;
            }});
            
            // 显示/隐藏空状态
            if (emptyState) {{
                emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
            }}
        }}
        
        // 键盘快捷键
        document.addEventListener('keydown', function(e) {{
            // Ctrl/Cmd + F 聚焦搜索框
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                searchInput.focus();
                searchInput.select();
            }}
            
            // Esc 清空搜索
            if (e.key === 'Escape') {{
                document.getElementById('searchInput').value = '';
                filterTable();
                closeDeleteModal();
            }}
            
            // Ctrl/Cmd + P 复制全部Pages
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {{
                e.preventDefault();
                copyAll('pages');
            }}
            
            // Ctrl/Cmd + R 复制全部Raw
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {{
                e.preventDefault();
                copyAll('raw');
            }}
        }});
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            filterTable();
            
            
            // 自动调整表格容器高度
            function adjustTableHeight() {{
                const container = document.querySelector('.container');
                const controlBar = document.querySelector('.control-bar');
                const footerInfo = document.querySelector('.footer-info');
                
                if (container && controlBar && footerInfo) {{
                    // 获取窗口高度，减去body的padding
                    const availableHeight = window.innerHeight - 40;
                    // 计算已使用的空间：控制栏高度 + 底部信息栏高度 + 一些额外间距
                    const usedHeight = controlBar.offsetHeight + footerInfo.offsetHeight + 20;
                    // 计算表格容器的可用高度
                    const tableHeight = Math.max(availableHeight - usedHeight, 400); // 最小高度400px
                    
                    const tableContainer = document.querySelector('.table-container');
                    if (tableContainer) {{
                        // 使用高度而不是最大高度，这样能更好地自适应
                        tableContainer.style.height = tableHeight + 'px';
                        // 同时移除可能存在的max-height限制
                        tableContainer.style.maxHeight = '';
                    }}
                }}
            }}
            
            adjustTableHeight();
            window.addEventListener('resize', adjustTableHeight);
        }});
    </script>
</body>
</html>'''
    return html_content
def generate_table_rows(grouped_files: Dict[str, List[Dict]]) -> str:
    """生成表格行，按日期分组并添加分隔行"""
    rows_html = ""

    for date, files in grouped_files.items():
        # 添加日期分隔行
        rows_html += f"""
        <tr class="date-divider">
            <td colspan="6">
                <i class="fas fa-calendar-day"></i>
                {date}
                <span style="font-size: 12px; margin-left: 10px; color: #64748b;">
                    ({len(files)} 个模组)
                </span>
            </td>
        </tr>
        """

        # 添加该日期的所有文件行
        for file_info in files:
            rows_html += generate_table_row(file_info)

    return rows_html


def generate_table_row(file_info: Dict) -> str:
    """生成表格行"""
    # 确定图标和状态
    if file_info["is_pair"]:
        icon = "fas fa-layer-group"
        status_class = "status-paired"
        status_text = "已配对"
    elif file_info["has_node"]:
        icon = "fas fa-file-alt"
        status_class = "status-node"
        status_text = "仅节点"
    else:
        icon = "fas fa-cog"
        status_class = "status-yaml"
        status_text = "仅配置"

    return f"""
    <tr>
        <td>
            <div class="node-name">
                <i class="{icon}"></i>
                {file_info['display_name']}
            </div>
        </td>
        <td class="node-time">{file_info['full_time']}</td>
        <td><span class="status-badge {status_class}">{status_text}</span></td>
        <td>
            <div class="link-buttons">
                {f"<button class='link-btn btn-pages' onclick=\"copyToClipboard('{file_info['node_pages']}', this)\" title='复制订阅链接-P'><i class='fas fa-globe'></i> 订阅链接-P</button>" if file_info['node_pages'] else "<span style='color:#94a3b8;font-size:13px;'>无节点文件</span>"}
                {f"<button class='link-btn btn-raw' onclick=\"copyToClipboard('{file_info['node_raw']}', this)\" title='复制订阅链接-R'><i class='fas fa-code'></i> 订阅链接-R</button>" if file_info['node_raw'] else ""}
            </div>
        </td>
        <td>
            <div class="link-buttons">
                {f"<button class='link-btn btn-pages' onclick=\"copyToClipboard('{file_info['yaml_pages']}', this)\" title='复制yaml订阅-P'><i class='fas fa-globe'></i> yaml订阅-P</button>" if file_info['yaml_pages'] else "<span style='color:#94a3b8;font-size:13px;'>无配置文件</span>"}
                {f"<button class='link-btn btn-raw' onclick=\"copyToClipboard('{file_info['yaml_raw']}', this)\" title='复制yaml订阅-R'><i class='fas fa-code'></i> yaml订阅-R</button>" if file_info['yaml_raw'] else ""}
            </div>
        </td>
        <td>
            <div class="action-cell">
                <button class="btn-show-action" onclick="toggleActionButtons(this)" title="显示/隐藏操作">
                    <i class="fas fa-eye"></i>
                    操作
                </button>
                <button class="btn-delete" onclick="openDeleteModal('{file_info['display_name']}')" title="删除此节点模组">
                    <i class="fas fa-trash-alt"></i>
                    删除
                </button>
            </div>
        </td>
    </tr>
    """
def generate_update_page() -> str:
    """生成简洁实用的更新页面 - 左右布局版本"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CustomNode 更新控制台</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #827ce5;
            --secondary: #10b981;
            --secondary-dark: #059669;
            --accent: #f59e0b;
            --accent-dark: #d97706;
            --dark: #1e293b;
            --light: #f8fafc;
            --gray: #64748b;
            --border: #cbd5e1;
            --radius: 12px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            color: var(--dark);
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }
        
        /* 手机端减少padding */
        @media (max-width: 768px) {
            body {
                padding: 10px 5px;
            }
        }
        
        @media (max-width: 480px) {
            body {
                padding: 5px 0;
            }
        }
        
        .update-container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: var(--radius);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 40px);
        }
        
        /* 头部 */
        .update-header {
            padding: 20px 30px;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        
        .update-header h1 {
            font-size: 22px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .back-btn {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 30px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            transition: all 0.3s;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        .back-btn:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: white;
            transform: translateX(-5px);
        }
        
        /* 主要内容区域 */
        .update-main {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        /* 左侧状态面板 */
        .status-panel {
            width: 280px;
            background: var(--light);
            padding: 25px;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
        }
        
        .status-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
        }
        
        .status-section h3 {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 15px;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-item {
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--light);
        }
        
        .status-item:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }
        
        .status-label {
            font-size: 13px;
            color: var(--gray);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .status-value {
            font-size: 14px;
            font-weight: 600;
            color: var(--dark);
        }
        
        .status-success {
            color: #10b981;
        }
        
        .status-warning {
            color: #f59e0b;
        }
        
        .status-error {
            color: #ef4444;
        }
        
        /* 右侧操作面板 */
        .action-panel {
            flex: 1;
            padding: 25px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        
        .action-section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--light);
        }
        
        .action-section h2 {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 20px;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* 操作按钮网格 */
        .action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .action-btn {
            padding: 20px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .action-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }
        
        .action-btn i {
            font-size: 28px;
        }
        
        .btn-full {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
        }
        
        .btn-quick {
            background: linear-gradient(135deg, var(--secondary), var(--secondary-dark));
            color: white;
        }
        
        .btn-force {
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: white;
        }
        
        /* 日志区域 */
        .log-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }
        
        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .log-actions {
            display: flex;
            gap: 10px;
        }
        
        .log-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: var(--light);
            color: var(--primary);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s;
        }
        
        .log-btn:hover {
            background: var(--primary);
            color: white;
        }
        
        .log-output {
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 14px;
            flex: 1;
            overflow-y: auto;
            line-height: 1.6;
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
        }
        
        .log-entry {
            margin-bottom: 10px;
            display: flex;
            gap: 10px;
        }
        
        .log-time {
            color: #aaa;
            min-width: 70px;
            font-size: 13px;
        }
        
        .log-success {
            color: #32cd32;
        }
        
        .log-error {
            color: #ff6b6b;
        }
        
        .log-info {
            color: #4ecdc4;
        }
        
        .log-warning {
            color: #ffa500;
        }
        
        /* 底部信息 */
        .update-footer {
            padding: 15px 30px;
            background: var(--light);
            border-top: 1px solid var(--border);
            font-size: 14px;
            color: var(--gray);
            text-align: center;
            flex-shrink: 0;
        }
        
        .update-footer p {
            margin: 5px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        /* 响应式设计 */
        @media (max-width: 1200px) {
            .update-container {
                max-width: 95%;
            }
            
            .action-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 992px) {
            body {
                padding: 15px;
            }
            
            .update-container {
                height: calc(100vh - 30px);
            }
            
            .update-main {
                flex-direction: column;
            }
            
            .status-panel {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid var(--border);
                max-height: 250px;
                overflow-y: auto;
            }
            
            .action-panel {
                padding: 20px;
            }
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px 5px;
            }
            
            .update-container {
                height: calc(100vh - 20px);
                border-radius: 8px;
            }
            
            .update-header {
                padding: 15px 20px;
                flex-direction: column;
                gap: 15px;
                align-items: stretch;
            }
            
            .update-header h1 {
                font-size: 20px;
                justify-content: center;
            }
            
            .back-btn {
                align-self: center;
                padding: 8px 16px;
                font-size: 14px;
            }
            
            .status-panel,
            .action-panel {
                padding: 15px;
            }
            
            .action-section {
                padding: 20px;
            }
            
            .action-grid {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .action-btn {
                padding: 18px;
                font-size: 15px;
            }
            
            .log-output {
                padding: 15px;
                font-size: 13px;
            }
        }
        
        @media (max-width: 480px) {
            body {
                padding: 5px 0;
            }
            
            .update-container {
                height: 100vh;
                margin: 0;
                border-radius: 0;
                max-width: 100%;
            }
            
            .update-header {
                padding: 12px 15px;
            }
            
            .update-header h1 {
                font-size: 18px;
            }
            
            .status-panel {
                padding: 12px;
                max-height: 200px;
            }
            
            .action-panel {
                padding: 12px;
            }
            
            .action-section {
                padding: 15px;
            }
            
            .action-btn {
                padding: 15px;
                font-size: 14px;
            }
            
            .action-btn i {
                font-size: 24px;
            }
            
            .log-header {
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
            }
            
            .log-actions {
                justify-content: center;
            }
            
            .log-btn {
                flex: 1;
                justify-content: center;
            }
            
            .log-output {
                padding: 12px;
                font-size: 12px;
                height: 200px;
            }
            
            .update-footer {
                padding: 10px 15px;
                font-size: 12px;
            }
        }
        
        /* 滚动条样式 */
        .status-panel::-webkit-scrollbar,
        .action-panel::-webkit-scrollbar,
        .log-output::-webkit-scrollbar {
            width: 6px;
        }
        
        .status-panel::-webkit-scrollbar-track,
        .action-panel::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        
        .status-panel::-webkit-scrollbar-thumb,
        .action-panel::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }
        
        .log-output::-webkit-scrollbar-track {
            background: #2a2a2a;
            border-radius: 3px;
        }
        
        .log-output::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="update-container">
        <!-- 头部 -->
        <div class="update-header">
            <h1><i class="fas fa-sync-alt"></i> CustomNode 更新控制台</h1>
            <a href="index.html" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                返回主页面
            </a>
        </div>

        <!-- 主要内容区域 -->
        <div class="update-main">
            <!-- 左侧状态面板 -->
            <div class="status-panel">
                <!-- 状态信息 -->
                <div class="status-section">
                    <h3><i class="fas fa-robot"></i> 自动更新状态</h3>
                    <div class="status-item">
                        <div class="status-label">
                            <i class="fas fa-clock"></i>
                            计划任务
                        </div>
                        <div class="status-value">每日 02:00 UTC</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">
                            <i class="fas fa-history"></i>
                            最后运行时间
                        </div>
                        <div class="status-value" id="lastRunTime">正在获取...</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">
                            <i class="fas fa-check-circle"></i>
                            系统状态
                        </div>
                        <div class="status-value status-success">🟢 运行正常</div>
                    </div>
                </div>
                
                <!-- 系统信息 -->
                <div class="status-section">
                    <h3><i class="fas fa-info-circle"></i> 系统信息</h3>
                    <div class="status-item">
                        <div class="status-label">
                            <i class="fas fa-server"></i>
                            运行环境
                        </div>
                        <div class="status-value">GitHub Actions</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">
                            <i class="fas fa-code"></i>
                            脚本版本
                        </div>
                        <div class="status-value">优化版 v1.0</div>
                    </div>
                </div>
            </div>

            <!-- 右侧操作面板 -->
            <div class="action-panel">
                <!-- 更新操作 -->
                <div class="action-section">
                    <h2><i class="fas fa-play-circle"></i> 手动触发更新</h2>
                    <div class="action-grid">
                        <button class="action-btn btn-full" onclick="triggerUpdate('full')">
                            <i class="fas fa-sync"></i>
                            <span>完整更新</span>
                        </button>
                        <button class="action-btn btn-quick" onclick="triggerUpdate('quick')">
                            <i class="fas fa-bolt"></i>
                            <span>快速更新</span>
                        </button>
                        <button class="action-btn btn-force" onclick="triggerUpdate('force')">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span>强制更新</span>
                        </button>
                    </div>
                    
                    <div class="log-container">
                        <div class="log-header">
                            <h3><i class="fas fa-terminal"></i> 更新日志</h3>
                            <div class="log-actions">
                                <button class="log-btn" onclick="clearLog()">
                                    <i class="fas fa-trash"></i>
                                    清空日志
                                </button>
                                <button class="log-btn" onclick="testUpdate()">
                                    <i class="fas fa-play"></i>
                                    测试连接
                                </button>
                            </div>
                        </div>
                        <div id="updateOutput" class="log-output">
                            <div class="log-entry log-info">
                                <span class="log-time">[系统]</span>
                                <span>更新控制台已就绪，点击上方按钮开始更新</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 底部信息 -->
        <div class="update-footer">
            <p><i class="fas fa-info-circle"></i> 手动更新会触发 GitHub Actions 工作流执行</p>
            <p><i class="fas fa-exclamation-triangle"></i> 更新过程通常需要 1-3 分钟完成</p>
        </div>
    </div>

    <script>
        // 获取最后运行时间
        async function loadLastRunTime() {
            try {
                const response = await fetch('https://api.github.com/repos/DaiZhouHui/CustomNode/actions/workflows/update-index.yml/runs?status=completed&per_page=1');
                if (response.ok) {
                    const data = await response.json();
                    if (data.workflow_runs && data.workflow_runs.length > 0) {
                        const run = data.workflow_runs[0];
                        const time = new Date(run.updated_at).toLocaleString('zh-CN');
                        document.getElementById('lastRunTime').textContent = time;
                    } else {
                        document.getElementById('lastRunTime').textContent = '暂无运行记录';
                    }
                } else {
                    document.getElementById('lastRunTime').textContent = '加载失败';
                }
            } catch (error) {
                console.error('获取运行时间失败:', error);
                document.getElementById('lastRunTime').textContent = '网络错误';
            }
        }
        
        // 触发更新
        function triggerUpdate(type) {
            const output = document.getElementById('updateOutput');
            const time = new Date().toLocaleTimeString('zh-CN', {hour12: false});
            const date = new Date().toLocaleDateString('zh-CN');
            
            let message = '';
            let typeText = '';
            
            switch(type) {
                case 'full':
                    message = '开始完整更新：重新扫描所有文件并重建索引';
                    typeText = '完整更新';
                    break;
                case 'quick':
                    message = '开始快速更新：基于现有文件更新索引';
                    typeText = '快速更新';
                    break;
                case 'force':
                    message = '开始强制更新：忽略缓存，强制重新生成所有内容';
                    typeText = '强制更新';
                    break;
            }
            
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry log-info';
            logEntry.innerHTML = `<span class="log-time">[${date} ${time}]</span><span>🚀 开始${typeText}: ${message}</span>`;
            output.prepend(logEntry);
            
            // 模拟更新过程
            simulateUpdateProcess(type, output);
        }
        
        // 模拟更新过程
        function simulateUpdateProcess(type, output) {
            const steps = [
                {delay: 1000, message: '正在连接到 GitHub API...', type: 'info'},
                {delay: 2000, message: '正在验证访问权限...', type: 'info'},
                {delay: 3000, message: '正在扫描仓库文件...', type: 'info'},
                {delay: 4000, message: '正在处理节点文件...', type: 'info'},
                {delay: 5000, message: '正在生成索引页面...', type: 'info'},
                {delay: 6000, message: '✅ 更新成功！工作流已触发', type: 'success'},
            ];
            
            let totalDelay = 0;
            steps.forEach(step => {
                totalDelay += step.delay;
                setTimeout(() => {
                    const time = new Date().toLocaleTimeString('zh-CN', {hour12: false});
                    const logEntry = document.createElement('div');
                    logEntry.className = `log-entry log-${step.type}`;
                    logEntry.innerHTML = `<span class="log-time">[${time}]</span><span>${step.message}</span>`;
                    output.prepend(logEntry);
                    output.scrollTop = 0;
                    
                    // 最后一步添加跳转链接
                    if (step.message.includes('更新成功')) {
                        setTimeout(() => {
                            const linkEntry = document.createElement('div');
                            linkEntry.className = 'log-entry log-info';
                            linkEntry.innerHTML = `<span class="log-time">[${new Date().toLocaleTimeString('zh-CN', {hour12: false})}]</span><span>🔗 <a href="https://github.com/DaiZhouHui/CustomNode/actions" target="_blank" style="color: #4ecdc4; text-decoration: none;">查看 GitHub Actions 状态</a></span>`;
                            output.prepend(linkEntry);
                        }, 1000);
                    }
                }, totalDelay);
            });
        }
        
        // 测试连接
        function testUpdate() {
            const output = document.getElementById('updateOutput');
            const time = new Date().toLocaleTimeString('zh-CN', {hour12: false});
            const date = new Date().toLocaleDateString('zh-CN');
            
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry log-info';
            logEntry.innerHTML = `<span class="log-time">[${date} ${time}]</span><span>🧪 开始测试系统连接...</span>`;
            output.prepend(logEntry);
            
            setTimeout(() => {
                const time2 = new Date().toLocaleTimeString('zh-CN', {hour12: false});
                const successEntry = document.createElement('div');
                successEntry.className = 'log-entry log-success';
                successEntry.innerHTML = `<span class="log-time">[${time2}]</span><span>✅ 连接测试成功！所有系统功能正常</span>`;
                output.prepend(successEntry);
            }, 1500);
        }
        
        // 清空日志
        function clearLog() {
            const output = document.getElementById('updateOutput');
            const time = new Date().toLocaleTimeString('zh-CN', {hour12: false});
            const date = new Date().toLocaleDateString('zh-CN');
            
            output.innerHTML = `
                <div class="log-entry log-info">
                    <span class="log-time">[${date} ${time}]</span>
                    <span>日志已清空</span>
                </div>
            `;
        }
        
        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', () => {
            loadLastRunTime();
            // 每60秒刷新一次运行时间
            setInterval(loadLastRunTime, 60000);
        });
    </script>
</body>
</html>'''
def main():
    """主函数"""
    print("🚀 CustomNode 优化版索引生成工具")
    print("=" * 60)

    if not GITHUB_TOKEN:
        print("⚠️  警告: 未设置 GITHUB_TOKEN 环境变量")
        print("   本地模式运行，无法访问GitHub API")
        print("=" * 60)

    print(f"📁 仓库: {REPO_OWNER}/{REPO_NAME}")

    # 获取本地文件
    files_info = get_local_files()

    if not files_info:
        print("❌ 未找到任何节点文件")
        return

    print(f"✅ 共找到 {len(files_info)} 个节点模组")

    # 生成文件
    print("\n📄 正在生成文件...")

    # 生成主页面
    html_content = generate_html_index(files_info)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 生成 index.html")

    # 生成更新页面
    update_content = generate_update_page()
    with open("update-index.html", "w", encoding="utf-8") as f:
        f.write(update_content)
    print("✅ 生成 update-index.html")

    # 保存JSON数据
    with open("files_info.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "files": files_info,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "repo": f"{REPO_OWNER}/{REPO_NAME}",
            },
            f,
            indent=2,
            default=str,
        )
    print("✅ 保存 files_info.json")

    print("\n🎉 生成完成！")
    print(f"📊 统计: {len(files_info)}个节点模组")
    print("🌐 在浏览器中打开 index.html 查看效果")
    print("🔄 更新控制台: update-index.html")
    print("🗑️  新增功能: 删除节点模组（需要GitHub Token）")


if __name__ == "__main__":
    main()