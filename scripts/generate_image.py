import argparse
import requests
import time
import json
import os
from urllib.parse import urlparse

BASE_URL = "https://ixspy.com"

def get_headers(api_key, is_json=True):
    headers = {"Authorization": f"Bearer {api_key}"}
    if is_json:
        headers["Content-Type"] = "application/json"
    return headers

def upload_image_if_local(file_path_or_url, api_key):
    """如果传入的是本地文件路径，则上传至 API 并返回 URL；如果是 URL，则直接返回。"""
    if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
        return file_path_or_url
    
    if not os.path.isfile(file_path_or_url):
        raise FileNotFoundError(f"Local file not found: {file_path_or_url}")
        
    print(f"[*] Uploading local image: {file_path_or_url}...")
    url = f"{BASE_URL}/ai-tool/api/v1/images/upload"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    with open(file_path_or_url, "rb") as f:
        files = {"image": f}
        response = requests.post(url, headers=headers, files=files)
        
    data = response.json()
    if data.get("error", {}).get("code") == 0:
        cdn_url = data["data"]["url"]
        print(f"[+] Upload successful. CDN URL: {cdn_url}")
        return cdn_url
    else:
        raise Exception(f"Image upload failed: {data.get('error', {}).get('message', 'Unknown error')}")

def create_task(api_key, task_type, payload):
    """发起作图任务"""
    print(f"[*] Creating task of type '{task_type}'...")
    url = f"{BASE_URL}/ai-tool/api/v1/images/generations/{task_type}"
    response = requests.post(url, headers=get_headers(api_key), json=payload)
    data = response.json()
    
    if data.get("error", {}).get("code") == 0:
        task_id = data["data"]["task_id"]
        print(f"[+] Task created successfully. Task ID: {task_id}")
        return task_id
    else:
        raise Exception(f"Task creation failed: {data.get('error', {}).get('message', 'Unknown error')} - {json.dumps(data)}")

def poll_task_status(api_key, task_id, interval=10):
    """轮询任务状态"""
    print(f"[*] Polling status for task {task_id}...")
    url = f"{BASE_URL}/ai-tool/api/v1/images/generations/tasks/{task_id}"
    
    while True:
        response = requests.get(url, headers=get_headers(api_key, is_json=False))
        data = response.json()
        
        if data.get("error", {}).get("code") != 0:
            raise Exception(f"Failed to fetch task status: {data.get('error', {}).get('message', 'Unknown error')}")
            
        status = data["data"]["status"]
        print(f"    - Status: {status}")
        
        if status == "completed":
            print(f"[+] Task {task_id} completed!")
            return data["data"]
        elif status == "error":
            raise Exception(f"Task {task_id} failed on server side.")
            
        time.sleep(interval)

def get_task_status(api_key, task_id):
    """单次查询任务状态"""
    url = f"{BASE_URL}/ai-tool/api/v1/images/generations/tasks/{task_id}"
    response = requests.get(url, headers=get_headers(api_key, is_json=False))
    data = response.json()
    if data.get("error", {}).get("code") == 0:
        return data["data"]
    else:
        raise Exception(f"Failed to fetch task status: {data.get('error', {}).get('message', 'Unknown error')}")

def list_tasks(api_key, limit=20):
    """获取任务列表"""
    url = f"{BASE_URL}/ai-tool/api/v1/images/tasks-list?page=1&page_size={limit}"
    print(url, get_headers(api_key, is_json=False))
    response = requests.get(url, headers=get_headers(api_key, is_json=False))
    data = response.json()
    if data.get("error", {}).get("code") == 0:
        return data["data"]
    else:
        raise Exception(f"Failed to fetch tasks list: {data.get('error', {}).get('message', 'Unknown error')}")

def get_upscaled_image(api_key, task_id):
    """获取高清图片"""
    print(f"[*] Fetching upscaled image for task {task_id}...")
    url = f"{BASE_URL}/ai-tool/api/v1/images/upscale/{task_id}"
    response = requests.get(url, headers=get_headers(api_key, is_json=False))
    data = response.json()
    
    if data.get("error", {}).get("code") == 0:
        return data["data"]["hd_image_url"]
    else:
        print(f"[-] Failed to get upscaled image: {data.get('error', {}).get('message', '')}. Will fallback to standard definition.")
        return None

