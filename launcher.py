#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业AI提示词生成器 - 桌面启动器
支持API Key管理，自动启动浏览器
Windows 11 Fluent Design 风格
"""

import os
import sys
import json
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, font
from pathlib import Path

# Windows 11 颜色方案
class ModernColors:
    """现代配色方案"""
    # 渐变背景
    BG_GRADIENT_START = "#0078D4"
    BG_GRADIENT_END = "#00BCF2"
    
    # 浅色主题
    BG_PRIMARY = "#F3F3F3"
    BG_SECONDARY = "#FFFFFF"
    BG_CARD = "#FFFFFF"
    BG_INPUT = "#F5F5F5"
    
    TEXT_PRIMARY = "#1A1A1A"
    TEXT_SECONDARY = "#5F5F5F"
    TEXT_TERTIARY = "#8A8A8A"
    TEXT_ON_ACCENT = "#FFFFFF"
    
    ACCENT = "#0078D4"
    ACCENT_HOVER = "#006CC1"
    ACCENT_LIGHT = "#E6F2FF"
    
    BORDER = "#E0E0E0"
    BORDER_FOCUS = "#0078D4"
    
    SUCCESS = "#107C10"
    WARNING = "#FF8C00"
    ERROR = "#E81123"
    
    SHADOW = "rgba(0,0,0,0.1)"

class ModernLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI提示词生成器")
        self.root.geometry("600x750")
        self.root.resizable(False, False)
        self.root.overrideredirect(False)

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Flask 相关
        self.flask_thread = None
        self.flask_app = None

        # 样式配置
        self.colors = ModernColors()
        self.setup_fonts()

        # 配置文件路径 - 在打包环境下使用exe所在目录，开发环境下使用脚本所在目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            work_dir = Path(sys.executable).parent
        else:
            # 开发环境
            work_dir = Path(__file__).parent

        self.config_file = work_dir / "launcher_config.json"

        # 应用配置
        self.app_port = 5000
        self.app_host = "127.0.0.1"
        self.app_url = f"http://{self.app_host}:{self.app_port}"

        # 加载配置
        self.config = self.load_config()

        # 创建UI
        self.create_ui()

        # 应用隐藏API设置
        if self.config.get('hide_api', False):
            self.toggle_api_visibility()

        # 窗口居中
        self.center_window()

        # 添加淡入动画
        self.fade_in()
    
    def setup_fonts(self):
        """设置字体"""
        self.font_title = font.Font(family="Segoe UI Variable Display", size=28, weight="bold")
        self.font_subtitle = font.Font(family="Segoe UI Variable", size=12, weight="normal")
        self.font_label = font.Font(family="Segoe UI Variable", size=10, weight="bold")
        self.font_input = font.Font(family="Segoe UI Variable", size=11, weight="normal")
        self.font_button = font.Font(family="Segoe UI Variable", size=11, weight="bold")
        self.font_status = font.Font(family="Segoe UI Variable", size=9, weight="normal")
        self.font_version = font.Font(family="Segoe UI Variable", size=8, weight="normal")
    
    def fade_in(self):
        """淡入动画"""
        self.root.attributes('-alpha', 0.0)
        for i in range(0, 11):
            self.root.attributes('-alpha', i / 10)
            self.root.update()
            self.root.after(15)
    
    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 600
        window_height = 750
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def load_config(self):
        """加载配置"""
        default_config = {
            "api_key": "",
            "volc_api_key": "",
            "save_api": False,
            "hide_api": False
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except:
                pass
        
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            # 读取现有配置（如果存在）
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            else:
                existing = {}

            # 更新配置
            if self.save_api_var.get():
                # 保存时，更新所有配置
                existing.update({
                    'api_key': self.config.get('api_key', ''),
                    'volc_api_key': self.config.get('volc_api_key', ''),
                    'save_api': True,
                    'hide_api': self.config.get('hide_api', False)
                })
            else:
                # 不保存时，清除密钥但保留其他设置
                existing['api_key'] = ''
                existing['volc_api_key'] = ''
                existing['save_api'] = False
                existing['hide_api'] = self.config.get('hide_api', False)

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

            print(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors.BG_PRIMARY)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部渐变背景
        header_frame = tk.Frame(main_container, bg=self.colors.BG_GRADIENT_START)
        header_frame.pack(fill=tk.X, ipady=40)
        
        # Logo
        logo_label = tk.Label(
            header_frame,
            text="✨",
            bg=self.colors.BG_GRADIENT_START,
            fg=self.colors.TEXT_ON_ACCENT,
            font=('Segoe UI Emoji', 52)
        )
        logo_label.pack(pady=(20, 10))
        
        # 标题
        title_label = tk.Label(
            header_frame,
            text="AI提示词生成器",
            bg=self.colors.BG_GRADIENT_START,
            fg=self.colors.TEXT_ON_ACCENT,
            font=self.font_title
        )
        title_label.pack(pady=(5, 5))
        
        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="Professional AI Prompt Generator",
            bg=self.colors.BG_GRADIENT_START,
            fg="#E6E6E6",
            font=self.font_subtitle
        )
        subtitle_label.pack()
        
        # 内容区域
        content_frame = tk.Frame(main_container, bg=self.colors.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)
        
        # API Key 输入卡片
        card_frame = tk.Frame(
            content_frame,
            bg=self.colors.BG_CARD,
            relief=tk.FLAT,
            borderwidth=0
        )
        card_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 添加阴影效果（用边框模拟）
        shadow_frame = tk.Frame(
            content_frame,
            bg="#DDDDDD",
            height=1
        )
        shadow_frame.pack(fill=tk.X, pady=(0, 15))
        
        # API Key 输入
        self.api_entry_var = tk.StringVar(value=self.config.get('api_key', ''))
        
        api_label = tk.Label(
            card_frame,
            text="智谱AI API Key",
            bg=self.colors.BG_CARD,
            fg=self.colors.TEXT_PRIMARY,
            font=self.font_label,
            anchor='w'
        )
        api_label.pack(fill=tk.X, padx=25, pady=(25, 8))
        
        # API Key 输入框容器
        api_input_frame = tk.Frame(card_frame, bg=self.colors.BG_INPUT, bd=1, relief=tk.FLAT)
        api_input_frame.pack(fill=tk.X, padx=25, pady=(0, 15), ipady=12)
        
        self.api_entry = tk.Entry(
            api_input_frame,
            textvariable=self.api_entry_var,
            font=self.font_input,
            bg=self.colors.BG_INPUT,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.api_entry.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # 火山引擎 API Key（可选）
        self.volc_api_entry_var = tk.StringVar(value=self.config.get('volc_api_key', ''))
        
        volc_label = tk.Label(
            card_frame,
            text="火山引擎 API Key（可选）",
            bg=self.colors.BG_CARD,
            fg=self.colors.TEXT_SECONDARY,
            font=self.font_label,
            anchor='w'
        )
        volc_label.pack(fill=tk.X, padx=25, pady=(0, 8))
        
        volc_input_frame = tk.Frame(card_frame, bg=self.colors.BG_INPUT, bd=1, relief=tk.FLAT)
        volc_input_frame.pack(fill=tk.X, padx=25, pady=(0, 25), ipady=12)
        
        self.volc_api_entry = tk.Entry(
            volc_input_frame,
            textvariable=self.volc_api_entry_var,
            font=self.font_input,
            bg=self.colors.BG_INPUT,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.volc_api_entry.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # 选项
        options_frame = tk.Frame(content_frame, bg=self.colors.BG_PRIMARY)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.save_api_var = tk.BooleanVar(value=self.config.get('save_api', False))
        save_check = tk.Checkbutton(
            options_frame,
            text="保存 API Key",
            variable=self.save_api_var,
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_SECONDARY,
            selectcolor=self.colors.BG_PRIMARY,
            activebackground=self.colors.BG_PRIMARY,
            activeforeground=self.colors.TEXT_PRIMARY,
            font=('Segoe UI Variable', 10),
            cursor="hand2"
        )
        save_check.pack(side=tk.LEFT, padx=(0, 20))
        
        self.hide_api_var = tk.BooleanVar(value=self.config.get('hide_api', False))
        hide_check = tk.Checkbutton(
            options_frame,
            text="隐藏密钥",
            variable=self.hide_api_var,
            command=self.toggle_api_visibility,
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_SECONDARY,
            selectcolor=self.colors.BG_PRIMARY,
            activebackground=self.colors.BG_PRIMARY,
            activeforeground=self.colors.TEXT_PRIMARY,
            font=('Segoe UI Variable', 10),
            cursor="hand2"
        )
        hide_check.pack(side=tk.LEFT)
        
        # 启动按钮（大按钮）
        self.launch_btn = tk.Button(
            content_frame,
            text="🚀 启动应用",
            command=self.launch_app,
            font=self.font_button,
            bg=self.colors.ACCENT,
            fg=self.colors.TEXT_ON_ACCENT,
            activebackground=self.colors.ACCENT_HOVER,
            activeforeground=self.colors.TEXT_ON_ACCENT,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=16
        )
        self.launch_btn.pack(fill=tk.X, pady=(0, 12))
        
        # 绑定按钮悬停效果
        self.launch_btn.bind('<Enter>', lambda e: self.launch_btn.config(bg=self.colors.ACCENT_HOVER))
        self.launch_btn.bind('<Leave>', lambda e: self.launch_btn.config(bg=self.colors.ACCENT))
        
        # 退出按钮
        exit_btn = tk.Button(
            content_frame,
            text="🚪 退出程序",
            command=self.on_closing,
            font=self.font_button,
            bg="#666666",
            fg="#FFFFFF",
            activebackground="#555555",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=12
        )
        exit_btn.pack(fill=tk.X, pady=(0, 20))

        # 绑定按钮悬停效果
        exit_btn.bind('<Enter>', lambda e: exit_btn.config(bg="#555555"))
        exit_btn.bind('<Leave>', lambda e: exit_btn.config(bg="#666666"))
        
        # 状态栏
        self.status_label = tk.Label(
            content_frame,
            text="准备就绪",
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_TERTIARY,
            font=self.font_status
        )
        self.status_label.pack()
        
        # 版本信息
        version_label = tk.Label(
            main_container,
            text="v1.5.1 | Windows 11 Edition",
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_TERTIARY,
            font=self.font_version
        )
        version_label.pack(side=tk.BOTTOM, pady=15)
    
    def toggle_api_visibility(self):
        """切换API Key的显示/隐藏"""
        hide = self.hide_api_var.get()
        
        api_value = self.api_entry.get()
        volc_api_value = self.volc_api_entry.get()
        
        if hide:
            self.api_entry.config(show='*')
            self.volc_api_entry.config(show='*')
        else:
            self.api_entry.config(show='')
            self.volc_api_entry.config(show='')
        
        self.api_entry.delete(0, tk.END)
        self.api_entry.insert(0, api_value)
        self.volc_api_entry.delete(0, tk.END)
        self.volc_api_entry.insert(0, volc_api_value)
    
    def launch_app(self):
        """启动应用"""
        api_key = self.api_entry.get().strip()
        volc_api_key = self.volc_api_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("提示", "请输入智谱AI API Key")
            self.api_entry.focus()
            return
        
        self.config['api_key'] = api_key
        self.config['volc_api_key'] = volc_api_key
        self.config['save_api'] = self.save_api_var.get()
        self.config['hide_api'] = self.hide_api_var.get()
        
        if self.save_api_var.get():
            if self.save_config():
                self.status_label.config(text="配置已保存", fg=self.colors.TEXT_TERTIARY)
            else:
                messagebox.showerror("错误", "保存配置失败")
        
        self.launch_btn.config(text="⏳ 启动中...", state=tk.DISABLED, bg=self.colors.TEXT_TERTIARY)
        self.status_label.config(text="正在启动服务...", fg=self.colors.TEXT_TERTIARY)
        self.root.update()
        
        try:
            self.start_server()
            
            import time
            import socket
            
            self.status_label.config(text="正在等待服务启动...", fg=self.colors.TEXT_TERTIARY)
            self.root.update()
            
            max_retries = 30
            server_started = False
            
            for i in range(max_retries):
                time.sleep(1)
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((self.app_host, self.app_port))
                    sock.close()
                    
                    if result == 0:
                        server_started = True
                        break
                except:
                    pass
                
                self.status_label.config(text=f"正在等待服务启动... ({i+1}/{max_retries})", fg=self.colors.TEXT_TERTIARY)
                self.root.update()
            
            if not server_started:
                raise Exception(f"服务器启动超时（已等待{max_retries}秒），请检查API Key是否正确")
            
            time.sleep(1)
            
            self.open_browser()
            
            self.status_label.config(text="应用已启动，浏览器已打开", fg=self.colors.SUCCESS)
            self.launch_btn.config(text="✅ 运行中", state=tk.DISABLED, bg=self.colors.SUCCESS)
            
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动应用:\n{str(e)}")
            self.launch_btn.config(text="🚀 启动应用", state=tk.NORMAL, bg=self.colors.ACCENT)
            self.status_label.config(text="启动失败", fg=self.colors.ERROR)
    
    def start_server(self):
        """启动Flask服务器"""
        import threading
        import io
        import logging
        import warnings
        
        import os
        api_key = self.config.get('api_key', '')
        volc_api_key = self.config.get('volc_api_key', '')
        if api_key:
            os.environ['API_KEY'] = api_key
        if volc_api_key:
            os.environ['VOLC_API_KEY'] = volc_api_key
        
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
        warnings.filterwarnings("ignore")
        
        from app import app as flask_app
        
        self.flask_app = flask_app
        
        def run_flask():
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            devnull = io.StringIO()
            try:
                sys.stdout = devnull
                sys.stderr = devnull
                flask_app.run(
                    debug=False,
                    port=self.app_port,
                    host=self.app_host,
                    use_reloader=False,
                    threaded=True
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.daemon = True
        self.flask_thread = flask_thread
        flask_thread.start()
        
        import time
        time.sleep(0.5)
        
        return True
    
    def open_browser(self):
        """打开浏览器"""
        try:
            webbrowser.open(self.app_url)
        except Exception as e:
            raise Exception(f"无法打开浏览器: {str(e)}")

    def on_closing(self):
        """窗口关闭事件 - 确保清理所有进程"""
        try:
            print("正在关闭应用...")

            # 如果有Flask线程在运行，让它自然结束（因为是daemon线程）
            if self.flask_thread and self.flask_thread.is_alive():
                print("等待Flask线程结束...")
                # Flask是daemon线程，会自动随主线程结束

            # 尝试优雅退出
            import sys
            sys.exit(0)

        except Exception as e:
            print(f"退出时发生错误: {e}")
            # 强制退出
            import os
            os._exit(0)

def main():
    root = tk.Tk()
    app = ModernLauncherApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
