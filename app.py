# app.py
from flask import Flask, render_template, request, jsonify
import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import Optional
import logging
from typing import Optional

# 确定运行路径（打包或开发环境）
if getattr(sys, 'frozen', False):
    # 打包后的环境
    BASE_DIR = Path(sys._MEIPASS)
    # 可写目录（用于历史记录）
    WORK_DIR = Path(sys.executable).parent
    print(f"打包环境: BASE_DIR={BASE_DIR}, WORK_DIR={WORK_DIR}")
else:
    # 开发环境
    BASE_DIR = Path(__file__).parent
    WORK_DIR = BASE_DIR
    print(f"开发环境: BASE_DIR={BASE_DIR}, WORK_DIR={WORK_DIR}")

# 确保模板和静态文件夹存在
template_folder = BASE_DIR / 'templates'
static_folder = BASE_DIR / 'static'

if not template_folder.exists():
    print(f"警告: 模板文件夹不存在: {template_folder}")
if not static_folder.exists():
    print(f"警告: 静态文件夹不存在: {static_folder}")

app = Flask(__name__, template_folder=str(template_folder), static_folder=str(static_folder))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置：用户需自行填写API Key
API_KEY = os.getenv('API_KEY', '')  # 通过启动器设置API Key
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 火山引擎配置
VOLC_API_KEY = os.getenv('VOLC_API_KEY', '')  # 通过启动器设置火山引擎API Key
VOLC_ENDPOINT = os.getenv('VOLC_ENDPOINT', '')  # 火山引擎推理接入点ID

