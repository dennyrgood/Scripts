#!/usr/bin/env python3
"""
dms_migrate_to_json.py - Migrate from index.html DMS_STATE to .dms_state.json

Extracts DMS_STATE from index.html and creates new .dms_state.json format.
This is a one-time migration script.

Usage:
  python3 dms_migrate_to_json.py --doc Doc --index Doc/index.html
"""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime

def _extract_categories_from_html(content: str) -> dict:
    """Extract categories and their files from HTML structure"""
    categories = {}
    
    # Find each section with data-category
    for section_match in re.finditer(
        r'<section[^>]*data-category="([^"]+)"[^>]*>.*?</section>',
        content,
        re.DOTALL
    ):
        category = section_match.group(1)
        section_content = section_match.group(0)
        
        # Find all data-path entries in this section
        files = re.findall(r'data-path="([^"]+)"', section_content)
        categories[category] = files
    
    return categories

def migrate(doc_dir: Path, index_path: Path):
    """Migrate from embedded DMS_STATE to separate .dms_state.json"""
    
    print("=== DMS Migration: Embedded State → Separate JSON ===\n")
    
    # Read current index.html
    if not index_path.exists():
        print(f"ERROR: {index_path} not found")
        return 1
    
    content = index_path.read_text(encoding='utf-8')
    
    # Extract DMS_STATE
    state_match = re.search(r'<!-- DMS_STATE\n(.*?)\n-->', content, re.DOTALL)
    if not state_match:
        print("ERROR: DMS_STATE not found in index.html")
        return 1
    
    old_state_text = state_match.group(1).strip()
    old_state = json.loads(old_state_text)
    
    # Extract categories from HTML structure (not from state, which may not have them)
    categories_from_html = _extract_categories_from_html(content)
    
    # Transform to new format
    new_state = {
        "metadata": {
            "last_scan": old_state.get("last_scan", datetime.now().isoformat()),
            "last_apply": datetime.now().isoformat(),
            "migrated_from_embedded": True,
            "migration_date": datetime.now().isoformat()
        },
        "categories": list(categories_from_html.keys()) if categories_from_html else old_state.get("categories", []),
        "documents": {}
    }
    
    # Convert processed_files to documents
    for file_path, file_data in old_state.get("processed_files", {}).items():
        # Find the correct category from HTML structure
        category = "Junk"  # default
        for cat, files in categories_from_html.items():
            if file_path in files:
                category = cat
                break
        
        new_state["documents"][file_path] = {
            "hash": file_data.get("hash", ""),
            "category": category,
            "summary": file_data.get("description", file_data.get("summary", "")),
            "summary_approved": file_data.get("summary_approved", True),
            "title": file_data.get("title", Path(file_path).stem),
            "last_processed": file_data.get("last_processed", datetime.now().isoformat())
        }
    
    # Save new .dms_state.json
    state_path = doc_dir / ".dms_state.json"
    state_path.write_text(json.dumps(new_state, indent=2), encoding='utf-8')
    
    print(f"✓ Created {state_path}")
    print(f"  Categories: {len(new_state['categories'])}")
    print(f"  Documents: {len(new_state['documents'])}")
    summaries_count = sum(1 for d in new_state['documents'].values() if d['summary'])
    print(f"  - {summaries_count} with summaries")
    print(f"\n✓ Migration complete!")
    print(f"\nNext steps:")
    print(f"  1. Verify .dms_state.json looks correct")
    print(f"  2. Run: dms render (to regenerate index.html)")
    print(f"  3. Check index.html in browser")
    print(f"  4. If all good: git add .dms_state.json && git commit")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Migrate DMS to JSON-based state")
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    parser.add_argument("--index", default="Doc/index.html", help="Path to index.html")
    args = parser.parse_args()
    
    doc_dir = Path(args.doc)
    index_path = Path(args.index)
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    return migrate(doc_dir, index_path)

if __name__ == "__main__":
    exit(main())
