#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业AI提示词生成器 - 桌面启动器
支持API Key管理，自动启动浏览器
深色主题设计 - 与网页端风格一致
"""

__version__ = "1.7.0"
__author__ = "Prompt Tool PRO Team"
__copyright__ = "Copyright (c) 2024 Prompt Tool PRO"

import os
import sys
import json
import webbrowser
import tkinter as tk
from tkinter import messagebox, font, ttk
from pathlib import Path
import logging
from datetime import datetime

# 与网页端一致的深色主题配色方案
class ModernColors:
    """现代深色配色方案 - 与网页端风格一致"""
    # 渐变背景（网页端风格：紫色渐变）
    BG_GRADIENT_START = "#667eea"
    BG_GRADIENT_END = "#764ba2"

    # 深色主题背景
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_CARD = "#2a2a3e"
    BG_INPUT = "#15151f"

    # 文本颜色
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#b3b3b3"
    TEXT_TERTIARY = "#808080"
    TEXT_ON_ACCENT = "#ffffff"

    # 强调色（紫色系）
    ACCENT = "#a682ff"
    ACCENT_HOVER = "#b895ff"
    ACCENT_LIGHT = "#1e1a35"

    # 边框颜色
    BORDER = "#3a3a4e"
    BORDER_FOCUS = "#a682ff"

    # 状态颜色
    SUCCESS = "#4CAF50"
    WARNING = "#ff9800"
    ERROR = "#f44336"

    # 阴影
    SHADOW = "rgba(0, 0, 0, 0.5)"

class RoundedCheckbutton:
    """自定义圆角复选框"""
    def __init__(self, parent, text, variable, bg, fg, checked_color, unchecked_color, cursor="hand2"):
        self.parent = parent
        self.text = text
        self.variable = variable
        self.bg = bg
        self.fg = fg
        self.checked_color = checked_color
        self.unchecked_color = unchecked_color
        self.checked = variable.get()

        # 创建容器
        self.frame = tk.Frame(parent, bg=bg, cursor=cursor)
        self.frame.pack(side=tk.LEFT, padx=5)

        # 创建 Canvas 用于绘制圆角复选框
        self.canvas = tk.Canvas(
            self.frame,
            width=18,
            height=18,
            bg=bg,
            highlightthickness=0,
            cursor=cursor
        )
        self.canvas.pack(side=tk.LEFT, padx=(0, 8))

        # 创建标签
        self.label = tk.Label(
            self.frame,
            text=text,
            bg=bg,
            fg=fg,
            font=('Microsoft YaHei UI', 9, 'bold'),
            cursor=cursor
        )
        self.label.pack(side=tk.LEFT)

        # 绑定点击事件
        self.canvas.bind('<Button-1>', self.toggle)
        self.label.bind('<Button-1>', self.toggle)
        self.frame.bind('<Button-1>', self.toggle)

        # 绘制初始状态
        self.draw()

    def draw(self):
        """绘制复选框"""
        self.canvas.delete("all")

        # 确定颜色
        if self.checked:
            fill_color = self.checked_color
        else:
            fill_color = self.unchecked_color

        # 绘制圆角复选框（简化版）
        # 使用单色填充，边框与背景相同
        x1, y1 = 1, 1
        x2, y2 = 17, 17

        # 绘制四个圆角（作为背景）
        r = 3
        self.canvas.create_oval(x1, y1, x1 + r*2, y1 + r*2, fill=fill_color, outline=fill_color)
        self.canvas.create_oval(x2 - r*2, y1, x2, y1 + r*2, fill=fill_color, outline=fill_color)
        self.canvas.create_oval(x1, y2 - r*2, x1 + r*2, y2, fill=fill_color, outline=fill_color)
        self.canvas.create_oval(x2 - r*2, y2 - r*2, x2, y2, fill=fill_color, outline=fill_color)

        # 绘制中间填充
        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill_color, outline=fill_color)
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill_color, outline=fill_color)

        # 如果选中，绘制对号
        if self.checked:
            self.canvas.create_line(5, 9, 8, 12, width=2, fill="#ffffff", capstyle=tk.ROUND)
            self.canvas.create_line(8, 12, 13, 6, width=2, fill="#ffffff", capstyle=tk.ROUND)

    def toggle(self, event=None):
        """切换状态"""
        self.checked = not self.checked
        self.variable.set(self.checked)
        self.draw()

class RoundedButton:
    """自定义圆角按钮"""
    def __init__(self, parent, text, command, bg, active_bg, fg, font, padx=18, pady=14, cursor="hand2"):
        self.parent = parent
        self.text = text
        self.command = command
        self.bg = bg
        self.active_bg = active_bg
        self.fg = fg
        self.font = font
        self.cursor = cursor

        # 创建容器
        self.frame = tk.Frame(parent, bg=parent.cget('bg'), cursor=cursor)

        # 创建 Canvas 用于绘制圆角按钮
        self.canvas = tk.Canvas(
            self.frame,
            bg=parent.cget('bg'),
            highlightthickness=0,
            cursor=cursor
        )

        # 创建标签
        self.label = tk.Label(
            self.canvas,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            cursor=cursor
        )

        # 绑定事件
        self.label.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Enter>', self.on_enter)
        self.canvas.bind('<Leave>', self.on_leave)

        # 计算尺寸
        text_width = self.font.measure(text)
        self.width = text_width + padx * 2
        self.height = pady * 2 + 20

        # 设置 Canvas 尺寸
        self.canvas.config(width=self.width, height=self.height)

        # 放置标签
        self.canvas.create_window(
            self.width // 2,
            self.height // 2,
            window=self.label
        )

    def pack(self, **kwargs):
        """包装方法"""
        self.frame.pack(**kwargs)
        self.canvas.pack()
        self.draw(self.bg)

    def pack_forget(self):
        """包装方法"""
        self.frame.pack_forget()

    def draw(self, color):
        """绘制圆角按钮"""
        self.canvas.delete("button_bg")

        x1, y1 = 0, 0
        x2, y2 = self.width, self.height
        r = 8  # 圆角半径

        # 绘制圆角矩形背景
        self.canvas.create_oval(x1, y1, x1 + r*2, y1 + r*2, fill=color, outline="", tags="button_bg")
        self.canvas.create_oval(x2 - r*2, y1, x2, y1 + r*2, fill=color, outline="", tags="button_bg")
        self.canvas.create_oval(x1, y2 - r*2, x1 + r*2, y2, fill=color, outline="", tags="button_bg")
        self.canvas.create_oval(x2 - r*2, y2 - r*2, x2, y2, fill=color, outline="", tags="button_bg")
        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="", tags="button_bg")
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="", tags="button_bg")

        # 更新标签背景
        self.label.config(bg=color)

    def on_click(self, event):
        """点击事件"""
        if self.command:
            self.command()

    def on_enter(self, event):
        """鼠标进入"""
        self.draw(self.active_bg)

    def on_leave(self, event):
        """鼠标离开"""
        self.draw(self.bg)

    def config(self, **kwargs):
        """配置方法"""
        if 'text' in kwargs:
            self.text = kwargs['text']
            self.label.config(text=kwargs['text'])
        if 'state' in kwargs:
            if kwargs['state'] == tk.DISABLED:
                self.label.config(fg="#808080")
                self.canvas.config(cursor="arrow")
            else:
                self.label.config(fg=self.fg)
                self.canvas.config(cursor=self.cursor)
        if 'bg' in kwargs:
            self.bg = kwargs['bg']
            self.draw(self.bg)

class ModernLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"专业AI提示词生成器 v{__version__}")
        
        # 初始化日志记录器
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("初始化启动器")
        self.root.geometry("560x800")
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
        self.setup_styles()

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
        # 优先使用系统字体，确保在不同平台上都有良好渲染
        import platform
        system = platform.system()

        if system == "Windows":
            font_family = "Microsoft YaHei UI"
            subtitle_font = "Microsoft YaHei UI"
            input_font = "Consolas"
        elif system == "Darwin":  # macOS
            font_family = "PingFang SC"
            subtitle_font = "PingFang SC"
            input_font = "Menlo"
        else:  # Linux
            font_family = "Noto Sans CJK SC"
            subtitle_font = "Noto Sans CJK SC"
            input_font = "Ubuntu Mono"

        # 启用字体抗锯齿
        try:
            tk.call('tk', 'scaling', 1.2)
        except:
            pass

        self.font_title = font.Font(family=font_family, size=24, weight="bold")
        self.font_subtitle = font.Font(family=subtitle_font, size=10, weight="normal")
        self.font_label = font.Font(family=font_family, size=9, weight="bold")
        self.font_input = font.Font(family=input_font, size=10, weight="normal")
        self.font_button = font.Font(family=font_family, size=10, weight="bold")
        self.font_status = font.Font(family=font_family, size=9, weight="normal")
        self.font_version = font.Font(family=font_family, size=8, weight="normal")

    def setup_styles(self):
        """设置 ttk 样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 自定义 Checkbutton 样式
        style.configure(
            'Custom.Checkbutton',
            background=self.colors.BG_PRIMARY,
            foreground=self.colors.TEXT_SECONDARY,
            font=('Microsoft YaHei UI', 9, 'bold'),
            focuscolor='none',
            borderwidth=0,
            indicatorcolor=self.colors.BG_INPUT
        )

        style.map(
            'Custom.Checkbutton',
            background=[('active', self.colors.BG_PRIMARY)],
            foreground=[('active', self.colors.TEXT_PRIMARY)]
        )
    
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
        window_width = 560
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def load_config(self):
        """加载配置"""
        self.logger.info(f"正在加载配置文件: {self.config_file}")
        default_config = {
            "api_key": "",
            "volc_api_key": "",
            "volc_endpoint": "",
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
        self.logger.info("正在保存配置")
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
                # 注意：API密钥以明文保存，不安全。建议使用系统密钥环或加密。
                existing.update({
                    'api_key': self.config.get('api_key', ''),
                    'volc_api_key': self.config.get('volc_api_key', ''),
                    'volc_endpoint': self.config.get('volc_endpoint', ''),
                    'save_api': True,
                    'hide_api': self.config.get('hide_api', False)
                })
            else:
                # 不保存时，清除密钥但保留其他设置
                existing['api_key'] = ''
                existing['volc_api_key'] = ''
                existing['volc_endpoint'] = ''
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

        # 顶部渐变背景（紫色渐变，与网页端一致）
        header_frame = tk.Frame(main_container, bg=self.colors.BG_GRADIENT_START)
        header_frame.pack(fill=tk.X, ipady=35)

        # Logo
        logo_label = tk.Label(
            header_frame,
            text="🎨",
            bg=self.colors.BG_GRADIENT_START,
            fg=self.colors.TEXT_ON_ACCENT,
            font=('Segoe UI Emoji', 48)
        )
        logo_label.pack(pady=(18, 8))

        # 标题
        title_label = tk.Label(
            header_frame,
            text="AI提示词生成器",
            bg=self.colors.BG_GRADIENT_START,
            fg=self.colors.TEXT_ON_ACCENT,
            font=self.font_title
        )
        title_label.pack(pady=(4, 4))

        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="Professional AI Prompt Generator",
            bg=self.colors.BG_GRADIENT_START,
            fg="#f0f0f0",
            font=self.font_subtitle
        )
        subtitle_label.pack()

        # 内容区域
        content_frame = tk.Frame(main_container, bg=self.colors.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=25)

        # API Key 输入卡片（深色半透明卡片）
        card_frame = tk.Frame(
            content_frame,
            bg=self.colors.BG_CARD,
            relief=tk.FLAT,
            borderwidth=0
        )
        card_frame.pack(fill=tk.X, pady=(0, 18))

        # 卡片顶部边框（紫色，与网页端一致）
        card_border = tk.Frame(
            content_frame,
            bg=self.colors.ACCENT,
            height=3
        )
        card_border.pack(fill=tk.X, pady=(0, 12))

        # API Key 输入
        self.api_entry_var = tk.StringVar(value=self.config.get('api_key', ''))

        api_label = tk.Label(
            card_frame,
            text="智谱AI API Key",
            bg=self.colors.BG_CARD,
            fg=self.colors.ACCENT,
            font=self.font_label,
            anchor='w'
        )
        api_label.pack(fill=tk.X, padx=22, pady=(20, 6))

        # API Key 输入框（带圆角边框效果）
        api_input_frame = tk.Frame(
            card_frame,
            bg=self.colors.BG_INPUT,
            bd=1,
            relief=tk.FLAT,
            borderwidth=0,
            highlightbackground=self.colors.BORDER,
            highlightcolor=self.colors.ACCENT,
            highlightthickness=2
        )
        api_input_frame.pack(fill=tk.X, padx=22, pady=(0, 12))
        api_input_frame.pack_propagate(False)  # 防止子组件改变Frame大小
        api_input_frame.config(height=38)  # 设置固定高度

        self.api_entry = tk.Entry(
            api_input_frame,
            textvariable=self.api_entry_var,
            font=self.font_input,
            bg=self.colors.BG_INPUT,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=self.colors.ACCENT,
            selectbackground=self.colors.ACCENT,
            selectforeground=self.colors.TEXT_ON_ACCENT
        )
        self.api_entry.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

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
        volc_label.pack(fill=tk.X, padx=22, pady=(0, 6))

        volc_input_frame = tk.Frame(
            card_frame,
            bg=self.colors.BG_INPUT,
            bd=1,
            relief=tk.FLAT,
            borderwidth=0,
            highlightbackground=self.colors.BORDER,
            highlightcolor=self.colors.ACCENT,
            highlightthickness=2
        )
        volc_input_frame.pack(fill=tk.X, padx=22, pady=(0, 18))

        self.volc_api_entry = tk.Entry(
            volc_input_frame,
            textvariable=self.volc_api_entry_var,
            font=self.font_input,
            bg=self.colors.BG_INPUT,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=self.colors.ACCENT,
            selectbackground=self.colors.ACCENT,
            selectforeground=self.colors.TEXT_ON_ACCENT
        )
        self.volc_api_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # 火山引擎推理接入点ID（图像生成必需）
        self.volc_endpoint_entry_var = tk.StringVar(value=self.config.get('volc_endpoint', ''))

        volc_endpoint_label = tk.Label(
            card_frame,
            text="火山引擎推理接入点ID（图像生成必需）",
            bg=self.colors.BG_CARD,
            fg=self.colors.TEXT_SECONDARY,
            font=self.font_label,
            anchor='w'
        )
        volc_endpoint_label.pack(fill=tk.X, padx=22, pady=(0, 6))

        volc_endpoint_input_frame = tk.Frame(
            card_frame,
            bg=self.colors.BG_INPUT,
            bd=1,
            relief=tk.FLAT,
            borderwidth=0,
            highlightbackground=self.colors.BORDER,
            highlightcolor=self.colors.ACCENT,
            highlightthickness=2
        )
        volc_endpoint_input_frame.pack(fill=tk.X, padx=22, pady=(0, 18))

        self.volc_endpoint_entry = tk.Entry(
            volc_endpoint_input_frame,
            textvariable=self.volc_endpoint_entry_var,
            font=self.font_input,
            bg=self.colors.BG_INPUT,
            fg=self.colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=self.colors.ACCENT,
            selectbackground=self.colors.ACCENT,
            selectforeground=self.colors.TEXT_ON_ACCENT
        )
        self.volc_endpoint_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # 选项
        options_frame = tk.Frame(content_frame, bg=self.colors.BG_PRIMARY)
        options_frame.pack(fill=tk.X, pady=(0, 16))

        # 创建自定义圆角复选框
        self.save_api_var = tk.BooleanVar(value=self.config.get('save_api', False))
        self.save_check = RoundedCheckbutton(
            options_frame,
            text="  保存 API Key",
            variable=self.save_api_var,
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_SECONDARY,
            checked_color=self.colors.ACCENT,
            unchecked_color=self.colors.BG_INPUT
        )

        self.hide_api_var = tk.BooleanVar(value=self.config.get('hide_api', False))
        self.hide_check = RoundedCheckbutton(
            options_frame,
            text="  隐藏密钥",
            variable=self.hide_api_var,
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_SECONDARY,
            checked_color=self.colors.ACCENT,
            unchecked_color=self.colors.BG_INPUT
        )

        # 绑定复选框状态变化事件（hide_check 需要在 toggle 之后执行额外操作）
        # 解除原有的绑定，重新绑定包含 toggle 和额外操作的函数
        def hide_check_handler(event):
            self.hide_check.toggle(event)
            self.root.after(10, self.toggle_api_visibility)

        self.hide_check.frame.unbind('<Button-1>')
        self.hide_check.label.unbind('<Button-1>')
        self.hide_check.canvas.unbind('<Button-1>')

        self.hide_check.frame.bind('<Button-1>', hide_check_handler)
        self.hide_check.label.bind('<Button-1>', hide_check_handler)
        self.hide_check.canvas.bind('<Button-1>', hide_check_handler)

        # 启动按钮（自定义圆角按钮）
        self.launch_btn = RoundedButton(
            content_frame,
            text="🚀 启动应用",
            command=self.launch_app,
            bg=self.colors.BG_GRADIENT_START,
            active_bg=self.colors.BG_GRADIENT_END,
            fg=self.colors.TEXT_ON_ACCENT,
            font=self.font_button,
            padx=18,
            pady=14
        )
        self.launch_btn.pack(fill=tk.X, pady=(0, 10))

        # 退出按钮（自定义圆角按钮）
        self.exit_btn = RoundedButton(
            content_frame,
            text="🚪 退出程序",
            command=self.on_closing,
            bg=self.colors.ACCENT_LIGHT,
            active_bg="#2d254a",
            fg=self.colors.TEXT_PRIMARY,
            font=self.font_button,
            padx=18,
            pady=11
        )
        self.exit_btn.pack(fill=tk.X, pady=(0, 18))

        # 绑定输入框焦点效果
        self.bind_entry_focus(self.api_entry, api_input_frame)
        self.bind_entry_focus(self.volc_api_entry, volc_input_frame)
        self.bind_entry_focus(self.volc_endpoint_entry, volc_endpoint_input_frame)

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
            text="v1.7.0 | 深色主题 | 圆角UI",
            bg=self.colors.BG_PRIMARY,
            fg=self.colors.TEXT_TERTIARY,
            font=self.font_version
        )
        version_label.pack(side=tk.BOTTOM, pady=12)

    def bind_entry_focus(self, entry, frame):
        """绑定输入框焦点事件"""
        def on_focus_in(event):
            frame.config(highlightbackground=self.colors.ACCENT, highlightcolor=self.colors.ACCENT)

        def on_focus_out(event):
            frame.config(highlightbackground=self.colors.BORDER, highlightcolor=self.colors.BORDER)

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def toggle_api_visibility(self):
        """切换API Key的显示/隐藏"""
        hide = self.hide_api_var.get()

        if hide:
            self.api_entry.config(show='*')
            self.volc_api_entry.config(show='*')
            self.volc_endpoint_entry.config(show='*')
        else:
            self.api_entry.config(show='')
            self.volc_api_entry.config(show='')
            self.volc_endpoint_entry.config(show='')
    
    def launch_app(self):
        """启动应用"""
        self.logger.info("用户点击启动按钮")
        api_key = self.api_entry.get().strip()
        volc_api_key = self.volc_api_entry.get().strip()
        volc_endpoint = self.volc_endpoint_entry.get().strip()

        if not api_key:
            self.logger.warning("用户未输入API Key")
            messagebox.showwarning("提示", "请输入智谱AI API Key")
            self.api_entry.focus()
            return

        self.config['api_key'] = api_key
        self.config['volc_api_key'] = volc_api_key
        self.config['volc_endpoint'] = volc_endpoint
        self.config['save_api'] = self.save_api_var.get()
        self.config['hide_api'] = self.hide_api_var.get()

        if self.save_api_var.get():
            if self.save_config():
                self.status_label.config(text="配置已保存", fg=self.colors.TEXT_TERTIARY)
            else:
                messagebox.showerror("错误", "保存配置失败")

        # 更新按钮状态
        self.launch_btn.label.config(text="⏳ 启动中...")
        self.launch_btn.label.config(fg="#808080")
        self.launch_btn.canvas.config(cursor="arrow")

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
            self.launch_btn.label.config(text="✅ 运行中")
            self.logger.info("应用启动成功")
            self.launch_btn.label.config(fg="#ffffff")
            self.launch_btn.canvas.config(cursor="arrow")

        except Exception as e:
            self.logger.error(f"启动失败: {str(e)}", exc_info=True)
            messagebox.showerror("启动失败", f"无法启动应用:\n{str(e)}")
            self.launch_btn.label.config(text="🚀 启动应用")
            self.launch_btn.label.config(fg=self.colors.TEXT_ON_ACCENT)
            self.launch_btn.canvas.config(cursor="hand2")
            self.status_label.config(text="启动失败", fg=self.colors.ERROR)
    
    def start_server(self):
        """启动Flask服务器"""
        import threading
        import logging
        
        self.logger.info("准备启动Flask服务器")
        api_key = self.config.get('api_key', '')
        volc_api_key = self.config.get('volc_api_key', '')
        volc_endpoint = self.config.get('volc_endpoint', '')

        print(f"从配置中获取的API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else api_key}")
        print(f"从配置中获取的火山引擎API Key: {volc_api_key[:20]}...{volc_api_key[-10:] if volc_api_key and len(volc_api_key) > 30 else volc_api_key}")
        print(f"从配置中获取的火山引擎推理接入点ID: {volc_endpoint}")




        if api_key:
            os.environ['API_KEY'] = api_key
            print(f"已设置环境变量API_KEY")
        if volc_api_key:
            os.environ['VOLC_API_KEY'] = volc_api_key
            print(f"已设置环境变量VOLC_API_KEY")
        if volc_endpoint:
            os.environ['VOLC_ENDPOINT'] = volc_endpoint
            print(f"已设置环境变量VOLC_ENDPOINT: {volc_endpoint}")
        
        # 不再禁用日志，以便调试
        # log = logging.getLogger('werkzeug')
        # log.setLevel(logging.ERROR)
        # log.disabled = True
        # warnings.filterwarnings("ignore")
        
        from app import app as flask_app

        self.flask_app = flask_app

        def run_flask():
            from werkzeug.serving import WSGIRequestHandler

            # 重定向Flask的日志输出
            original_log = WSGIRequestHandler.log
            def custom_log(self, type, message, *args):
                msg = f"[Flask] {type} {message % args if args else message}"
                print(msg)
                if sys.__stdout__ is not None:
                    sys.__stdout__.write(msg + '\n')
                    sys.__stdout__.flush()
            WSGIRequestHandler.log = custom_log

            self.logger.info(f"Flask服务器启动中，端口: {self.app_port}...")
            print(f"Flask服务器启动中，端口: {self.app_port}...")
            flask_app.run(
                debug=False,
                port=self.app_port,
                host=self.app_host,
                use_reloader=False,
                threaded=True
            )
        
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
            self.logger.info(f"正在打开浏览器: {self.app_url}")
            webbrowser.open(self.app_url)
            self.logger.info("浏览器已打开")
        except Exception as e:
            raise Exception(f"无法打开浏览器: {str(e)}")

    def on_closing(self):
        """窗口关闭事件 - 确保清理所有进程"""
        try:
            self.logger.info("正在关闭应用...")
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

def setup_logging():
    """配置日志系统，同时输出到控制台和文件"""
    # 确定日志文件路径
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        work_dir = Path(sys.executable).parent
    else:
        # 开发环境
        work_dir = Path(__file__).parent
    
    # 创建logs目录
    logs_dir = work_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # 设置日志文件名（按日期）
    log_file = logs_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日志处理器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info(f"应用启动 - 版本 {__version__}")
    logger.info(f"日志文件: {log_file}")
    logger.info("="*50)
    
    return logger

def main():
    # 设置日志
    logger = setup_logging()
    
    root = tk.Tk()
    app = ModernLauncherApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
