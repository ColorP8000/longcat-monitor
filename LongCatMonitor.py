
import tkinter as tk
from tkinter import ttk
import requests
import time
import threading
import random
from datetime import datetime
import os
import sys

def load_env(file_path='.env'):
    """从 .env 文件加载配置"""
    config = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

# 从 .env 文件加载配置
env_config = load_env()

COOKIE_STR = env_config.get('COOKIE_STR', '')
BASE_USAGE_URL = env_config.get('BASE_USAGE_URL', 'https://longcat.chat/api/lc-platform/v1/tokenUsage')

if not COOKIE_STR:
    print("错误：未在 .env 文件中找到 COOKIE_STR 配置")
    print("请确保 .env 文件存在且包含 COOKIE_STR")
    sys.exit(1)

HEADERS = {
    "Cookie": COOKIE_STR,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://longcat.chat/platform/usage",
    "Accept": "application/json, text/plain, */*"
}


class LongCatMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LongCat API 额度监控")
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap(default="icon.ico")
        except:
            pass

        # 配置样式
        self.setup_ui()

        # 首次获取数据
        self.fetch_data()

        # 启动自动刷新（每5分钟）
        self.auto_refresh()

    def setup_ui(self):
        # 主容器 - 使用 pack 布局，确保状态栏始终在底部
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 标题栏（包含刷新按钮）
        title_frame = tk.Frame(main_container, bg="#1a1a2e", pady=10)
        title_frame.pack(fill=tk.X)

        # 标题（左侧）
        title_label = tk.Label(
            title_frame,
            text="🐱 LongCat API 额度监控",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        title_label.pack(side=tk.LEFT, padx=(20, 10))

        # 刷新按钮（右侧）
        refresh_btn = tk.Button(
            title_frame,
            text="🔄",
            font=("Microsoft YaHei", 12),
            bg="#4CAF50",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
            command=self.fetch_data
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(10, 20))

        # 状态栏 - 先打包放在底部
        status_frame = tk.Frame(main_container, bg="#0f0f23", pady=8)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame,
            text="正在获取数据...",
            font=("Microsoft YaHei", 11),
            bg="#0f0f23",
            fg="#aaaaaa"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.time_label = tk.Label(
            status_frame,
            text="",
            font=("Microsoft YaHei", 11),
            bg="#0f0f23",
            fg="#aaaaaa"
        )
        self.time_label.pack(side=tk.RIGHT, padx=10)

        # 主内容区 - 填充剩余空间
        main_frame = tk.Frame(main_container, bg="#16213e", padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 额度显示卡片
        self.total_card = self.create_card(main_frame, "总额度", "#4CAF50")
        self.used_card = self.create_card(main_frame, "已用额度", "#FF9800")
        self.available_card = self.create_card(main_frame, "剩余额度", "#2196F3")

        # 进度条区域（包含百分比）
        progress_frame = tk.Frame(main_frame, bg="#16213e")
        progress_frame.pack(fill=tk.X, pady=(10, 5))

        # 百分比显示
        percent_frame = tk.Frame(progress_frame, bg="#16213e")
        percent_frame.pack(fill=tk.X)

        tk.Label(
            percent_frame,
            text="剩余百分比：",
            font=("Microsoft YaHei", 10),
            bg="#16213e",
            fg="#aaaaaa"
        ).pack(side=tk.LEFT)

        self.percent_label = tk.Label(
            percent_frame,
            text="--",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#16213e",
            fg="#E91E63"
        )
        self.percent_label.pack(side=tk.RIGHT)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=380
        )
        self.progress_bar.pack(pady=5)

        self.progress_label = tk.Label(
            progress_frame,
            text="已用 0%",
            font=("Microsoft YaHei", 9),
            bg="#16213e",
            fg="#888888"
        )
        self.progress_label.pack(anchor=tk.E)

    def create_card(self, parent, title, color):
        """创建额度显示卡片"""
        card = tk.Frame(parent, bg="#1a1a2e", padx=15, pady=8)
        card.pack(fill=tk.X, pady=3)

        tk.Label(
            card,
            text=title,
            font=("Microsoft YaHei", 10),
            bg="#1a1a2e",
            fg="#888888"
        ).pack(anchor=tk.W)

        value_label = tk.Label(
            card,
            text="--",
            font=("Microsoft YaHei", 20, "bold"),
            bg="#1a1a2e",
            fg=color
        )
        value_label.pack(anchor=tk.W)

        # 保存引用以便更新
        if '总额度' in title:
            self.total_label = value_label
        elif '已用' in title:
            self.used_label = value_label
        elif '剩余' in title:
            self.available_label = value_label
        elif '百分比' in title:
            self.percent_label = value_label

        return card

    def fetch_data(self):
        """获取额度数据"""
        self.status_label.config(text="正在获取数据...")

        # 在后台线程中执行请求，避免界面卡顿
        thread = threading.Thread(target=self._fetch_data_thread)
        thread.daemon = True
        thread.start()

    def _fetch_data_thread(self):
        """后台线程获取数据"""
        timestamp = int(time.time() * 1000)
        url = f"{BASE_USAGE_URL}?day=today&t={timestamp}"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            res = resp.json()

            if res.get("code") != 0:
                error_msg = res.get('message', '未知错误')
                self.root.after(0, lambda: self.show_error(f"接口异常：{error_msg}"))
                return

            # 解析数据
            model_data = res["data"]["extData"]["LongCat-Pro-Preview"]
            data = {
                "total": model_data["totalToken"],
                "used": model_data["usedToken"],
                "available": model_data["availableToken"]
            }

            # 在主线程中更新UI
            self.root.after(0, lambda: self.update_ui(data))

        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: self.show_error(f"请求失败：{str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"解析错误：{str(e)}"))

    def update_ui(self, data):
        """更新界面显示"""
        total = data["total"]
        used = data["used"]
        available = data["available"]

        # 更新卡片数值
        self.total_label.config(text=f"{total:,}")
        self.used_label.config(text=f"{used:,}")
        self.available_label.config(text=f"{available:,}")

        # 计算并更新百分比（剩余百分比）
        if total > 0:
            remaining_percent = (available / total) * 100
            used_percent = (used / total) * 100
            self.percent_label.config(text=f"{remaining_percent:.1f}%")
            self.progress_var.set(used_percent)
            self.progress_label.config(text=f"已用 {used_percent:.1f}%")
        else:
            self.percent_label.config(text="100%")
            self.progress_var.set(0)
            self.progress_label.config(text="已用 0%")

        # 更新时间
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"最后更新：{now}")
        self.status_label.config(text="✅ 数据已更新")

    def show_error(self, message):
        """显示错误信息"""
        self.total_label.config(text="--")
        self.used_label.config(text="--")
        self.available_label.config(text="--")
        self.percent_label.config(text="--")
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_label.config(text=f"❌ {message}")

    def auto_refresh(self):
        """自动刷新（5-10分钟随机间隔，避免风控）"""
        self.fetch_data()
        # 生成5-10分钟的随机间隔（300000-600000毫秒）
        random_interval = random.randint(300000, 600000)
        self.root.after(random_interval, self.auto_refresh)


def main():
    root = tk.Tk()

    # 设置 DPI 感知（Windows 高分辨率屏幕适配）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = LongCatMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
