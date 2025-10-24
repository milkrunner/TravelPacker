#!/usr/bin/env python3
"""
Repository cleanup script
Removes temporary files, caches, and old backups
"""

import os
import shutil
from pathlib import Path

def remove_directory(path: Path, name: str) -> int:
    """Remove directory and return count of removed items"""
    count = 0
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"✅ Removed {name}: {path}")
            count = 1
        except Exception as e:
            print(f"❌ Failed to remove {path}: {e}")
    return count

def remove_file(path: Path, name: str) -> int:
    """Remove file and return count"""
    count = 0
    if path.exists():
        try:
            path.unlink()
            print(f"✅ Removed {name}: {path}")
            count = 1
        except Exception as e:
            print(f"❌ Failed to remove {path}: {e}")
    return count

def find_and_remove_pycache(root: Path) -> int:
    """Recursively find and remove __pycache__ directories"""
    count = 0
    for dirpath, dirnames, _ in os.walk(root):
        if '__pycache__' in dirnames:
            cache_path = Path(dirpath) / '__pycache__'
            count += remove_directory(cache_path, "__pycache__")
    return count

def find_and_remove_old_files(root: Path) -> int:
    """Find and remove .old backup files"""
    count = 0
    for old_file in root.rglob("*.old"):
        count += remove_file(old_file, "backup file")
    return count

def main():
    """Main cleanup function"""
    print("🧹 Starting repository cleanup...\n")
    
    repo_root = Path(__file__).parent.parent.parent
    removed_count = 0
    
    print("1. Removing Python cache directories...")
    removed_count += find_and_remove_pycache(repo_root)
    
    print("\n2. Removing backup files...")
    removed_count += remove_file(repo_root / "web_app.py.old", "old web_app backup")
    removed_count += find_and_remove_old_files(repo_root)
    
    print("\n3. Removing pytest cache...")
    removed_count += remove_directory(repo_root / ".pytest_cache", "pytest cache")
    
    print("\n4. Removing coverage files...")
    removed_count += remove_file(repo_root / ".coverage", "coverage data")
    
    print("\n5. Removing virtual environment caches...")
    venv_pycache = repo_root / "venv" / "__pycache__"
    if venv_pycache.exists():
        print("⚠️  Skipping venv/__pycache__ (part of virtual environment)")
    
    print(f"\n✨ Cleanup complete! Removed {removed_count} items.")
    print("\n💡 Tip: Run 'git status' to see what was cleaned up.")
    print("💡 Tip: These items are now in .gitignore and won't be committed.")

if __name__ == "__main__":
    main()
