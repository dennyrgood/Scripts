#!/usr/bin/env python3
"""
dms_cleanup.py - Remove deleted files from .dms_state.json

If a file is in .dms_state.json but deleted from the filesystem,
this removes it from the state.

Then regenerates index.html.
"""
import argparse
import sys
import json
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Remove deleted files from DMS state")
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    args = parser.parse_args()
    
    doc_dir = Path(args.doc)
    state_path = doc_dir / ".dms_state.json"
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    if not state_path.exists():
        print(f"No state file found at {state_path}")
        return 0
    
    # Load state
    state = json.loads(state_path.read_text(encoding='utf-8'))
    
    # Find files that are in state but not on disk
    missing_files = []
    for file_path in list(state['documents'].keys()):
        full_path = doc_dir / file_path.lstrip('./')
        if not full_path.exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✓ No deleted files to clean up.")
        return 0
    
    print(f"==> Removing {len(missing_files)} deleted file(s) from state...\n")
    
    for file_path in missing_files:
        category = state['documents'][file_path].get('category', 'Unknown')
        print(f"  - {Path(file_path).name} (was in {category})")
        del state['documents'][file_path]
    
    # Save updated state
    state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    print(f"\n✓ Updated {state_path}")
    
    # Regenerate index.html
    print(f"\n==> Regenerating index.html...\n")
    
    scripts_dir = Path(__file__).parent.parent.parent
    render_script = scripts_dir / "dms_util" / "dms_render.py"
    
    result = subprocess.run(
        [sys.executable, str(render_script),
         "--doc", str(doc_dir),
         "--index", str(doc_dir / "index.html")],
        capture_output=False
    )
    
    if result.returncode == 0:
        print(f"\n✓ Cleanup complete!")
    else:
        print(f"ERROR: Failed to render index.html", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
