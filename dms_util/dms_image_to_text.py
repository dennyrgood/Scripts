#!/usr/bin/env python3
"""
dms_image_to_text.py - Convert images to text descriptions

Reads .dms_scan.json to find images in new files.
Converts images (PNG, JPG) to text via OCR.
Outputs text files to md_outputs/ for later summarization.

Does NOT update any state files - just produces intermediate text files.
"""
import argparse
import sys
import json
import subprocess
from pathlib import Path

def load_scan_results(scan_path: Path) -> dict:
    """Load .dms_scan.json to see what changed"""
    if not scan_path.exists():
        print(f"No scan results found at {scan_path}")
        return {"new_files": [], "changed_files": []}
    
    return json.loads(scan_path.read_text(encoding='utf-8'))

def find_images_in_files(files: list, doc_dir: Path) -> list:
    """Find image files in the list"""
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    images = []
    
    for file_info in files:
        file_path = file_info.get('path', '')
        ext = Path(file_path).suffix.lower()
        if ext in image_exts:
            images.append(file_path)
    
    return images

def convert_image_to_text(image_path: str, doc_dir: Path, md_dir: Path) -> bool:
    """Convert image to text using tesseract or similar"""
    
    full_path = doc_dir / image_path.lstrip('./')
    
    if not full_path.exists():
        print(f"  ⚠ Image not found: {image_path}")
        return False
    
    # Create output filename
    output_filename = f"{Path(image_path).stem}.txt"
    output_path = md_dir / output_filename
    
    # Try to use tesseract for OCR
    try:
        result = subprocess.run(
            ["tesseract", str(full_path), str(output_path).replace('.txt', '')],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0 and output_path.exists():
            print(f"  ✓ {image_path}")
            return True
        else:
            print(f"  ✗ Failed to convert: {image_path}")
            return False
    except FileNotFoundError:
        print(f"  ⚠ tesseract not installed, skipping: {image_path}")
        return False
    except Exception as e:
        print(f"  ✗ Error converting {image_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert images to text")
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    parser.add_argument("--md", default="Doc/md_outputs", help="Output directory for markdown/text")
    args = parser.parse_args()
    
    doc_dir = Path(args.doc)
    md_dir = Path(args.md)
    scan_path = doc_dir / ".dms_scan.json"
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    # Create output directory
    md_dir.mkdir(parents=True, exist_ok=True)
    
    # Load scan results
    scan_results = load_scan_results(scan_path)
    
    # Find images in new and changed files
    new_images = find_images_in_files(scan_results.get('new_files', []), doc_dir)
    changed_images = find_images_in_files(scan_results.get('changed_files', []), doc_dir)
    
    all_images = new_images + changed_images
    
    if not all_images:
        print("No images found in new/changed files.")
        return 0
    
    print(f"==> Converting {len(all_images)} image(s) to text...\n")
    
    converted = 0
    for image_path in all_images:
        if convert_image_to_text(image_path, doc_dir, md_dir):
            converted += 1
    
    print(f"\n✓ Converted {converted}/{len(all_images)} image(s)")
    
    if converted > 0:
        print(f"\nOutput files in {md_dir}/")
        print(f"\nNext step:")
        print(f"  Run: dms summarize")
    
    return 0

if __name__ == "__main__":
    exit(main())
