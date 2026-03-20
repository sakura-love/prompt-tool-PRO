# app.py
from flask import Flask, render_template, request, jsonify
import requests
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
import sys

# 确定运行路径（打包或开发环境）
if getattr(sys, 'frozen', False):
    # 打包后的环境
    BASE_DIR = Path(sys._MEIPASS)
    # 可写目录（用于历史记录）
    WORK_DIR = Path(sys.executable).parent
else:
    # 开发环境
    BASE_DIR = Path(__file__).parent
    WORK_DIR = BASE_DIR

app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'), static_folder=str(BASE_DIR / 'static'))

# 配置：用户需自行填写API Key
API_KEY = os.getenv('API_KEY', '')  # 通过启动器设置API Key
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 火山引擎配置
VOLC_API_KEY = os.getenv('VOLC_API_KEY', '')  # 通过启动器设置火山引擎API Key
VOLC_IMAGE_API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
VOLC_IMAGE_MODEL = "doubao-seedream-4-5-251128"  # 图像生成模型

# 历史记录文件路径（放在可写目录）
HISTORY_FILE = WORK_DIR / "prompt_history.txt"

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_input = data.get('input', '')
    style = data.get('style', None)

    if not user_input:
        return jsonify({"error": "请输入内容"}), 400

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 统一使用一套提示词生成逻辑
    professional_prompt = generate_prompt(user_input, style)
    max_tokens = 800

    payload = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "user", "content": professional_prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": max_tokens
    }

    # 增加重试机制
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"调用API，尝试 {attempt + 1}/{max_retries}，输入: {user_input}")

            timeout = 30 + (attempt * 15)

            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=timeout
            )

            print(f"API状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"API返回内容长度: {len(content)} 字符")  # 调试

                # 解析逻辑...
                try:
                    # 清理可能的markdown代码块标记
                    content = re.sub(r'```json\s*', '', content)
                    content = re.sub(r'```\s*', '', content)
                    content = content.strip()

                    data = json.loads(content)

                    # 提取关键字段
                    positive = data.get("positive_prompt", "")
                    negative = data.get("negative_prompt", "")
                    analysis = data.get("scene_analysis", "")

                    # 如果字段缺失，尝试从其他字段补充
                    if not positive and "positive" in data:
                        positive = data["positive"]
                    if not negative and "negative" in data:
                        negative = data["negative"]

                    # 确保有基础内容
                    if not positive:
                        positive = f"masterpiece, best quality, 8k, ultra detailed, {user_input}"
                    if not negative:
                        negative = "low quality, blurry, bad anatomy, deformed, watermark, text, ugly"

                    # 提取其他有用信息
                    art_style = data.get("art_style", "")
                    lighting = data.get("lighting", "")
                    composition = data.get("composition", "")
                    technical_notes = data.get("technical_notes", "")

                    # 生成多个变体
                    variants = generate_variants(positive, user_input)
                    data["variants"] = variants

                    response_data = {
                        "positive_prompt": positive,
                        "negative_prompt": negative,
                        "scene_analysis": analysis,
                        "art_style": art_style,
                        "lighting": lighting,
                        "composition": composition,
                        "technical_notes": technical_notes
                    }

                    # 如果有变体，添加到响应中
                    if "variants" in data:
                        response_data["variants"] = data["variants"]

                    print(f"解析成功 - 正向提示词长度: {len(positive)}")  # 调试

                    return jsonify(response_data)

                except json.JSONDecodeError:
                    print(f"JSON解析失败，尝试文本解析")  # 调试
                    return parse_text_response(content, user_input)

            elif response.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"速率限制，等待 {wait_time} 秒...")
                time.sleep(wait_time)
                continue

            else:
                error_msg = f"API错误: {response.status_code}"
                print(f"API调用失败: {error_msg}, 响应内容: {response.text}")
                try:
                    error_detail = response.json()
                    print(f"详细错误信息: {error_detail}")
                    if 'error' in error_detail:
                        return jsonify({"error": f"{error_msg} - {error_detail['error']}"}), 500
                except:
                    pass
                return jsonify({"error": error_msg}), 500

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