def download_image(image_url, output_dir, task_id):
    """下载图片到本地"""
    print(f"[*] Downloading image from {image_url}...")
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 尝试从 URL 提取扩展名，默认用 .jpg
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1]
        if not ext:
            ext = ".jpg"
            
        filename = f"ixspy_task_{task_id}_{int(time.time())}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"[+] Image successfully downloaded to: {filepath}")
        return filepath
    else:
        raise Exception(f"Failed to download image from {image_url}. Status code: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="IXSPY AI Image Generation CLI Script")
    parser.add_argument("--action", choices=["generate", "status", "list_tasks", "download"], default="generate", help="Action to perform")
    parser.add_argument("--task_id", help="Task ID for status or download action")
    parser.add_argument("--limit", type=int, default=10, help="Number of tasks to fetch for list_tasks")
    
    parser.add_argument("--api_key", help="Your IXSPY API Key (Overrides environment variable if provided)")
    parser.add_argument("--type", choices=[
        "custom_composition_multi", "custom_composition", "scene_replacement", 
        "product_replacement", "product_recoloring", "partial_redraw", 
        "smart_expand", "translation", "ai_upscale_2k"
    ], help="Type of generation task")
    
    # API 参数
    parser.add_argument("--original_image", nargs="*", help="Path or URL of the original image(s). Multiple allowed for custom_composition_multi")
    parser.add_argument("--reference_image", help="Path or URL of the reference image")
    parser.add_argument("--prompt", help="Text prompt for the generation")
    parser.add_argument("--ratios", default="auto", help="Aspect ratio (e.g., auto, 1:1, 16:9)")
    parser.add_argument("--color", help="Target color for product_recoloring (e.g., #ff4500ff)")
    parser.add_argument("--direction", help="Direction for smart_expand (e.g., top, left, auto)")
    parser.add_argument("--source_language", help="Source language for translation")
    parser.add_argument("--target_language", help="Target language for translation")
    
    # 脚本控制参数
    parser.add_argument("--output_dir", default=".", help="Directory to save the downloaded image")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("IXSPY_API_KEY")
    
    if not api_key:
        error_result = {
            "status": "error",
            "message": "API Key is missing! Please set the IXSPY_API_KEY environment variable.\n\nHow to set it:\n- Windows (Command Prompt): set IXSPY_API_KEY=your_api_key_here\n- Windows (PowerShell): $env:IXSPY_API_KEY=\"your_api_key_here\"\n- macOS/Linux (Terminal): export IXSPY_API_KEY=\"your_api_key_here\""
        }
        print("\n=== ERROR ===")
        print(json.dumps(error_result, indent=2))
        exit(1)
        
    try:
        if args.action == "status":
            if not args.task_id:
                raise Exception("--task_id is required for action 'status'")
            status_data = get_task_status(api_key, args.task_id)
            print("\n=== TASK STATUS ===")
            print(json.dumps(status_data, indent=2, ensure_ascii=False))
            
        elif args.action == "list_tasks":
            tasks_data = list_tasks(api_key, args.limit)
            print("\n=== TASK LIST ===")
            print(json.dumps(tasks_data, indent=2, ensure_ascii=False))
            
        elif args.action == "download":
            if not args.task_id:
                raise Exception("--task_id is required for action 'download'")
            
            final_image_url = get_upscaled_image(api_key, args.task_id)
            if not final_image_url:
                # fallback to checking normal status for sd_image_url
                status_data = get_task_status(api_key, args.task_id)
                final_image_url = status_data.get("sd_image_url")
                
            if not final_image_url:
                raise Exception(f"No completed image URL found for task {args.task_id}")
                
            output_filepath = download_image(final_image_url, os.path.abspath(args.output_dir), args.task_id)
            result = {
                "status": "success",
                "task_id": args.task_id,
                "url": final_image_url,
                "local_path": output_filepath
            }
            print("\n=== DOWNLOAD RESULT ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.action == "generate":
            if not args.type:
                raise Exception("the following arguments are required: --type for action 'generate'")
            
            payload = {}
            # 1. 处理上传参数
            if args.original_image:
                urls = []
                for img in args.original_image:
                    urls.append(upload_image_if_local(img, api_key))
                if args.type == "custom_composition_multi":
                    payload["original_image"] = urls
                else:
                    payload["original_image"] = urls[0] if urls else None

            if args.reference_image:
                payload["reference_image"] = upload_image_if_local(args.reference_image, api_key)
                
            # 2. 组装其他必填/选填参数
            if args.prompt: payload["prompt"] = args.prompt
            if args.ratios: payload["ratios"] = args.ratios
            if args.color: payload["color"] = args.color
            if args.direction: payload["direction"] = args.direction
            if args.source_language: payload["source_language"] = args.source_language
            if args.target_language: payload["target_language"] = args.target_language
            
            # 3. 发起任务
            task_id = create_task(api_key, args.type, payload)
            
            # 4. 轮询状态
            task_data = poll_task_status(api_key, task_id)
            
            # 5. 获取图片 URL
            final_image_url = None
            hd_url = get_upscaled_image(api_key, task_id)
            if hd_url:
                final_image_url = hd_url
            else:
                final_image_url = task_data.get("sd_image_url")
                
            if not final_image_url:
                raise Exception("Task completed but no image URL was returned.")
                
            # 6. 下载图片
            output_filepath = download_image(final_image_url, os.path.abspath(args.output_dir), task_id)
            
            # 最终输出结果，方便大模型解析
            result = {
                "status": "success",
                "task_id": task_id,
                "url": final_image_url,
                "local_path": output_filepath
            }
            print("\n=== FINAL RESULT ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print("\n=== ERROR ===")
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        exit(1)

if __name__ == "__main__":
    main()
