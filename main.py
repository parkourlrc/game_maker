# -*- coding: utf-8 -*-

import requests
import json
import uuid
import websocket
import threading
import time

import urllib.parse
import random
import base64
import os
import sys
import shutil


def clear_output_folder():
    output_path = 'D:/ComfyUI/output'
    if os.path.exists(output_path) and os.path.isdir(output_path):
        shutil.rmtree(output_path)  # 删除目录及其内容
        os.makedirs(output_path)  # 重新创建output目录
        print("Output folder cleared.")
    else:
        os.makedirs(output_path)
        print("Output folder created.")

def save_image(image_data, filename):
    if not os.path.exists('output'):
        os.makedirs('output')

    image_data = base64.b64decode(image_data)
    with open(os.path.join('output', filename), 'wb',encoding='utf-8') as f:
        f.write(image_data)
    print(f"图像已保存：{filename}")

# ComfyUI服务器地址
comfyui_url = "http://127.0.0.1:8188"

# 生成唯一的client_id
client_id = str(uuid.uuid4())

# WebSocket连接
ws = None


def send_prompt():
    # 读取workflow_api.json文件
    with open('workflow_api.json', 'r',encoding='utf-8') as f:
        workflow_api = json.load(f)

# 添加随机种子和时间戳
    for node_id, node_data in workflow_api.items():
        if node_data.get('class_type') == 'KSampler':
            workflow_api[node_id]['inputs']['seed'] = random.randint(0, 0xffffffffffffffff)
            workflow_api[node_id]['inputs']['timestamp'] = int(time.time())
            print(f"已更新节点 {node_id} 的种子和时间戳")
            break
    else:
        print("未找到 KSampler 节点")
    # # 更新 workflow_api 中的特定节点的 'input' 下的 'text' 值
    # if '190' in workflow_api:
    #     workflow_api['190']['inputs']['text'] = prompts
    # else:
    #     print("未找到节点 ID 为 190 的节点")
    # 准备请求数据
    data = {
        "client_id": client_id,
        "prompt": workflow_api
    }

    # 清除ComfyUI缓存
    requests.post(f"{comfyui_url}/queue", json={"clear": True})

    # 发送POST请求
    response = requests.post(f"{comfyui_url}/prompt", json=data)

    if response.status_code == 200:
        result = response.json()
        print("请求成功发送！")
        print("任务ID:", result.get('prompt_id'))
        return result.get('prompt_id')
    else:
        print("请求失败：", response.status_code)
        print("错误信息：", response.text)
        return None

def handle_executed_message(data):
    outputs = data['data']['output']
    for node_id, node_output in outputs.items():
        print(f"节点 {node_id} 的输出：")
        for output_name, output_data in node_output.items():
            if isinstance(output_data, list) and output_data and isinstance(output_data[0], dict) and 'filename' in output_data[0]:
                for image in output_data:
                    print(f"  - 图像文件：{image['filename']}")
                    # 如果需要，这里可以添加代码来复制或移动文件
            elif isinstance(output_data, dict) and 'images' in output_data:
                for i, image_data in enumerate(output_data['images']):
                    filename = f"output_{node_id}_{i}.png"
                    save_image(image_data, filename)
            else:
                print(f"  - {output_name}: {output_data}")

# 处理WebSocket消息
def on_message(ws, message):
    if isinstance(message, str):
        try:
            data = json.loads(message)
            print("收到消息：", data)

            if data['type'] == 'status':
                print(f"队列中剩余任务数： {data['data']['status']['exec_info']['queue_remaining']}")
            elif data['type'] == 'execution_start':
                print(f"任务开始执行： {data['data']['prompt_id']}")
            elif data['type'] == 'executing':
                print(f"正在执行节点： {data['data']['node']}")
            elif data['type'] == 'progress':
                print(f"进度： {data['data']['value']}/{data['data']['max']}")
            elif data['type'] == 'executed':
                handle_executed_message(data)
            else:
                print(f"未知消息类型：{data['type']}")

        except json.JSONDecodeError:
            print("无法解析JSON数据")
    else:
        print("收到二进制数据(可能是图片预览)")

# 获取输出图片
def get_output_images(prompt_id):
    response = requests.get(f"{comfyui_url}/history/{prompt_id}")
    if response.status_code == 200:
        history = response.json()
        outputs = history[prompt_id]['outputs']
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for image in node_output['images']:
                    if image['type'] == 'output':
                        image_url = f"{comfyui_url}/view?filename={image['filename']}&type=output"
                        print(f"输出图片URL: {image_url}")

# WebSocket连接
def on_open(ws):
    print("WebSocket连接已建立")

def on_close(ws):
    print("WebSocket连接已关闭")

def on_error(ws, error):
    print(f"WebSocket错误： {error}")

# 启动WebSocket连接
def start_websocket():
    global ws
    websocket.enableTrace(True)

    # 构建正确的WebSocket URL
    parsed_url = urllib.parse.urlparse(comfyui_url)
    ws_scheme = 'wss' if parsed_url.scheme == 'https' else 'ws'
    ws_url = f"{ws_scheme}://{parsed_url.netloc}/ws?client_id={client_id}"

    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_open=on_open,
                                on_close=on_close,
                                on_error=on_error)
    ws.run_forever()


# 主程序
if __name__ == "__main__":

    clear_output_folder()

    if len(sys.argv) > 1 and sys.argv[1] == "autorun":
        print("Autorunning main.py")
    # 启动WebSocket连接
    websocket_thread = threading.Thread(target=start_websocket)
    websocket_thread.start()

    # 等待WebSocket连接建立
    time.sleep(2)

    # 发送绘图请求
    prompt_id = send_prompt()

    # 保持程序运行，直到用户中断
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序已终止")
        if ws:
            ws.close()