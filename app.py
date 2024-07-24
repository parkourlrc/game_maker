# app.py
from flask import Flask, request,jsonify
from flask_cors import CORS
import subprocess
import sys
import os
import json
import random
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)   # 设置日志级别

@app.route('/prompts', methods=['POST'])
def receive_prompt():
    data = request.get_json()
    prompts = data.get('prompts')
    app.logger.info("Received prompt: %s", prompts)  # 使用app.logger来记录日志
    # 更新 workflow_api.json 文件
    workflow_api_path = 'workflow_api.json'   
    # 读取现有 JSON 文件内容
    with open(workflow_api_path, 'r', encoding='utf-8') as f:
        workflow_api = json.load(f)

    if '190' in workflow_api:
        workflow_api["190"]["inputs"]["text"] = prompts
    else:
        print("未找到节点 ID 为 190 的节点")
    # 写入更新后的内容到 JSON 文件
    with open(workflow_api_path, 'w', encoding='utf-8') as f:
        json.dump(workflow_api, f, ensure_ascii=False, indent=4)  # ensure_ascii=False 用于保留中文等非ASCII字符，indent=4 使得输出更易读
    # 调用 main.py 并传递 prompts 参数的注释部分可以根据实际需要启用或继续注释
    # subprocess.Popen([sys.executable, 'main.py', 'autorun', prompts])
    return jsonify({ 'status': 'success', 'prompts': prompts }), 200
@app.route('/autorun')
def autorun():
    print("Received autorun request")
    # 启动 main.py 并传递 'autorun' 参数
    subprocess.Popen([sys.executable, 'main.py', 'autorun'])
    return "Autorun initiated", 200
@app.route('/get_files')
def get_files():
    output_dir = r'D:/ComfyUI/output' # 输出文件存放在这个目录
    #files = {'images': [], 'videos': []}
    files = {
        'image': None,
        'video': None
    }
    # 假设每次只生成一个图片和一个视频
    for filename in os.listdir(output_dir):
        #if filename.endswith(('.png', '.jpg', '.jpeg')):  # 假设图片文件是这些格式
        #    files['images'].append(filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            files['image'] = filename
        #elif filename.endswith('.mp4'):  # 假设视频文件是这个格式
        #    files['videos'].append(filename)
        elif filename.lower().endswith('.mp4'):
            files['video'] = filename
    return jsonify(files)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # 确保使用适当的端口