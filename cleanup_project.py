#!/usr/bin/env python3
"""
Cleanup Script for AI Interviewer Project
Removes unused files and optimizes project structure
"""

import os
import shutil
from pathlib import Path

class ProjectCleanup:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.removed_files = []
        self.removed_dirs = []
        self.saved_space = 0
        
    def get_size(self, path):
        """Get size of file or directory in bytes"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def remove_file(self, filepath, reason):
        """Remove a file and track it"""
        filepath = Path(filepath)
        if filepath.exists():
            size = self.get_size(filepath)
            try:
                filepath.unlink()
                self.removed_files.append((str(filepath), reason, size))
                self.saved_space += size
                print(f"✅ Removed: {filepath.name} ({size / 1024:.1f} KB) - {reason}")
            except Exception as e:
                print(f"❌ Failed to remove {filepath}: {e}")
    
    def remove_directory(self, dirpath, reason):
        """Remove a directory and track it"""
        dirpath = Path(dirpath)
        if dirpath.exists():
            size = self.get_size(dirpath)
            try:
                shutil.rmtree(dirpath)
                self.removed_dirs.append((str(dirpath), reason, size))
                self.saved_space += size
                print(f"✅ Removed directory: {dirpath.name} ({size / 1024 / 1024:.1f} MB) - {reason}")
            except Exception as e:
                print(f"❌ Failed to remove {dirpath}: {e}")
    
    def cleanup_test_files(self):
        """Remove test files not needed in production"""
        print("\n📋 Removing test files...")
        
        test_files = [
            self.root_dir / "frontend" / "test_tab_switching.html",
        ]
        
        for file in test_files:
            self.remove_file(file, "Test file not needed in production")
    
    def cleanup_redundant_scripts(self):
        """Remove redundant run scripts"""
        print("\n📋 Removing redundant scripts...")
        
        scripts = [
            self.root_dir / "run.py",
            self.root_dir / "run.sh",
            self.root_dir / "run.bat",
            self.root_dir / "setup.bat",
        ]
        
        for script in scripts:
            self.remove_file(script, "Redundant with docker-compose")
    
    def cleanup_pycache(self):
        """Remove Python cache directories"""
        print("\n📋 Removing Python cache...")
        
        for pycache in self.root_dir.rglob("__pycache__"):
            self.remove_directory(pycache, "Python cache")
    
    def cleanup_old_frontend(self):
        """Ask user if they want to remove old frontend"""
        print("\n📋 Checking frontend directories...")
        
        old_frontend = self.root_dir / "frontend"
        new_frontend = self.root_dir / "frontend-new"
        
        if old_frontend.exists() and new_frontend.exists():
            print(f"\n⚠️  Found both 'frontend' and 'frontend-new' directories")
            print(f"   Old frontend size: {self.get_size(old_frontend) / 1024 / 1024:.1f} MB")
            print(f"   New frontend size: {self.get_size(new_frontend) / 1024 / 1024:.1f} MB")
            
            response = input("\n   Remove old 'frontend' directory? (y/N): ").strip().lower()
            if response == 'y':
                self.remove_directory(old_frontend, "Using frontend-new instead")
            else:
                print("   Skipped - keeping both frontends")
    
    def cleanup_node_modules(self):
        """Optionally remove node_modules (can be reinstalled)"""
        print("\n📋 Checking node_modules...")
        
        for node_modules in self.root_dir.rglob("node_modules"):
            # Skip if in venv
            if "venv" in str(node_modules):
                continue
                
            size_mb = self.get_size(node_modules) / 1024 / 1024
            print(f"\n⚠️  Found node_modules: {node_modules}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   (Can be reinstalled with 'npm install')")
            
            response = input("\n   Remove to save space? (y/N): ").strip().lower()
            if response == 'y':
                self.remove_directory(node_modules, "Can be reinstalled with npm install")
            else:
                print("   Skipped - keeping node_modules")
    
    def generate_report(self):
        """Generate cleanup report"""
        print("\n" + "=" * 80)
        print("CLEANUP REPORT")
        print("=" * 80)
        
        if not self.removed_files and not self.removed_dirs:
            print("\n✅ No files removed - project is already clean!")
            return
        
        print(f"\n📊 Summary:")
        print(f"   Files removed: {len(self.removed_files)}")
        print(f"   Directories removed: {len(self.removed_dirs)}")
        print(f"   Space saved: {self.saved_space / 1024 / 1024:.2f} MB")
        
        if self.removed_files:
            print(f"\n📄 Files removed:")
            for filepath, reason, size in self.removed_files:
                print(f"   - {Path(filepath).name} ({size / 1024:.1f} KB)")
        
        if self.removed_dirs:
            print(f"\n📁 Directories removed:")
            for dirpath, reason, size in self.removed_dirs:
                print(f"   - {Path(dirpath).name} ({size / 1024 / 1024:.1f} MB)")
        
        print("\n" + "=" * 80)

def main():
    print("=" * 80)
    print("AI INTERVIEWER - PROJECT CLEANUP")
    print("=" * 80)
    print("\nThis script will remove unnecessary files to optimize your project.")
    print("⚠️  Make sure you have a backup before proceeding!")
    print()
    
    response = input("Continue with cleanup? (y/N): ").strip().lower()
    if response != 'y':
        print("\n❌ Cleanup cancelled")
        return
    
    root_dir = Path(__file__).parent
    cleanup = ProjectCleanup(root_dir)
    
    # Run cleanup tasks
    cleanup.cleanup_test_files()
    cleanup.cleanup_redundant_scripts()
    cleanup.cleanup_pycache()
    cleanup.cleanup_old_frontend()
    cleanup.cleanup_node_modules()
    
    # Generate report
    cleanup.generate_report()
    
    print("\n✅ Cleanup complete!")
    print("\n💡 Next steps:")
    print("   1. Review DEPLOYMENT_SUMMARY.md")
    print("   2. Set up .env file")
    print("   3. Deploy to Railway or Render")

if __name__ == "__main__":
    main()
