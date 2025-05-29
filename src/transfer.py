import os
import re
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def process_markdown_images(md_file_path, output_dir="output", image_dir="images"):
    """
    处理 Markdown 文件中的远程图片
    参数：
    - md_file_path: 原始 Markdown 文件路径
    - output_dir: 输出目录（包含处理后的 md 文件和图片目录）
    - image_dir: 图片存储目录名（相对于 output_dir）
    """
    # 创建输出目录结构
    output_path = Path(output_dir)
    image_path = output_path / image_dir
    image_path.mkdir(parents=True, exist_ok=True)

    # 读取原始 Markdown 内容
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 正则匹配所有图片链接
    pattern = r'!\[(.*?)\]\((.*?)\)'
    matches = re.findall(pattern, content)
    
    # 准备替换映射表
    url_mapping = {}
    
    def download_image(url, alt_text, index):
        """下载单个图片并返回本地路径"""
        try:
            # 处理特殊文件名字符
            clean_alt = re.sub(r'[\\/*?:"<>|]', '_', alt_text)[:50]
            
            # 从 URL 获取文件名
            parsed_url = urlparse(url)
            original_name = os.path.basename(parsed_url.path)
            
            # 生成文件名（优先使用原文件名）
            if original_name and '.' in original_name:
                filename = f"{clean_alt}_{original_name}"
            else:
                ext = get_file_extension(url)
                filename = f"image_{index}{ext}"
            
            local_path = image_path / filename
            
            # 处理重复文件名
            counter = 1
            while local_path.exists():
                name, ext = os.path.splitext(filename)
                local_path = image_path / f"{name}_{counter}{ext}"
                counter += 1
            
            # 下载图片
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # 返回相对路径（相对于输出目录）
            return Path(image_dir) / local_path.name
        
        except Exception as e:
            print(f"下载失败: {url} - {str(e)}")
            return url  # 返回原 URL 保持不修改

    # 并发下载图片（最多5个线程）
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for idx, (alt, url) in enumerate(matches):
            futures.append(
                executor.submit(
                    download_image, 
                    url, 
                    alt.strip(), 
                    idx
                )
            )
        
        # 等待所有任务完成并收集结果
        for future, (alt, orig_url) in zip(futures, matches):
            local_path = future.result()
            url_mapping[orig_url] = str(local_path)

    # 替换 Markdown 中的图片链接
    def replace_url(match):
        alt_text = match.group(1)
        orig_url = match.group(2)
        return f'![{alt_text}]({url_mapping.get(orig_url, orig_url)})'

    new_content = re.sub(pattern, replace_url, content)

    # 保存处理后的 Markdown 文件
    output_md = output_path / f"{Path(md_file_path).name}"
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"处理完成！\n新文件路径: {output_md}\n图片保存目录: {image_path}")

def get_file_extension(url):
    """根据 URL 或 Content-Type 获取文件扩展名"""
    # 尝试从 URL 路径获取扩展名
    path = urlparse(url).path
    if '.' in path:
        ext = os.path.splitext(path)[1]
        if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            return ext
    
    # 如果 URL 没有扩展名，尝试通过请求获取 Content-Type
    try:
        response = requests.head(url, timeout=5)
        content_type = response.headers.get('Content-Type', '')
        if content_type.startswith('image/'):
            ext = '.' + content_type.split('/')[1]
            if ext == '.jpeg':
                ext = '.jpg'
            return ext
    except:
        pass
    
    # 默认返回 .png
    return '.png'

if __name__ == "__main__":
    # 使用示例
    folder_path = "raw"
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
          process_markdown_images(
              md_file_path=file_path,
              output_dir="processed_docs",
              image_dir="assets/images"
          )