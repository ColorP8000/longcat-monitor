# LongCat API 额度监控

一个简单的桌面应用程序，用于监控 LongCat API 的剩余额度。

## 功能特点

- 📊 实时显示总额度、已用额度、剩余额度
- 📊 显示剩余百分比和进度条
- 🔄 手动点击刷新按钮立即获取最新数据
- ⏰ 自动刷新（5-10分钟随机间隔，防止账号风控）
- 🎨 美观的深色主题界面

## 安装使用

### 方法一：直接运行（推荐）

下载整个 `dist` 文件夹，双击 `LongCatMonitor.exe` 即可运行，无需安装任何依赖。

文件夹结构：
```
dist/
├── LongCatMonitor.exe  # 主程序
├── .env                # 配置文件
└── icon.ico            # 图标文件
```

**注意：** 这三个文件必须放在同一个目录下，缺一不可。

### 方法二：从源码运行

1. 确保已安装 Python 3.8+
2. 安装依赖：
   ```bash
   pip install requests
   ```
3. 配置 `.env` 文件（见下方配置说明）
4. 运行脚本：
   ```bash
   python LongCatMonitor.py
   ```

## 配置说明

### 1. 获取 Cookie

1. 打开浏览器，登录 [LongCat 平台](https://longcat.chat/platform/usage)
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面，点击任意一个请求
5. 在 Request Headers 中找到 Cookie 字段
6. 复制完整的 Cookie 值（通常是一长串文本）

**提示：** Cookie 通常由多个键值对组成（如 `a1=xxx; webId=xxx; ...`），需要将它们合并成一个完整的字符串。如果不确定如何操作，可以让 AI 工具帮你处理，例如：

> "请把以下 Cookie 片段合并成一个完整的字符串，用分号加空格分隔：a1=xxx, webId=xxx, ..."

### 2. 填写配置

打开 `.env` 文件，将合成的完整 Cookie 字符串粘贴到 `COOKIE_STR=` 后面：

```
COOKIE_STR=你合成的完整Cookie字符串
BASE_USAGE_URL=https://longcat.chat/api/lc-platform/v1/tokenUsage
```

## 技术栈

- Python 3
- tkinter（GUI）
- requests（HTTP 请求）
- PyInstaller（打包）

## License

MIT License
