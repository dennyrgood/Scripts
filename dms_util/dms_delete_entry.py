#!/usr/bin/env python3
"""
dms_delete_entry.py - Remove entries from .dms_state.json

This allows you to selectively delete documents from the state.
Deleted entries will be re-scanned as "new" on the next scan,
allowing them to be re-summarized or re-processed.

Usage:
  dms delete-entry <file_path>     # Delete a specific entry
  dms delete-entry --list          # List all entries in state
  dms delete-entry --by-pattern <pattern>  # Delete all matching pattern (careful!)
  
Examples:
  dms delete-entry "./index.html"
  dms delete-entry "./md_outputs/IMG_4666.jpeg.txt"
  dms delete-entry --by-pattern "IMG_"
  dms delete-entry --by-pattern "long" --words-over 100  # Delete all with >100 word summaries
"""
import argparse
import sys
import json
from pathlib import Path


def load_state(state_path: Path) -> dict:
    """Load .dms_state.json"""
    if not state_path.exists():
        print(f"ERROR: {state_path} not found")
        return None
    
    try:
        return json.loads(state_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"ERROR: Failed to load state: {e}", file=sys.stderr)
        return None


def list_entries(state: dict):
    """List all entries in state with their word counts"""
    docs = state.get('documents', {})
    
    if not docs:
        print("No documents in state.")
        return
    
    print(f"Documents in state ({len(docs)} total):\n")
    
    for i, (path, doc) in enumerate(sorted(docs.items()), 1):
        summary = doc.get('summary', '')
        word_count = len(summary.split())
        category = doc.get('category', 'Unknown')
        print(f"  {i:2d}. {path}")
        print(f"      Category: {category} | Words: {word_count}")
        print(f"      Summary: {summary[:70]}...")
        print()


def delete_entry(state: dict, file_path: str) -> bool:
    """Delete a single entry from state"""
    docs = state.get('documents', {})
    
    # Normalize path
    if not file_path.startswith('./'):
        file_path = './' + file_path
    
    if file_path not in docs:
        print(f"  Entry not found: {file_path}")
        print(f"\n  Tip: Use 'dms delete-entry --list' to see all entries")
        return False
    
    doc = docs[file_path]
    summary = doc.get('summary', '')
    word_count = len(summary.split())
    category = doc.get('category', 'Unknown')
    
    print(f"  Deleting: {file_path}")
    print(f"    Category: {category}")
    print(f"    Words: {word_count}")
    print(f"    Summary: {summary[:70]}...")
    
    del docs[file_path]
    return True


def delete_by_pattern(state: dict, pattern: str, words_over: int = None) -> int:
    """Delete all entries matching pattern"""
    docs = state.get('documents', {})
    pattern_lower = pattern.lower()
    
    # Find matching entries
    matches = []
    for path, doc in docs.items():
        if pattern_lower in path.lower():
            summary = doc.get('summary', '')
            word_count = len(summary.split())
            
            # If words_over specified, only match if summary is longer
            if words_over and word_count <= words_over:
                continue
            
            matches.append((path, word_count, doc.get('category', 'Unknown')))
    
    if not matches:
        print(f"No entries matching pattern: {pattern}")
        if words_over:
            print(f"  with summaries over {words_over} words")
        return 0
    
    print(f"Found {len(matches)} matching entries:\n")
    for i, (path, word_count, category) in enumerate(matches, 1):
        print(f"  {i}. {path}")
        print(f"     Category: {category} | Words: {word_count}")
    
    # Ask for confirmation
    response = input(f"\nDelete these {len(matches)} entries? [y/N]: ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return 0
    
    # Delete them
    deleted = 0
    for path, _, _ in matches:
        del docs[path]
        deleted += 1
    
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Delete entries from .dms_state.json",
        epilog="Deleted entries will appear as 'new' on the next scan."
    )
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # List entries
    subparsers.add_parser("list", help="List all entries in state")
    
    # Delete specific entry
    p_delete = subparsers.add_parser("delete", help="Delete a specific entry")
    p_delete.add_argument("path", help="File path to delete (e.g., './index.html')")
    
    # Delete by pattern
    p_pattern = subparsers.add_parser("by-pattern", help="Delete entries matching pattern")
    p_pattern.add_argument("pattern", help="Pattern to match (case-insensitive)")
    p_pattern.add_argument("--words-over", type=int, help="Only delete if summary has more than N words")
    
    args = parser.parse_args()
    
    if not args.action:
        # Old style: dms delete-entry <path>
        # This shouldn't happen with new subparser style
        parser.print_help()
        return 1
    
    doc_dir = Path(args.doc)
    state_path = doc_dir / ".dms_state.json"
    
    if not doc_dir.exists():
        print(f"ERROR: {doc_dir} not found")
        return 1
    
    # Load state
    state = load_state(state_path)
    if state is None:
        return 1
    
    docs = state.get('documents', {})
    
    # Perform action
    if args.action == "list":
        list_entries(state)
        return 0
    
    elif args.action == "delete":
        print(f"==> Deleting entry from state...\n")
        if delete_entry(state, args.path):
            # Save modified state
            state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
            print(f"\n✓ Entry deleted")
            print(f"✓ State saved")
            print(f"\nNext step:")
            print(f"  Run: dms scan")
            print(f"  The deleted entry will appear as 'new' and can be re-summarized.")
            return 0
        else:
            return 1
    
    elif args.action == "by-pattern":
        print(f"==> Deleting entries matching pattern: {args.pattern}\n")
        if args.words_over:
            print(f"    Only entries with summaries > {args.words_over} words\n")
        
        deleted = delete_by_pattern(state, args.pattern, args.words_over)
        
        if deleted > 0:
            # Save modified state
            state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
            print(f"\n✓ Deleted {deleted} entry/entries")
            print(f"✓ State saved")
            print(f"\nNext step:")
            print(f"  Run: dms scan")
            print(f"  The deleted entries will appear as 'new'.")
            return 0
        else:
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
