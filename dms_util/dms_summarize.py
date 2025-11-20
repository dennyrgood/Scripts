#!/usr/bin/env python3
"""
dms_summarize.py - Generate AI summaries for new/changed files

Reads .dms_scan.json to find new/changed files.
Generates summaries via Ollama.
Outputs: .dms_pending_summaries.json (awaiting user approval)

Does NOT update .dms_state.json (that happens in apply).
"""
import argparse
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

def load_config() -> dict:
    """Load DMS config"""
    config_path = Path(__file__).parent.parent / "dms_config.json"
    if not config_path.exists():
        return {
            "ollama_model": "phi3:mini",
            "ollama_host": "https://ollama.ldmathes.cc",
            "summary_max_words": 50,
            "temperature": 0.3
        }
    return json.loads(config_path.read_text(encoding='utf-8'))

def load_scan_results(scan_path: Path) -> dict:
    """Load .dms_scan.json"""
    if not scan_path.exists():
        return {"new_files": [], "changed_files": []}
    return json.loads(scan_path.read_text(encoding='utf-8'))

def read_file_content(file_path: Path) -> str:
    """Read file content safely"""
    try:
        if file_path.suffix in {'.txt', '.md', '.html', '.py', '.js', '.json'}:
            return file_path.read_text(encoding='utf-8', errors='replace')[:2000]  # First 2000 chars
        return f"[Binary file: {file_path.name}]"
    except Exception as e:
        return f"[Error reading file: {e}]"

def check_ollama(host: str, model: str) -> bool:
    """Check if Ollama is running and model available"""
    try:
        resp = requests.get(f"{host}/api/tags", timeout=5)
        if resp.status_code != 200:
            return False
        tags = resp.json().get('models', [])
        return any(model in t.get('name', '') for t in tags)
    except:
        return False

def generate_summary(file_content: str, config: dict) -> str:
    """Generate summary via Ollama"""
    try:
        resp = requests.post(
            f"{config['ollama_host']}/api/generate",
            json={
                "model": config['ollama_model'],
                "prompt": f"Summarize this document in {config['summary_max_words']} words or less:\n\n{file_content}",
                "temperature": config['temperature'],
                "stream": False
            },
            timeout=120
        )
        
        if resp.status_code == 200:
            return resp.json().get('response', '').strip()
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}", file=sys.stderr)
        return None

def categorize_file(file_path: str, summary: str) -> str:
    """Simple categorization based on filename and summary keywords"""
    name_lower = file_path.lower()
    summary_lower = summary.lower()
    
    if any(x in summary_lower for x in ['setup', 'install', 'guide', 'howto', 'tutorial']):
        return "Guides"
    elif any(x in summary_lower for x in ['model', 'training', 'weight', 'lora']):
        return "Models"
    elif any(x in summary_lower for x in ['script', 'code', 'command', 'bash', 'python']):
        return "Scripts"
    elif any(x in summary_lower for x in ['workflow', 'process', 'procedure', 'optimization']):
        return "Workflows"
    elif any(x in name_lower or x in summary_lower for x in ['quick', 'reference', 'cheat', 'faq', 'tip']):
        return "QuickRefs"
    else:
        return "Guides"  # Default

def main():
    parser = argparse.ArgumentParser(description="Generate AI summaries for new files")
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    parser.add_argument("--model", help="Override Ollama model")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen, don't write")
    args = parser.parse_args()
    
    doc_dir = Path(args.doc)
    scan_path = doc_dir / ".dms_scan.json"
    pending_path = doc_dir / ".dms_pending_summaries.json"
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    # Load config
    config = load_config()
    if args.model:
        config['ollama_model'] = args.model
    
    print("==> Generating AI summaries...\n")
    print(f"Using model: {config['ollama_model']}")
    print(f"Ollama host: {config['ollama_host']}\n")
    
    # Check Ollama is available
    if not check_ollama(config['ollama_host'], config['ollama_model']):
        print(f"ERROR: Cannot connect to Ollama at {config['ollama_host']}")
        print(f"Make sure Ollama is running (ollama serve)")
        return 1
    
    # Load scan results
    scan_results = load_scan_results(scan_path)
    files_to_summarize = scan_results.get('new_files', []) + scan_results.get('changed_files', [])
    
    if not files_to_summarize:
        print("No files to summarize.")
        return 0
    
    # Check if we have partial progress - resume from there
    already_done = set()
    if pending_path.exists():
        print(f"Found partial progress in {pending_path}")
        try:
            existing = json.loads(pending_path.read_text(encoding='utf-8'))
            already_done = {s['file']['path'] for s in existing.get('summaries', [])}
            print(f"✓ {len(already_done)} already summarized, resuming from there\n")
            summaries = existing.get('summaries', [])
        except:
            summaries = []
    else:
        summaries = []
    
    # Filter out already-done files
    files_to_process = [f for f in files_to_summarize if f.get('path') not in already_done]
    
    print(f"Summarizing {len(files_to_process)}/{len(files_to_summarize)} file(s)...\n")
    
    for i, file_info in enumerate(files_to_process, 1):
        file_path = file_info.get('path', '')
        full_path = doc_dir / file_path.lstrip('./')
        
        print(f"[{len(already_done) + i}/{len(files_to_summarize)}] {Path(file_path).name}")
        
        if not full_path.exists():
            print(f"  ⚠ File not found\n")
            continue
        
        # Read file content
        content = read_file_content(full_path)
        
        # Generate summary
        summary = generate_summary(content, config)
        
        if summary:
            category = categorize_file(file_path, summary)
            print(f"  Summary: {summary[:60]}...")
            print(f"  Category: {category}\n")
            
            summaries.append({
                "file": {
                    "path": file_path,
                    "hash": file_info.get('hash', ''),
                    "size": file_info.get('size', 0)
                },
                "summary": summary,
                "category": category,
                "title": Path(file_path).stem,
                "timestamp": datetime.now().isoformat()
            })
        else:
            print(f"  ✗ Failed to generate summary\n")
    
    if args.dry_run:
        print(f"DRY RUN: Would save {len(summaries)} summary/summaries")
        return 0
    
    # Save pending summaries
    pending_path = doc_dir / ".dms_pending_summaries.json"
    pending_data = {
        "timestamp": datetime.now().isoformat(),
        "summaries": summaries
    }
    
    pending_path.write_text(json.dumps(pending_data, indent=2), encoding='utf-8')
    
    print(f"\n✓ Generated {len(summaries)} summary/summaries")
    print(f"✓ Saved to {pending_path}")
    print(f"\nNext step:")
    print(f"  Run: dms review")
    
    return 0

if __name__ == "__main__":
    exit(main())