def generate_prompt(user_input, style=None):
    """生成统一的提示词"""
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
    style_instruction = ""
    if style and style in style_prompts:
        style_instruction = f"""

【重要要求】
用户选择了特定的画风：{style}
在正向提示词中必须包含以下画风关键词：{style_prompts[style]}
确保生成的图像符合所选画风的特征。"""

    return f"""
你是一位专业的AI绘画提示词工程师，擅长为各种AI绘画工具生成高质量、结构化的提示词。你的任务是生成丰富、详细、多维度的提示词。

用户输入：{user_input}{style_instruction}

请根据以下专业标准，生成详细的提示词：

【专业分析】
1. 核心主体：分析用户描述的主要对象、特征、属性
2. 详细描述：添加材质、颜色、纹理、姿态、表情、服装、饰品等细节
3. 场景环境：描述背景、空间、氛围、时间、天气、季节、地理位置
4. 光照效果：指定光源类型、方向、强度、阴影、色调、光晕、反射
5. 艺术风格：{"严格按照用户选择的画风要求" if style else "指定艺术流派、艺术家、媒介（根据需要选择合适风格）"}
6. 技术参数：分辨率、画质、细节等级、渲染引擎、风格化程度
7. 构图视角：镜头类型、角度、景深、比例、对称性、黄金分割
8. 情绪氛围：表达的情感、氛围、故事性、叙事感



【结构化输出】
请以JSON格式返回，包含以下字段：
{{
    "positive_prompt": "英文正向提示词（详细版）",
    "negative_prompt": "英文负向提示词（排除所有不想要的元素）",
    "scene_analysis": "详细的场景分析和建议",
    "art_style": "艺术风格建议",
    "lighting": "光照效果建议",
    
    
}}


【要求】
1. 必须返回JSON格式
2. 所有提示词必须是英文
3. 每个版本的提示词都要有独特性
4. 包含足够的细节和修饰词
5. 符合各AI工具的最佳实践
6. 生成详细且全面的提示词
{"7. 必须严格按照用户选择的画风生成提示词" if style else "7. 选择最适合的绘画风格"}
"""

def generate_variants(positive_prompt, user_input):
    """根据基础prompt生成多个变体"""
    variants = {
        "basic": positive_prompt,
        "detailed": positive_prompt,
        "artistic": positive_prompt,
        "technical": positive_prompt,
        "creative": positive_prompt
    }

    # 根据用户输入添加额外元素
    if "精灵" in user_input or "fairy" in user_input.lower():
        variants["artistic"] += ", ethereal, magical, fantasy art, digital painting"
        variants["creative"] += ", surreal, dreamlike, otherworldly, magical atmosphere"

    if "赛博朋克" in user_input or "cyberpunk" in user_input.lower():
        variants["technical"] += ", neon lights, futuristic, dystopian, high contrast"
        variants["creative"] += ", holographic, cybernetic, augmented reality, glitch effects"

    if "森林" in user_input or "forest" in user_input.lower():
        variants["detailed"] += ", ancient trees, moss, ferns, dappled sunlight, mist"
        variants["artistic"] += ", impressionist, nature painting, organic textures"

    # 添加质量修饰词
    for key in variants:
        variants[key] += ", masterpiece, best quality, 8k"

    return variants

