#!/usr/bin/env python3
"""
dms_status.py - Show current DMS state and workflow status

Displays:
- Total documents in state
- Breakdown by category
- Summary coverage
- Pending changes (if any)
- Last scan/apply timestamps
- Any intermediate files waiting
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

def load_state(state_path: Path) -> dict:
    """Load .dms_state.json"""
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text(encoding='utf-8'))

def load_json_file(path: Path) -> dict:
    """Load any JSON file"""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except:
        return None

def format_timestamp(ts: str) -> str:
    """Format ISO timestamp nicely"""
    if not ts:
        return "Never"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts

def main():
    parser = argparse.ArgumentParser(description="Show DMS status")
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    args = parser.parse_args()
    
    doc_dir = Path(args.doc)
    state_path = doc_dir / ".dms_state.json"
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    # Load state
    state = load_state(state_path)
    
    if not state:
        print(f"No DMS state found at {state_path}")
        print(f"Run: dms init")
        return 0
    
    print("\n" + "="*70)
    print("DMS STATUS")
    print("="*70 + "\n")
    
    # Main state stats
    total_docs = len(state.get('documents', {}))
    print(f"📚 DOCUMENTS: {total_docs}\n")
    
    # Category breakdown
    by_cat = {}
    for doc in state.get('documents', {}).values():
        cat = doc.get('category', 'Unknown')
        by_cat[cat] = by_cat.get(cat, 0) + 1
    
    print("📁 Categories:")
    for cat in sorted(by_cat.keys()):
        count = by_cat[cat]
        print(f"   {cat:<15} {count:>3}")
    print()
    
    # Summary coverage
    with_summary = sum(1 for d in state.get('documents', {}).values() if d.get('summary'))
    without_summary = total_docs - with_summary
    coverage = (with_summary / total_docs * 100) if total_docs > 0 else 0
    
    print(f"📝 SUMMARIES")
    print(f"   With summaries:    {with_summary}/{total_docs} ({coverage:.0f}%)")
    if without_summary > 0:
        print(f"   Pending summaries: {without_summary}")
    print()
    
    # Metadata
    metadata = state.get('metadata', {})
    print(f"⏱️  TIMESTAMPS")
    print(f"   Last scan:  {format_timestamp(metadata.get('last_scan'))}")
    print(f"   Last apply: {format_timestamp(metadata.get('last_apply'))}")
    if metadata.get('migrated_from_embedded'):
        print(f"   Migrated:   {format_timestamp(metadata.get('migration_date'))}")
    print()
    
    # Check for pending work
    print(f"⏳ WORKFLOW STATUS\n")
    
    scan_path = doc_dir / ".dms_scan.json"
    pending_sum = doc_dir / ".dms_pending_summaries.json"
    pending_app = doc_dir / ".dms_pending_approved.json"
    
    workflow_state = "Clean"
    
    if scan_path.exists():
        scan_data = load_json_file(scan_path)
        new = len(scan_data.get('new_files', []))
        changed = len(scan_data.get('changed_files', []))
        missing = len(scan_data.get('missing_files', []))
        total_changes = new + changed + missing
        
        print(f"   ⚠️  SCAN RESULTS PENDING")
        print(f"      New files:     {new}")
        print(f"      Changed files: {changed}")
        print(f"      Missing files: {missing}")
        print(f"      Total changes: {total_changes}\n")
        workflow_state = "Scan pending"
    
    if pending_sum.exists():
        data = load_json_file(pending_sum)
        count = len(data.get('summaries', []))
        print(f"   ⚠️  SUMMARIES PENDING REVIEW")
        print(f"      Count: {count}\n")
        print(f"      Next: dms review\n")
        workflow_state = "Review needed"
    
    if pending_app.exists():
        data = load_json_file(pending_app)
        count = len(data.get('summaries', []))
        print(f"   ⚠️  APPROVED SUMMARIES PENDING APPLY")
        print(f"      Count: {count}\n")
        print(f"      Next: dms apply\n")
        workflow_state = "Apply needed"
    
    if workflow_state == "Clean":
        print(f"   ✓ All clean - no pending changes")
    
    print()
    
    # Recommendations
    print(f"💡 NEXT STEPS\n")
    
    if without_summary > 0:
        print(f"   → Summarize {without_summary} files without summaries:")
        print(f"     dms scan && dms summarize\n")
    elif workflow_state == "Clean" and without_summary == 0:
        print(f"   → All documents have summaries!")
        print(f"   → Add new files to Doc/ and run: dms scan\n")
    
    print("="*70 + "\n")
    
    return 0

if __name__ == "__main__":
    exit(main())
