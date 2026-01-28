# LinkedIn Scraper - Windows 完整使用手册

## 📋 目录
1. [首次安装](#首次安装)
2. [日常使用](#日常使用)
3. [故障排查](#故障排查)

---

## 首次安装

### Step 1: 安装 Python 3

1. 访问 https://www.python.org/downloads/
2. 下载最新版本 Python 3.x
3. 运行安装程序，**勾选 "Add Python to PATH"**
4. 完成安装

验证安装（打开 CMD）：
```cmd
python --version
```
应该显示 `Python 3.x.x`

### Step 2: 安装 Google Chrome

如果没有安装，从 https://www.google.com/chrome/ 下载安装

### Step 3: 安装 Cloudflare Tunnel (cloudflared)

**方法一：使用 winget（推荐）**
```cmd
winget install Cloudflare.cloudflared
```

**方法二：手动下载**
1. 访问 https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. 下载 Windows 64-bit 版本
3. 将 `cloudflared.exe` 放到 `C:\Windows\` 或添加到 PATH

验证安装：
```cmd
cloudflared --version
```

### Step 4: 创建项目文件夹

```cmd
mkdir C:\linkedin-scraper
cd C:\linkedin-scraper
```

### Step 5: 下载项目文件

**方法一：使用 curl（Windows 10/11 内置）**
```cmd
cd C:\linkedin-scraper
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/linkedin_scraper.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/sheets_integration.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/scraper_server.py
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_server_win.bat
curl -O https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_tunnel_win.bat
```

**方法二：浏览器直接下载**

访问以下链接，右键 → "另存为" 到 `C:\linkedin-scraper\`：
- https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/linkedin_scraper.py
- https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/sheets_integration.py
- https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/scraper_server.py
- https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_server_win.bat
- https://raw.githubusercontent.com/yalezangyong-droid/Claude/claude/linkedin-scraper-sheets-BL1bC/start_tunnel_win.bat

### Step 6: 安装 Python 依赖

```cmd
pip install selenium gspread google-auth flask
```

### Step 7: 放置 Google 凭证文件

将你的 `credentials.json` 文件复制到 `C:\linkedin-scraper\` 文件夹中。

### Step 8: 首次登录 LinkedIn

运行一次爬虫来登录 LinkedIn（会保存登录状态）：
```cmd
cd C:\linkedin-scraper
python linkedin_scraper.py --days 7 --output test.json
```

这会打开 Chrome 浏览器，手动登录 LinkedIn，登录成功后等待爬虫完成。

---

## 日常使用

### 🚀 每次使用需要打开两个 CMD 窗口：

#### 窗口1: 启动 Flask 服务器

```cmd
cd C:\linkedin-scraper
start_server_win.bat
```

或者手动运行：
```cmd
cd C:\linkedin-scraper
python scraper_server.py --port 5000 --sheet-id "1Gv36EQuIC2E04E8dResLMa_K9xU6i1rc4Bubsi3FS1M" --sheet-name "Will's LinkedIn Automated Tracker" --credentials "credentials.json"
```

保持这个窗口运行，你会看到：
```
 * Running on http://127.0.0.1:5000
```

#### 窗口2: 启动 Cloudflare Tunnel

打开**新的** CMD 窗口：
```cmd
cd C:\linkedin-scraper
start_tunnel_win.bat
```

或者手动运行：
```cmd
cloudflared tunnel --url http://localhost:5000
```

你会看到类似输出：
```
2024-01-15T10:30:00Z INF |  https://random-words-here.trycloudflare.com
```

**复制这个 https://xxxxx.trycloudflare.com URL！**

#### Step 3: 更新 Google Apps Script

1. 打开你的 Google Sheet
2. 菜单：`Extensions` → `Apps Script`
3. 找到第 19 行：
```javascript
const SCRAPER_URL = "https://你的新URL.trycloudflare.com";
```
4. 替换为刚才复制的 URL
5. 按 `Ctrl + S` 保存

#### Step 4: 从 Google Sheet 触发抓取

1. 回到 Google Sheet
2. 点击菜单：`LinkedIn Scraper` → `Fetch Last 30 Days`
3. 等待完成通知

#### 停止服务

在两个 CMD 窗口分别按 `Ctrl + C`

---

## 故障排查

### 问题：找不到文件 / No such file or directory

**原因**：没有进入正确的文件夹

**解决**：
```cmd
:: 确认文件位置
dir C:\linkedin-scraper

:: 进入文件夹
cd C:\linkedin-scraper
```

### 问题：Server Offline / <!DOCTYPE error

**原因**：Cloudflare Tunnel URL 过期了

**解决**：
1. 在窗口2按 `Ctrl + C` 停止 cloudflared
2. 重新运行 `cloudflared tunnel --url http://localhost:5000`
3. 复制新的 URL 到 Google Apps Script

### 问题：'python' 不是内部或外部命令

**原因**：Python 没有添加到 PATH

**解决**：
1. 重新安装 Python
2. 安装时勾选 "Add Python to PATH"

### 问题：'cloudflared' 不是内部或外部命令

**原因**：cloudflared 没有安装或不在 PATH

**解决**：
```cmd
winget install Cloudflare.cloudflared
```

然后**关闭并重新打开** CMD 窗口。

### 问题：LinkedIn 需要重新登录

**解决**：
```cmd
cd C:\linkedin-scraper
python linkedin_scraper.py --days 7 --output test.json
```
在打开的 Chrome 中手动登录。

### 问题：Google Sheets 权限错误

**解决**：
1. 打开 Google Sheet
2. 点击 `Share`（分享）
3. 添加 service account email（在 credentials.json 中的 client_email）
4. 给予 `Editor`（编辑者）权限

---

## 📁 文件结构

```
C:\linkedin-scraper\
├── linkedin_scraper.py      # 核心爬虫
├── sheets_integration.py    # Google Sheets 集成
├── scraper_server.py        # Flask 服务器
├── start_server_win.bat     # 启动 Flask
├── start_tunnel_win.bat     # 启动 Cloudflare Tunnel
└── credentials.json         # Google 服务账号凭证
```

---

## 💡 小贴士

1. **Cloudflare Tunnel 优势**：完全免费，无需注册账号，无使用限制
2. **创建桌面快捷方式**：右键 `.bat` 文件 → 发送到 → 桌面快捷方式
3. **每次 URL 都会变**：Cloudflare 免费版每次重启都会生成新 URL，需要更新 Apps Script

---

## 🆘 需要帮助？

如果遇到其他问题，检查：
1. CMD 窗口中的错误信息
2. 确保两个窗口（Flask 和 Cloudflare）都在运行
3. Google Apps Script 的执行日志（Apps Script 页面 → Executions）