def parse_text_response(content, user_input):
    """最激进的解析 - 提取所有可能的提示词内容"""
    print(f"使用激进解析，原始内容长度: {len(content)}")  # 调试

    # 首先尝试提取所有可能的提示词部分
    # 假设格式是：【正向提示词】内容\n【负向提示词】内容\n...

    # 尝试用正则表达式提取
    import re

    # 提取正向提示词（从【正向提示词】后到下一个【或结尾）
    positive_match = re.search(r'【正向提示词】\s*(.*?)(?:\n【|$)', content, re.DOTALL)
    if positive_match:
        positive = positive_match.group(1).strip()
    else:
        # 如果没有找到，尝试提取所有可能的提示词内容
        #假设提示词内容是逗号分隔的英文短语
        positive_parts = []
        for line in content.split('\n'):
            line = line.strip()
            if line and len(line) > 10 and not line.startswith('【'):
                # 检查是否是英文提示词（包含逗号）
                if ',' in line or len(line.split()) > 2:
                    positive_parts.append(line)

        positive = ', '.join(positive_parts) if positive_parts else f"masterpiece, best quality, 8k, ultra detailed, {user_input}"

    # 提取负向提示词
    negative_match = re.search(r'【负向提示词】\s*(.*?)(?:\n【|$)', content, re.DOTALL)
    if negative_match:
        negative = negative_match.group(1).strip()
    else:
        negative = "low quality, blurry, bad anatomy, deformed, watermark, text, ugly"

    # 提取分析
    analysis_match = re.search(r'【.*分析】\s*(.*?)(?:\n【|$)', content, re.DOTALL)
    if analysis_match:
        analysis = analysis_match.group(1).strip()
    else:
        analysis = f"用户输入: {user_input}"

    # 生成变体
    variants = generate_variants(positive, user_input)

    response_data = {
        "positive_prompt": positive,
        "negative_prompt": negative,
        "scene_analysis": analysis,
        "art_style": "",
        "lighting": "",
        "composition": "",
        "technical_notes": ""
    }

    if variants:
        response_data["variants"] = variants

    print(f"激进解析完成 - 正向提示词长度: {len(positive)}")  # 调试

    return jsonify(response_data)

@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    """调用火山引擎生成图像"""
    data = request.get_json()
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({"error": "请输入提示词"}), 400

    if not VOLC_API_KEY:
        return jsonify({"error": "请先配置火山引擎API Key"}), 400

    headers = {
        "Authorization": f"Bearer {VOLC_API_KEY}",
        "Content-Type": "application/json"
    }

    # 火山引擎图像生成API - 使用 Seedream 模型
    payload = {
        "model": VOLC_IMAGE_MODEL,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": "2K",
        "stream": False,
        "watermark": True
    }

    try:
        print(f"调用火山引擎API生成图像,提示词: {prompt}")

        response = requests.post(
            VOLC_IMAGE_API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        print(f"火山引擎API状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # 返回生成的图像URL
            return jsonify({
                "success": True,
                "image_url": result.get("data", [{}])[0].get("url", ""),
                "prompt": prompt,
                "message": "图像生成成功"
            })

        elif response.status_code == 401:
            return jsonify({"error": "API Key 无效或已过期"}), 401
        elif response.status_code == 429:
            return jsonify({"error": "API调用频率超限,请稍后再试"}), 429
        else:
            error_msg = f"API错误: {response.status_code}"
            print(f"火山引擎API调用失败: {error_msg}, 响应内容: {response.text}")
            return jsonify({"error": error_msg}), 500

    except requests.exceptions.Timeout:
        print("火山引擎API请求超时")
        return jsonify({"error": "请求超时，请稍后再试"}), 500
    except Exception as e:
        print(f"火山引擎API错误: {str(e)}")
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

        # 统一记录格式：包含所有信息
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
场景分析: {data.get('scene_analysis', '')}
{'-'*60}
艺术风格: {data.get('art_style', '')}
{'-'*60}
光照效果: {data.get('lighting', '')}
{'-'*60}
构图建议: {data.get('composition', '')}
{'-'*60}
技术备注: {data.get('technical_notes', '')}
{'-'*60}
"""
        # 如果有变体，也保存
        if 'variants' in data:
            record += "变体提示词:\n"
            for variant_name, variant_text in data['variants'].items():
                record += f"  {variant_name}: {variant_text}\n"
            record += f"{'-'*60}\n"

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
    return jsonify({"error": "500 - 服务器内部错误"}), 500

if __name__ == '__main__':
    # 检查API Key是否设置
    if not API_KEY:
        print("API Key未设置，请通过启动器设置")

    app.run(debug=False, port=5000, host='127.0.0.1', use_reloader=False)
