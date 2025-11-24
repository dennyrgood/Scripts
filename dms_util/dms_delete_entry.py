#!/usr/bin/env python3
"""
dms_delete_entry.py - Remove entries from .dms_state.json

Interactive tool for managing document entries in the DMS state.
Deleted entries will be re-scanned as "new" on the next scan,
allowing them to be re-summarized or re-processed.

Usage:
  dms delete-entry              # Interactive menu (default)
  
Non-interactive mode:
  dms delete-entry list                                    # List all entries
  dms delete-entry delete <path>                           # Delete specific entry
  dms delete-entry by-pattern <pattern> [--words-over N]  # Delete matching pattern

Examples:
  dms delete-entry                              # Launch interactive menu
  dms delete-entry delete "./index.html"
  dms delete-entry by-pattern "IMG_"
  dms delete-entry by-pattern "summary" --words-over 100  # Delete all with >100 word summaries
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


def review_missing_files(state: dict, doc_dir: Path) -> int:
    """Review and delete missing files interactively"""
    docs = state.get('documents', {})
    
    # Load missing files from scan
    missing_file_path = doc_dir / ".dms_missing_for_deletion.json"
    if not missing_file_path.exists():
        print("\nNo missing files detected. (Run 'dms scan' first)")
        return 0
    
    try:
        missing_data = json.loads(missing_file_path.read_text(encoding='utf-8'))
        missing_files = missing_data.get('files', [])
    except Exception as e:
        print(f"ERROR: Could not load missing files: {e}")
        return 0
    
    if not missing_files:
        print("\nNo missing files to review.")
        return 0
    
    print(f"\n==> Review Missing Files ({len(missing_files)} total)\n")
    
    deleted = 0
    for i, file_info in enumerate(missing_files, 1):
        file_path = file_info.get('path')
        was_category = file_info.get('was_category', 'Unknown')
        
        if file_path not in docs:
            print(f"  [{i}/{len(missing_files)}] {file_path} (already deleted)")
            continue
        
        doc = docs[file_path]
        summary = doc.get('summary', '')
        word_count = len(summary.split())
        
        print(f"\n  [{i}/{len(missing_files)}] {file_path}")
        print(f"  Category: {was_category} | Words: {word_count}")
        print(f"  Summary: {summary[:80]}...")
        
        choice = input(f"\n  Delete? [y/N]: ").strip().lower()
        if choice == 'y':
            del docs[file_path]
            print(f"  ✓ Deleted")
            deleted += 1
        else:
            print(f"  - Kept")
    
    if deleted > 0:
        print(f"\n✓ Deleted {deleted}/{len(missing_files)} missing file entries")
    
    return deleted
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


def interactive_menu(state: dict, state_path: Path) -> int:
    """Interactive menu for deleting entries"""
    docs = state.get('documents', {})
    
    while True:
        print("\n" + "="*60)
        print("DMS Entry Deletion Tool")
        print("="*60)
        print(f"\nDocuments in state: {len(docs)}")
        print("\nOptions:")
        print("  1. List all entries")
        print("  2. Delete by pattern")
        print("  3. Delete entries with long summaries (>50 words)")
        print("  4. Search and delete")
        print("  5. Review and delete missing files")
        print("  6. Exit without saving")
        print("\n7. SAVE and exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            list_entries(state)
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            pattern = input("\nEnter pattern to search for (case-insensitive): ").strip()
            if pattern:
                deleted = delete_by_pattern(state, pattern, words_over=None)
                if deleted > 0:
                    docs = state.get('documents', {})
        
        elif choice == "3":
            # Find and delete summaries over 50 words
            print("\n==> Finding entries with summaries > 50 words...\n")
            long_summaries = []
            for path, doc in docs.items():
                summary = doc.get('summary', '')
                word_count = len(summary.split())
                if word_count > 50:
                    long_summaries.append((path, word_count, doc.get('category', 'Unknown')))
            
            if not long_summaries:
                print("No entries with summaries over 50 words found.")
                input("\nPress Enter to continue...")
                continue
            
            print(f"Found {len(long_summaries)} entries with long summaries:\n")
            for i, (path, words, cat) in enumerate(long_summaries, 1):
                print(f"  {i}. {path}")
                print(f"     Category: {cat} | Words: {words}")
            
            confirm = input(f"\nDelete all {len(long_summaries)} entries? [y/N]: ").strip().lower()
            if confirm == 'y':
                for path, _, _ in long_summaries:
                    del docs[path]
                print(f"✓ Deleted {len(long_summaries)} entries")
                docs = state.get('documents', {})
        
        elif choice == "4":
            search_term = input("\nEnter search term: ").strip()
            if search_term:
                matches = []
                search_lower = search_term.lower()
                for path, doc in sorted(docs.items()):
                    if search_lower in path.lower() or search_lower in doc.get('summary', '').lower():
                        matches.append(path)
                
                if not matches:
                    print(f"No matches found for '{search_term}'")
                else:
                    print(f"\nFound {len(matches)} matches:\n")
                    for i, path in enumerate(matches, 1):
                        doc = docs[path]
                        word_count = len(doc.get('summary', '').split())
                        print(f"  {i}. {path}")
                        print(f"     Words: {word_count} | Category: {doc.get('category', 'Unknown')}")
                    
                    selections = input(f"\nEnter numbers to delete (comma-separated), or press Enter to skip: ").strip()
                    if selections:
                        try:
                            indices = [int(x.strip())-1 for x in selections.split(',')]
                            to_delete = [matches[i] for i in indices if 0 <= i < len(matches)]
                            if to_delete:
                                confirm = input(f"\nDelete {len(to_delete)} entries? [y/N]: ").strip().lower()
                                if confirm == 'y':
                                    for path in to_delete:
                                        del docs[path]
                                    print(f"✓ Deleted {len(to_delete)} entries")
                        except (ValueError, IndexError):
                            print("Invalid selection")
                input("\nPress Enter to continue...")
        
        elif choice == "5":
            # Review missing files
            deleted = review_missing_files(state, state_path.parent)
            if deleted > 0:
                docs = state.get('documents', {})
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            print("Exiting without saving.")
            return 0
        
        elif choice == "7":
            if docs:
                state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
                print("\n✓ State saved!")
                print(f"✓ Remaining documents: {len(docs)}")
                print(f"\nNext step:")
                print(f"  Run: dms scan")
                print(f"  The deleted entries will appear as 'new'.")
                return 0
            else:
                print("ERROR: No documents left - would create empty state")
                return 1
        
        else:
            print("Invalid choice")


def main():
    parser = argparse.ArgumentParser(
        description="Delete entries from .dms_state.json",
        epilog="Deleted entries will appear as 'new' on the next scan."
    )
    parser.add_argument("--doc", default="Doc", help="Doc directory")
    parser.add_argument("--no-interactive", action="store_true", help="Use non-interactive mode")
    
    # Subcommands for non-interactive mode
    subparsers = parser.add_subparsers(dest="action", help="Action to perform (non-interactive)")
    
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
    
    # If no action specified or interactive flag set, use interactive mode
    if not args.action:
        return interactive_menu(state, state_path)
    
    # Non-interactive mode
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
