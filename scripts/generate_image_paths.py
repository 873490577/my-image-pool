#!/usr/bin/env python3
"""
自动生成仓库中所有图片路径的JSON文件
"""

import os
import json
import sys
from pathlib import Path
import datetime

def get_image_paths(root_dir="."):
    """递归获取所有图片文件路径"""
    
    # 支持的图片格式
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.webp', '.svg', '.ico', '.jfif', '.pjpeg', '.pjp',
        '.avif', '.apng', '.heic', '.heif'
    }
    
    # 需要忽略的目录
    ignore_dirs = {
        '.git', '.github', '.vscode', '__pycache__', 
        'node_modules', 'venv', '.venv', 'env', 'dist',
        'build', '.next', '.nuxt', 'out'
    }
    
    image_paths = []
    
    # 转换为绝对路径
    root_path = Path(root_dir).resolve()
    
    for file_path in root_path.rglob("*"):
        # 跳过忽略的目录
        if any(part in ignore_dirs for part in file_path.parts):
            continue
        
        # 跳过隐藏文件（以点开头）
        if file_path.name.startswith('.'):
            continue
        
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in image_extensions:
                # 获取相对于仓库根目录的路径
                rel_path = file_path.relative_to(root_path)
                # 确保使用正斜杠（跨平台兼容）
                image_paths.append(str(rel_path).replace("\\", "/"))
    
    return sorted(image_paths)

def group_by_folder(paths):
    """按文件夹分组图片路径"""
    grouped = {}
    
    for path in paths:
        folder = str(Path(path).parent)
        if folder == ".":
            folder = "root"
        
        if folder not in grouped:
            grouped[folder] = []
        
        grouped[folder].append(path)
    
    return grouped

def group_by_extension(paths):
    """按文件扩展名分组"""
    grouped = {}
    
    for path in paths:
        ext = Path(path).suffix.lower()
        if not ext:
            ext = "no_extension"
        
        if ext not in grouped:
            grouped[ext] = []
        
        grouped[ext].append(path)
    
    return grouped

def create_json_output(image_paths):
    """创建完整的JSON输出结构"""
    
    # 按不同方式分组
    by_folder = group_by_folder(image_paths)
    by_extension = group_by_extension(image_paths)
    
    # 统计每个文件夹的图片数量
    folder_stats = {}
    for folder, paths in by_folder.items():
        folder_stats[folder] = len(paths)
    
    # 按扩展名统计
    extension_stats = {}
    for ext, paths in by_extension.items():
        extension_stats[ext] = len(paths)
    
    output = {
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "total_images": len(image_paths),
            "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
            "commit_sha": os.environ.get("GITHUB_SHA", ""),
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        },
        "statistics": {
            "by_folder": folder_stats,
            "by_extension": extension_stats,
        },
        "images": {
            "all_paths": image_paths,
            "by_folder": by_folder,
            "by_extension": by_extension,
        },
        "summary": f"Found {len(image_paths)} image files across {len(by_folder)} folders"
    }
    
    return output

def main():
    """主函数"""
    print("🚀 开始扫描图片文件...")
    
    try:
        # 扫描图片
        image_paths = get_image_paths(".")
        
        if not image_paths:
            print("⚠️  未找到图片文件")
            # 创建一个空的JSON结构
            output = {
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "total_images": 0,
                    "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
                    "commit_sha": os.environ.get("GITHUB_SHA", ""),
                    "run_id": os.environ.get("GITHUB_RUN_ID", ""),
                },
                "statistics": {
                    "by_folder": {},
                    "by_extension": {},
                },
                "images": {
                    "all_paths": [],
                    "by_folder": {},
                    "by_extension": {},
                },
                "summary": "No image files found"
            }
        else:
            print(f"📊 找到 {len(image_paths)} 个图片文件")
            
            # 显示一些统计信息
            by_ext = group_by_extension(image_paths)
            print("\n📁 按扩展名统计:")
            for ext, paths in sorted(by_ext.items()):
                print(f"  {ext}: {len(paths)} 个")
            
            # 创建JSON输出
            output = create_json_output(image_paths)
        
        # 写入JSON文件
        output_file = "image_paths.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 成功生成 {output_file}")
        print(f"📝 总图片数: {output['metadata']['total_images']}")
        
        # 如果是GitHub Actions环境，设置输出变量
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"total_images={output['metadata']['total_images']}\n")
                f.write(f"output_file={output_file}\n")
        
        return 0
        
    except Exception as e:
        print(f"❌ 生成失败: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
