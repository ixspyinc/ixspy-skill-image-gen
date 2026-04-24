---
name: ixspy-image-gen
description: Use this skill when the user wants to generate AI images, such as replacing image backgrounds, recoloring products, smart expanding images, or creating custom compositions using the IXSPY AI API. Whenever a user asks to modify an image using AI features like "change color", "replace background", "redraw part of image", or "translate text in image", this skill should be invoked. It can also be used to check task status, list recent tasks, and download high-resolution results for existing tasks.
---

# IXSPY AI Image Generation Skill

This skill allows you to generate and manipulate images using the IXSPY AI Image API. The API supports various modes including custom composition, scene replacement, product recoloring, and more.
本技能允许你使用 IXSPY AI 图像 API 来生成和处理图片。API 支持包括自由构图、场景替换、商品换色等多种模式。

## Core Mechanism / 核心机制

This skill relies on a bundled Python script (`scripts/generate_image.py`) that handles the entire asynchronous API workflow for you:
本技能依赖一个内置的 Python 脚本 (`scripts/generate_image.py`)，它会为你处理整个异步 API 工作流：
1. It automatically uploads local image paths to the API to get CDN URLs. (自动上传本地图片至 API 以获取 CDN URL)
2. It submits the task and gets a `task_id`. (提交作图任务并获取 `task_id`)
3. It polls the task status every 10 seconds until it completes. (每 10 秒轮询一次状态直到任务完成)
4. It fetches the upscaled high-definition image and downloads it directly to the local filesystem. (获取高清图片并直接下载保存到本地)

**You DO NOT need to write `curl` commands or handle the polling yourself. Just execute the Python script.**
**你不需要手写 `curl` 命令，也不需要手动处理轮询。只需执行 Python 脚本即可。**

## Prerequisites / 前置条件

- **API Key Configuration**: This skill requires the `IXSPY_API_KEY` environment variable to be set.
  (本技能要求必须配置 `IXSPY_API_KEY` 环境变量。)
  - Before using the skill, or if the script reports a missing API Key, please instruct the user to set it using one of the following methods depending on their OS:
    (在使用本技能前，或者如果脚本报错提示缺少 API Key，请指导用户根据其操作系统使用以下方法之一进行设置：)
    - **Windows (Command Prompt):** `set IXSPY_API_KEY=your_api_key_here`
    - **Windows (PowerShell):** `$env:IXSPY_API_KEY="your_api_key_here"`
    - **macOS/Linux (Terminal):** `export IXSPY_API_KEY="your_api_key_here"`
- **Python**: Ensure Python is available in the environment to run the script. 
  (确保运行环境中装有 Python。)

## Actions (`--action`) / 操作类型

The script supports multiple actions, controlled by the `--action` parameter. The default action is `generate`.
脚本支持多种操作，由 `--action` 参数控制。默认操作为 `generate`（作图）。

1. `generate` (Default): The complete workflow (upload -> create task -> poll -> download).
   (默认：完整的作图工作流：上传 -> 创建任务 -> 轮询 -> 下载图片)
2. `status`: Check the status of a specific task.
   (查询状态：查询特定任务的状态)
   - Requires: `--task_id`
3. `list_tasks`: Fetch the recent tasks list.
   (获取任务列表：获取最近的作图任务)
   - Optional: `--limit` (default is 10)
4. `download`: Fetch the high-res URL and download the completed image directly.
   (下载图片：获取高清图片 URL 并直接下载完成的图片)
   - Requires: `--task_id`, `--output_dir`

## Available Task Types (`--type`) / 可用的任务类型 (For `generate` action)

You must map the user's intent to one of the following task types:
你需要将用户的意图映射到以下任务类型之一：

1. `custom_composition_multi` (Custom Composition Multi / 自由构图-多图): Combine multiple images (max 5) based on a prompt.
   - Requires: `--original_image` (multiple paths allowed), `--prompt`, `--ratios`
2. `custom_composition` (Custom Composition / 自由构图): Modify a single image based on a prompt.
   - Requires: `--original_image`, `--prompt`, `--ratios`
3. `scene_replacement` (Scene Replacement / 场景替换): Replace the background/scene of an image.
   - Requires: `--original_image`, `--ratios`, and AT LEAST ONE OF (`--prompt` or `--reference_image`)
4. `product_replacement` (Product Replacement / 商品替换): Place a product onto a reference background.
   - Requires: `--original_image`, `--reference_image`. Optional: `--prompt`
5. `product_recoloring` (Product Recoloring / 商品换色): Change the color of a product in the image.
   - Requires: `--original_image`, `--color` (must be hex with alpha, e.g., `#ff4500ff`). Optional: `--prompt` (e.g.,对鞋子换色)
6. `partial_redraw` (Partial Redraw / 局部重绘): Redraw parts of an image based on text.
   - Requires: `--original_image`, `--prompt`. Optional: `--reference_image`
7. `smart_expand` (Smart Expand / 智能延展): Expand the canvas of an image.
   - Requires: `--original_image`, `--direction` (e.g., top_left, top, auto), `--ratios`
8. `translation` (Image Translation / 图片翻译): Translate text within an image.
   - Requires: `--original_image`, `--source_language` (e.g., auto), `--target_language` (e.g., Chinese, English)
9. `ai_upscale_2k` (AI Upscale 2K / AI超清-2K): Upscale the image resolution.
   - Requires: `--original_image`

## How to use the script / 脚本使用方式

Use the Bash tool to execute the Python script.
使用 Bash 工具来执行此 Python 脚本。

### Basic Usage Pattern / 基础用法

```bash
# Ensure the API Key is set in the environment variable IXSPY_API_KEY first
# (确保 API Key 已经在环境变量 IXSPY_API_KEY 中配置好)

# To generate an image:
python ixspy-image-gen/scripts/generate_image.py \
  --action "generate" \
  --type "TASK_TYPE" \
  --original_image "path/to/local/image.jpg" \
  --output_dir "path/to/save/output_dir" \
  [--prompt "your descriptive prompt"] \
  [--ratios "16:9"] \
  [--reference_image "path/to/ref.jpg"] \
  [--color "#ff0000ff"]

# To check status:
python ixspy-image-gen/scripts/generate_image.py --action status --task_id 123

# To list tasks:
python ixspy-image-gen/scripts/generate_image.py --action list_tasks --limit 5

# To download high-res result:
python ixspy-image-gen/scripts/generate_image.py --action download --task_id 123 --output_dir "./outputs"
```

### Parsing the Output / 解析输出结果

For `generate` and `download` actions, it prints a final JSON block:
作图或下载完成后，它将打印如下的 JSON 块：

```json
=== FINAL RESULT ===
{
  "status": "success",
  "task_id": 123,
  "url": "https://cdn...",
  "local_path": "D:/outputs/ixspy_task_123_1680000000.jpg"
}
```

For `status` or `list_tasks`, it prints the respective JSON array or object.
如果是状态或列表查询，它会打印相应的数据 JSON。

If it fails, it will print:
如果失败了，它会打印：

```json
=== ERROR ===
{
  "status": "error",
  "message": "Task failed on server side."
}
```