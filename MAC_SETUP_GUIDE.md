# LinkedIn Scraper - Mac 完整使用手册

## 📋 目录
1. [首次安装](#首次安装)
2. [日常使用](#日常使用)
3. [故障排查](#故障排查)

---

## 首次安装

### Step 1: 安装 Homebrew (如果没有)

打开 Terminal（终端），运行：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: 安装 Python 3

```bash
brew install python3
```

验证安装：
```bash
python3 --version
# 应该显示 Python 3.x.x
```

### Step 3: 安装 Google Chrome

如果没有安装，从 https://www.google.com/chrome/ 下载安装

### Step 4: 安装 Cloudflare Tunnel (cloudflared)

```bash
brew install cloudflared
```

> ⚠️ **注意**: 我们使用 Cloudflare Tunnel 而不是 ngrok，因为它完全免费且无需注册账号。

### Step 5: 创建项目文件夹

```bash
# 创建文件夹
mkdir -p ~/linkedin-scraper
cd ~/linkedin-scraper
```

### Step 6: 下载项目文件

```bash
# 下载所有文件
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/linkedin_scraper.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/sheets_integration.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/scraper_server.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_server.sh
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_all.sh

# 设置执行权限
chmod +x start_server.sh start_all.sh
```

### Step 7: 安装 Python 依赖

```bash
pip3 install selenium gspread google-auth flask
```

### Step 8: 放置 Google 凭证文件

将你的 `credentials.json` 文件复制到 `~/linkedin-scraper/` 文件夹中：
```bash
# 如果文件在下载文件夹
cp ~/Downloads/credentials.json ~/linkedin-scraper/
```

### Step 9: 首次登录 LinkedIn

运行一次爬虫来登录 LinkedIn（会保存登录状态）：
```bash
cd ~/linkedin-scraper
python3 linkedin_scraper.py --days 7 --output test.json
```

这会打开 Chrome 浏览器，手动登录 LinkedIn，登录成功后等待爬虫完成。

---

## 日常使用

### 🚀 每次使用只需 3 步：

#### Step 1: 打开终端，启动服务

```bash
cd ~/linkedin-scraper
./start_all.sh
```

你会看到类似输出：
```
2024.01.15 10:30:00 INF |  https://random-words-here.trycloudflare.com
```

**复制这个 https://xxxxx.trycloudflare.com URL！**

#### Step 2: 更新 Google Apps Script (如果 URL 变了)

1. 打开你的 Google Sheet
2. 菜单：`Extensions` → `Apps Script`
3. 找到第 19 行：
```javascript
const SCRAPER_URL = "https://你的新URL.trycloudflare.com";
```
4. 替换为刚才复制的 URL
5. 按 `Cmd + S` 保存

#### Step 3: 从 Google Sheet 触发抓取

1. 回到 Google Sheet
2. 点击菜单：`LinkedIn Scraper` → `Fetch Last 30 Days`
3. 等待完成通知

#### 停止服务

在终端按 `Ctrl + C` 停止所有服务

---

## 故障排查

### 问题：Server Offline / <!DOCTYPE error

**原因**：Cloudflare Tunnel URL 过期了（每次重启会变）

**解决**：
1. 重启 `./start_all.sh`
2. 复制新的 trycloudflare.com URL
3. 更新 Google Apps Script 中的 URL

### 问题：Chrome 没有打开 / Selenium 错误

**原因**：ChromeDriver 版本不匹配

**解决**：
```bash
pip3 install --upgrade selenium
```

Selenium 4.x 会自动管理 ChromeDriver。

### 问题：LinkedIn 需要重新登录

**原因**：登录 session 过期

**解决**：
```bash
cd ~/linkedin-scraper
python3 linkedin_scraper.py --days 7 --output test.json
```
手动在打开的 Chrome 中登录。

### 问题：Google Sheets 权限错误

**原因**：Service Account 没有权限

**解决**：
1. 打开 Google Sheet
2. 点击 `Share`（分享）
3. 添加 service account email（在 credentials.json 中的 client_email）
4. 给予 `Editor`（编辑者）权限

### 问题：cloudflared 报错

**解决**：
```bash
# 重新安装
brew reinstall cloudflared
```

---

## 📁 文件结构

```
~/linkedin-scraper/
├── linkedin_scraper.py      # 核心爬虫
├── sheets_integration.py    # Google Sheets 集成
├── scraper_server.py        # Flask 服务器
├── start_server.sh          # 启动 Flask
├── start_all.sh             # 一键启动全部
└── credentials.json         # Google 服务账号凭证
```

---

## 💡 小贴士

1. **Cloudflare Tunnel 优势**：完全免费，无需注册账号，无使用限制
2. **后台运行**：可以用 `nohup ./start_all.sh &` 让服务在后台运行
3. **定时任务**：可以用 Mac 的 `cron` 或 `launchd` 设置定时自动运行

---

## 🆘 需要帮助？

如果遇到其他问题，检查：
1. 终端中的错误信息
2. Flask 服务器的日志输出
3. Google Apps Script 的执行日志（Apps Script 页面 → Executions）