# 优先从配置文件读取火山引擎配置
try:
    volc_config_file = WORK_DIR / "launcher_config.json"
    if volc_config_file.exists():
        with open(volc_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if config.get('volc_api_key'):
                VOLC_API_KEY = config.get('volc_api_key')
                print(f"从配置文件读取VOLC_API_KEY: {VOLC_API_KEY[:20]}...{VOLC_API_KEY[-10:]}")
            if config.get('volc_endpoint'):
                VOLC_ENDPOINT = config.get('volc_endpoint')
                print(f"从配置文件读取VOLC_ENDPOINT: {VOLC_ENDPOINT}")
            else:
                print("警告: 配置文件中未找到volc_endpoint，图像生成可能失败")
except Exception as e:
    print(f"读取火山引擎配置失败: {e}")

# 火山引擎图像生成API端点
# 使用推理接入点的完整URL格式
# 图像生成模型需要使用推理接入点的基础URL + /completions
VOLC_ENDPOINT_BASE = "https://ark.cn-beijing.volces.com"
VOLC_ENDPOINT_ID = VOLC_ENDPOINT  # 推理接入点ID
VOLC_DEFAULT_IMAGE_MODEL = "doubao-seedream-4-5-251128"  # 默认图像生成模型（如果未配置推理接入点）


# 历史记录文件路径（放在可写目录）
HISTORY_FILE = WORK_DIR / "prompt_history.txt"

def get_api_key():
    """获取API Key"""
    return os.getenv('API_KEY', '')

def get_volc_api_key():
    """获取火山引擎API Key（动态读取，支持环境变量和配置文件）"""
    # 先从环境变量读取
    volc_api_key = os.getenv('VOLC_API_KEY', '')

    # 如果环境变量为空，尝试从配置文件读取
    if not volc_api_key:
        try:
            volc_config_file = WORK_DIR / "launcher_config.json"
            if volc_config_file.exists():
                with open(volc_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    volc_api_key = config.get('volc_api_key', '')
        except Exception as e:
            print(f"从配置文件读取火山引擎API Key失败: {e}")

    return volc_api_key


# 路由定义
@app.route('/')
def index():
    try:
        logger.info("正在加载首页...")
        template_path = template_folder / 'index.html'
        logger.info(f"模板路径: {template_path}")
        logger.info(f"模板存在: {template_path.exists()}")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"加载首页失败: {str(e)}")
        return f"加载首页失败: {str(e)}", 500

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        logger.info(f"接收到的请求数据: {data}")

        user_input = data.get('input', '')
        style = data.get('style', None)

        if not user_input or len(user_input.strip()) == 0:
            return jsonify({"error": "请输入内容"}), 400

        if len(user_input) > 10000:  # 限制输入长度
            return jsonify({"error": "输入内容过长，请控制在10000字符以内"}), 400

        # 动态获取API Key
        api_key = get_api_key()
        if not api_key:
            return jsonify({"error": "请先配置API Key"}), 401

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 统一使用一套提示词生成逻辑
        professional_prompt = generate_prompt(user_input, style)
        max_tokens = 800

        payload = {
            "model": "glm-4.7-flash",
            "messages": [
                {"role": "user", "content": professional_prompt}
            ],
            "thinking": {
                "type": "disabled"
            },
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": max_tokens
        }

        # 增加重试机制
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"调用API，尝试 {attempt + 1}/{max_retries}，输入: {user_input}")

                timeout = 30 + (attempt * 15)

                response = requests.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )

                logger.info(f"API状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()

                    # 检查响应结构
                    logger.info(f"API响应结构: {list(result.keys())}")
                    logger.info(f"完整API响应: {json.dumps(result, ensure_ascii=False)}")

                    # 提取content
                    if "choices" in result and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        logger.info(f"第一个choice的结构: {list(choice.keys())}")
                        if "message" in choice:
                            message = choice["message"]
                            logger.info(f"message的结构: {list(message.keys())}")
                            logger.info(f"message的完整内容: {json.dumps(message, ensure_ascii=False)}")

                            # 优先尝试content字段
                            content = message.get("content", "")

                            # 如果content为空,尝试reasoning_content字段
                            if not content or len(content.strip()) == 0:
                                content = message.get("reasoning_content", "")
                                logger.info(f"使用reasoning_content, 长度: {len(content)}")
                        else:
                            content = ""
                    else:
                        logger.error(f"API响应缺少choices字段: {result}")
                        raise ValueError("API响应格式异常")

                    logger.info(f"API返回content长度: {len(content)} 字符")

                    # 如果内容为空，尝试其他字段
                    if not content:
                        logger.warning("API返回内容为空，尝试其他字段")
                        # 检查是否有thinking字段
                        if "thinking" in result.get("choices", [{}])[0].get("message", {}):
                            thinking = result["choices"][0]["message"].get("thinking", "")
                            logger.info(f"Thinking内容长度: {len(thinking)} 字符")

                    # 如果还是空的，返回默认提示词
                    if not content or len(content.strip()) < 10:
                        logger.warning("API返回内容不足，使用默认提示词")
                        # 使用用户输入生成简单提示词
                        content = f"【英文正向提示词】\nmasterpiece, best quality, 8k, ultra detailed, {user_input}\n\n【英文负向提示词】\nlow quality, worst quality, blurry, bad anatomy, deformed, watermark, text"

                    # 直接使用文本解析（API返回两行文本格式）
                    return parse_text_response(content, user_input)

                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue

                elif response.status_code == 401:
                    error_msg = "API Key 无效或已过期"
                    print(f"API Key验证失败")
                    return jsonify({"error": error_msg}), 401

                else:
                    error_msg = f"API错误: {response.status_code}"
                    print(f"API调用失败: {error_msg}, 响应内容: {response.text}")
                    try:
                        error_detail = response.json()
                        print(f"详细错误信息: {error_detail}")
                        if 'error' in error_detail:
                            return jsonify({"error": f"{error_msg} - {error_detail['error']}"}), 400
                    except:
                        pass
                    return jsonify({"error": error_msg}), 400

            except requests.exceptions.Timeout:
                wait_time = (attempt + 1) * base_delay
                print(f"请求超时，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue

            except requests.exceptions.ConnectionError as e:
                wait_time = (attempt + 1) * base_delay
                print(f"连接错误: {str(e)}，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * base_delay
                    print(f"未知错误: {str(e)}，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"最终错误: {str(e)}")
                    return jsonify({"error": f"请求失败: {str(e)}"}), 500

        # 所有重试都失败
        return jsonify({"error": "API请求失败，请稍后再试或检查网络连接"}), 500

    except Exception as e:
        print(f"generate函数发生未捕获的异常: {str(e)}")  # 调试
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

def generate_prompt(user_input: str, style: Optional[str] = None) -> str:
    """生成统一的提示词 - 直接返回简单格式"""
    # 定义主流画风及其对应的提示词
    style_prompts = {
        "写实": "photorealistic, hyperrealistic, 8k, ultra detailed, realistic photography, sharp focus, high resolution, professional photography, natural lighting",
        "动漫": "anime style, manga style, vibrant colors, cel shading, clean lines, anime art, Japanese animation style, Studio Ghibli inspired",
        "插画": "illustration, digital illustration, flat design, vector art, colorful, artistic, clean composition, modern illustration style",
        "油画": "oil painting, impasto, brush strokes, canvas texture, classic art, painterly style, rich colors, traditional painting technique",
        "水彩": "watercolor painting, watercolor texture, soft edges, pastel colors, artistic wash, traditional watercolor technique, delicate",
        "素描": "pencil sketch, charcoal drawing, graphite, rough sketch, monochrome, hand drawn, detailed line art, sketch style",
        "3D渲染": "3D render, CGI, Octane render, ray tracing, 3D modeling, photorealistic 3D, smooth shading, high poly, modern 3D art",
        "赛博朋克": "cyberpunk, neon lights, futuristic, dystopian, sci-fi, high contrast, technological, blade runner style, holographic",
        "古风": "traditional Chinese art, ancient Chinese style, ink wash painting, traditional painting, oriental art, classic Chinese aesthetics",
        "像素": "pixel art, 8-bit, 16-bit, retro gaming, pixelated, nostalgic, indie game style",
        "卡通": "cartoon style, animated, colorful, stylized, fun, playful, character design, vibrant",
        "水墨": "ink wash painting, sumi-e, traditional Asian ink art, minimalist, fluid brushwork, artistic ink style"
    }

    # 如果用户选择了特定画风，添加到提示词中
    style_tags = ""
    if style and style in style_prompts:
        style_tags = f", {style_prompts[style]}"

    return f"""You are an AI image prompt generator. Generate English prompts for this description: {user_input}

Translate the description to English and generate detailed image prompts.

Output ONLY these two lines:

[English detailed positive prompt with quality tags and style keywords, translated from: {user_input}]{style_tags}

[Standard negative prompt with quality issues to avoid]

Requirements:
- Translate the description to English in the positive prompt
- Add relevant visual details, lighting, and composition keywords
- Include quality tags like: masterpiece, best quality, 8k, ultra detailed
- Separate all keywords with commas
- No Chinese text in the output
- Only output the two lines, nothing else

Example:
If input is "一只猫坐在窗边", output:
Line 1: masterpiece, best quality, 8k, ultra detailed, a cute cat sitting by the window, soft natural lighting, cozy atmosphere, detailed fur texture
Line 2: low quality, worst quality, blurry, bad anatomy, deformed, distorted, disfigured, bad proportions, extra limbs, missing limbs, watermark, text

Just output the two lines. No thinking, no explanation.
"""

def parse_text_response(content, user_input):
    """解析简单两行格式的提示词"""
    print(f"解析提示词，原始内容长度: {len(content)}")
    print(f"原始内容: {content}")

    positive = ""
    negative = ""

    # 清理可能的 markdown 代码块标记
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1]
    if content.endswith('```'):
        content = content.rsplit('\n', 1)[0]
    content = content.strip()

    # 按行分割
    lines = content.split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    print(f"分割后共 {len(lines)} 行")

    # 直接使用前两行（禁用思考模式后，content 会直接包含答案）
    if len(lines) > 0:
        positive = lines[0].strip('"')
        print(f"第一行（正向）: {positive[:100]}...")

    if len(lines) > 1:
        negative = lines[1].strip('"')
        print(f"第二行（负向）: {negative[:100]}...")

    # 如果没有提取到，使用默认值
    if not positive or len(positive) < 5:
        print("未能提取到正向提示词,使用默认值")
        positive = f"masterpiece, best quality, 8k, ultra detailed, {user_input}"

    if not negative or len(negative) < 10:
        print("未能提取到负向提示词,使用默认值")
        negative = "low quality, worst quality, blurry, bad anatomy, deformed, distorted, disfigured, bad proportions, extra limbs, missing limbs, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation, watermark, text, signature, logo, username, artist name, crop, cropped, out of frame, cut off, tiling, poorly drawn feet, poorly drawn face, out of focus, long neck, extra fingers, fewer fingers, bad hands, missing fingers, fused fingers, too many fingers, extra arms, extra legs, extra hands, malformed limbs, bad perspective, warped, error, jpeg artifacts, lowres, monochrome, grayscale"

    response_data = {
        "positive_prompt": positive,
        "negative_prompt": negative,
        "scene_analysis": "",
        "art_style": "",
        "lighting": "",
        "composition": "",
        "technical_notes": ""
    }

    print(f"解析完成 - 正向提示词长度: {len(positive)}, 负向提示词长度: {len(negative)}")

    return jsonify(response_data)

@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    """调用火山引擎生成图像"""
    data = request.get_json()
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({"error": "请输入提示词"}), 400

    # 动态获取火山引擎API Key
    volc_api_key = get_volc_api_key()
    if not volc_api_key:
        return jsonify({"error": "请先配置火山引擎API Key"}), 400


    try:
        # 确定使用的模型：推理接入点ID 或 默认模型名称
        model_id = VOLC_ENDPOINT_ID if VOLC_ENDPOINT_ID else VOLC_DEFAULT_IMAGE_MODEL
        model_type = "推理接入点" if VOLC_ENDPOINT_ID else "默认模型"

        print(f"调用火山引擎API生成图像,提示词: {prompt}")
        print(f"使用{model_type}: {model_id}")

        # 构建推理接入点的完整URL
        # 图像生成推理接入点使用专用端点
        api_url = f"{VOLC_ENDPOINT_BASE}/api/v3/images/generations"

        headers = {
            "Authorization": f"Bearer {volc_api_key}",
            "Content-Type": "application/json"
        }

        print(f"请求URL: {api_url}")
        print(f"请求头: {headers}")

        # doubao-seedream 图像生成模型的请求格式
        payload = {
            "model": model_id,
            "prompt": prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": "2K",
            "stream": False,
            "watermark": True
        }

        print(f"请求体: {payload}")


        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=60
        )


        print(f"火山引擎API状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"火山引擎API响应: {result}")

            # 解析响应，获取图像URL
            image_url = ""

            # 图像生成 API 的响应格式
            # 标准格式：{"data": [{"url": "..."}]}
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0].get("url", "")

            # 如果上面没找到，尝试其他格式
            if not image_url:
                # 尝试直接在顶层查找 url 字段
                image_url = result.get("url", "")

            # 再尝试从 images 数组中查找
            if not image_url and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0].get("url", "")

            # 最后尝试从 choices 中查找（兼容旧格式）
            if not image_url and "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                if isinstance(content, str):
                    image_url = content
                elif isinstance(content, list) and len(content) > 0:
                    for item in content:
                        if isinstance(item, dict):
                            image_url = item.get("image_url", "")
                            if image_url:
                                break

            if not image_url:
                print(f"未能从响应中解析出图像URL，完整响应: {result}")
                return jsonify({"error": "未能获取图像URL，请检查推理接入点配置\n\n响应结构可能不符合预期"}), 500

            # 返回生成的图像URL
            return jsonify({
                "success": True,
                "image_url": image_url,
                "prompt": prompt,
                "message": "图像生成成功"
            })


        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "请求参数错误")
            print(f"火山引擎400错误详情: {error_data}")

            # 检查是否是模型不支持当前 API 的问题
            if "does not support this api" in error_msg:
                model_name = error_data.get("error", {}).get("param", "")
                return jsonify({
                    "error": f"模型配置错误\n\n错误信息: {error_msg}\n\n当前使用的模型 ({model_name}) 不支持图像生成API。\n\n解决方案：\n1. 如果使用推理接入点，请检查推理接入点是否配置为图像生成类型\n2. 如果使用默认模型，可以尝试清空推理接入点配置，使用默认的 doubao-seedream 模型\n3. 访问火山引擎ARK控制台: https://console.volcengine.com/ark\n4. 创建或检查图像生成推理接入点（选择支持图像生成的模型如 doubao-seedream 系列）"
                }), 400

            return jsonify({"error": f"请求参数错误: {error_msg}\n\n请检查：\n1. API Key是否正确\n2. 模型配置是否正确\n3. API请求格式是否正确\n\n完整错误信息: {error_data}"}), 400
        elif response.status_code == 401:
            return jsonify({"error": "API Key 无效或已过期\n\n请检查：\n1. 火山引擎API Key是否正确\n2. API Key是否已激活\n3. 账户是否有足够余额"}), 401
        elif response.status_code == 404:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "推理接入点不存在或无访问权限")
            return jsonify({"error": f"推理接入点配置错误\n\n{error_msg}\n\n请检查：\n1. 推理接入点ID是否正确（格式：ep-xxxxxx）\n2. 推理接入点是否为图像生成模型\n3. 推理接入点是否已上线运行"}), 404
        elif response.status_code == 429:
            return jsonify({"error": "API调用频率超限，请稍后再试"}), 429
        else:
            error_msg = f"API错误: {response.status_code}"
            print(f"火山引擎API调用失败: {error_msg}, 响应内容: {response.text}")
            return jsonify({"error": error_msg}), 500


    except requests.exceptions.Timeout:
        print("火山引擎API请求超时")
        return jsonify({"error": "请求超时，请稍后再试"}), 500
    except Exception as e:
        print(f"火山引擎API错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"生成失败: {str(e)}"}), 500






@app.route('/api/download_image', methods=['POST'])
def download_image():
    """代理下载图像，解决跨域问题"""
    data = request.get_json()
    image_url = data.get('image_url', '')

    if not image_url:
        return jsonify({"error": "没有提供图片URL"}), 400

    try:
        # 下载图片
        print(f"开始下载图片: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # 获取图片内容
        image_data = response.content
        content_type = response.headers.get('Content-Type', 'image/png')

        # 将图片数据转换为base64
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        return jsonify({
            "success": True,
            "image_data": f"data:{content_type};base64,{image_base64}"
        })

    except Exception as e:
        print(f"下载图片失败: {str(e)}")
        return jsonify({"error": f"下载失败: {str(e)}"}), 500



@app.route('/api/save_history', methods=['POST'])
def save_history():
    """保存历史记录到文件"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "没有数据"}), 400

    try:
        # 格式化记录
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 统一记录格式：只保留基本信息
        record = f"""
{'='*60}
时间: {timestamp}
{'='*60}
用户输入: {data.get('input', '')}
{'-'*60}
正向提示词: {data.get('positive', '')}
{'-'*60}
负向提示词: {data.get('negative', '')}
{'-'*60}
"""


        # 追加到文件
        with open(str(HISTORY_FILE), 'a', encoding='utf-8') as f:
            f.write(record)

        print(f"已保存记录到 {HISTORY_FILE}")  # 调试
        return jsonify({"success": True})
    except Exception as e:
        print(f"保存失败: {e}")  # 调试
        return jsonify({"error": f"保存失败: {str(e)}"}), 500

@app.route('/api/load_history', methods=['GET'])
def load_history():
    """从文件加载历史记录"""
    try:
        if not HISTORY_FILE.exists():
            return jsonify({"history": []})

        with open(str(HISTORY_FILE), 'r', encoding='utf-8') as f:
            content = f.read()

        # 简化的解析（实际使用时可以更复杂）
        records = []
        lines = content.split('\n')

        current_record = {}
        for line in lines:
            if line.startswith('用户输入: '):
                current_record['input'] = line.replace('用户输入: ', '').strip()
            elif line.startswith('正向提示词: '):
                current_record['positive'] = line.replace('正向提示词: ', '').strip()
            elif line.startswith('负向提示词: '):
                current_record['negative'] = line.replace('负向提示词: ', '').strip()
                if current_record:
                    records.append(current_record)
                    current_record = {}

        # 只保留最近50条记录
        records = records[:50]

        return jsonify({"history": records})

    except Exception as e:
        print(f"加载历史记录失败: {e}")  # 调试
        return jsonify({"history": []})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """清除历史记录文件"""
    try:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
            print(f"已清除历史记录文件 {HISTORY_FILE}")  # 调试
        return jsonify({"success": True})
    except Exception as e:
        print(f"清除失败: {e}")  # 调试
        return jsonify({"error": f"清除失败: {str(e)}"}), 500

@app.route('/favicon.ico')
def favicon():
    """处理浏览器自动请求的favicon"""
    return '', 204

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({"error": "404 - 资源未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    print(f"500错误详情: {str(error)}")  # 打印详细错误信息
    import traceback
    traceback.print_exc()  # 打印完整的错误堆栈
    return jsonify({"error": f"500 - 服务器内部错误: {str(error)}"}), 500

if __name__ == '__main__':
    # 检查API Key是否设置
    if not get_api_key():
        print("API Key未设置，请通过启动器设置或通过环境变量设置")

    app.run(debug=False, port=5000, host='127.0.0.1', use_reloader=False)
