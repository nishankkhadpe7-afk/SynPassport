#!/usr/bin/env python3
"""
Installer for SynPassport Git Hooks
Configures core.hooksPath and installs pre-commit & post-commit hooks.
"""

import os
import shutil
import stat
import subprocess

def make_executable(filepath):
    st = os.stat(filepath)
    os.chmod(filepath, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    githooks_dir = os.path.join(repo_root, ".githooks")
    git_hooks_dir = os.path.join(repo_root, ".git", "hooks")
    
    os.makedirs(githooks_dir, exist_ok=True)
    os.makedirs(git_hooks_dir, exist_ok=True)
    
    # Configure git hooks directory
    try:
        subprocess.run(["/usr/bin/git", "config", "core.hooksPath", ".githooks"], check=True)
        print("✅ Git configured: core.hooksPath = .githooks")
    except Exception as e:
        print(f"Warning: Could not set git config core.hooksPath: {e}")
        
    for hook in ["pre-commit", "post-commit"]:
        src = os.path.join(githooks_dir, hook)
        dst = os.path.join(git_hooks_dir, hook)
        if os.path.exists(src):
            make_executable(src)
            shutil.copy2(src, dst)
            make_executable(dst)
            print(f"✅ Installed executable hook: {hook}")
            
    print("\n🎉 SynPassport git hooks successfully installed! CHANGELOG.md will now automatically update on every commit.")

if __name__ == "__main__":
    main()
