// 备用JavaScript版本，需要Node.js环境
const fs = require('fs');
const path = require('path');
const { Octokit } = require('@octokit/rest');

// 配置
const REPO_OWNER = 'DaiZhouHui';
const REPO_NAME = 'CustomNode';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

// 这里省略具体实现，原理与Python版本相同
// 建议使用Python版本，因为GitHub Actions默认支持Python