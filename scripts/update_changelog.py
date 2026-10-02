#!/usr/bin/env python3
"""
SynPassport Automated Changelog Generator
Generates and updates CHANGELOG.md based on full git commit history.
Can be executed manually or automatically via git hooks.
"""

import os
import re
import sys
import subprocess
from datetime import datetime

GIT_PATH = "/usr/bin/git"

def get_git_output(cmd_args):
    try:
        res = subprocess.run([GIT_PATH] + cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return res.stdout.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Warning: git command failed {cmd_args}: {e}", file=sys.stderr)
        return ""

def categorize_path(path):
    if "src/synpassport/passport" in path:
        return "Passport & Cryptography"
    elif "src/synpassport/checks" in path:
        return "Assurance & Statistical Checks"
    elif "src/synpassport/policy" in path:
        return "Policy Engine"
    elif "src/synpassport/agent" in path:
        return "Autonomous Assurance Agent"
    elif "src/synpassport/sdk" in path:
        return "Verification SDK & Guard"
    elif "src/synpassport/cli" in path:
        return "Command-Line Interface (CLI)"
    elif "src/synpassport/api" in path:
        return "REST API & Server"
    elif "src/synpassport/evidence" in path:
        return "Evidence Store"
    elif "src/synpassport/generators" in path:
        return "Synthetic Data Generators"
    elif "src/synpassport/mission" in path:
        return "Mission Profile"
    elif path.startswith("web/"):
        return "Web Dashboard (Next.js)"
    elif path.startswith("docs/") or path.endswith(".md"):
        return "Documentation"
    elif path.startswith("tests/"):
        return "Test Suite"
    elif path.startswith("policies/"):
        return "Policy Files"
    else:
        return "Configuration & Infrastructure"

def parse_commit_history():
    raw_log = get_git_output(['log', '--pretty=format:COMMIT_START|%H|%h|%an|%ae|%ad|%s', '--date=iso-strict'])
    if not raw_log:
        return []
    
    commit_blocks = raw_log.strip().split("COMMIT_START|")[1:]
    commits = []
    
    for block in commit_blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        parts = lines[0].split("|")
        if len(parts) < 6:
            continue
            
        full_hash, short_hash, author_name, author_email, date_str, subject = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        
        # Get stat breakdown for this commit
        stat_output = get_git_output(['show', '--stat', '--oneline', full_hash])
        stat_lines = [l.strip() for l in stat_output.splitlines() if l.strip()]
        summary_line = stat_lines[-1] if stat_lines else ""
        
        # Get files changed with status
        files_output = get_git_output(['show', '--name-status', '--oneline', full_hash])
        file_lines = files_output.splitlines()[1:]  # skip title line
        
        categories = {}
        changed_files = []
        for fl in file_lines:
            fl_parts = fl.strip().split(maxsplit=1)
            if len(fl_parts) == 2:
                status, filepath = fl_parts[0], fl_parts[1]
                cat = categorize_path(filepath)
                categories.setdefault(cat, []).append((status, filepath))
                changed_files.append((status, filepath))
                
        commits.append({
            "full_hash": full_hash,
            "short_hash": short_hash,
            "author": author_name,
            "email": author_email,
            "date": date_str,
            "subject": subject,
            "summary": summary_line,
            "categories": categories,
            "changed_files": changed_files
        })
        
    return commits

def generate_markdown(commits):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = []
    md.append("# SynPassport — Detailed Commit & Change History")
    md.append("")
    md.append(f"> **Last Updated**: `{now_str}`  ")
    md.append("> **Auto-Update**: Enabled via `.githooks/pre-commit` and `scripts/update_changelog.py`  ")
    md.append("")
    md.append("This document tracks every commit, feature addition, architectural improvement, security enhancement, and bug fix across the SynPassport codebase over time.")
    md.append("")
    md.append("---")
    md.append("")
    
    # Overview Summary Table
    md.append("## Commit Overview Summary")
    md.append("")
    md.append("| Commit | Date | Author | Description | Impact |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for c in commits:
        date_short = c["date"].split("T")[0]
        summary_clean = re.sub(r'^\d+ files? changed,?\s*', '', c["summary"])
        md.append(f"| [`{c['short_hash']}`](#commit-{c['short_hash']}) | {date_short} | {c['author']} | {c['subject']} | {summary_clean} |")
        
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Detailed Commit Log")
    md.append("")
    
    for c in commits:
        date_fmt = c["date"].replace("T", " ").split("+")[0]
        md.append(f"### Commit `{c['short_hash']}` — {c['subject']}")
        md.append(f"- **Hash**: `{c['full_hash']}`")
        md.append(f"- **Author**: {c['author']} (`{c['email']}`)")
        md.append(f"- **Date**: `{date_fmt}`")
        md.append(f"- **Stats**: `{c['summary']}`")
        md.append("")
        
        if c["categories"]:
            md.append("#### Component Breakdown")
            for cat_name, file_list in sorted(c["categories"].items()):
                md.append(f"- **{cat_name}** ({len(file_list)} files):")
                for st, fp in file_list[:10]:
                    status_label = {"A": "Added", "M": "Modified", "D": "Deleted"}.get(st, st)
                    md.append(f"  - `{status_label}` [{os.path.basename(fp)}](file://{os.path.abspath(fp)})")
                if len(file_list) > 10:
                    md.append(f"  - *... and {len(file_list) - 10} more files*")
            md.append("")
            
        md.append("---")
        md.append("")
        
    return "\n".join(md)

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)
    
    commits = parse_commit_history()
    markdown_content = generate_markdown(commits)
    
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")
    docs_changelog_path = os.path.join(repo_root, "docs", "CHANGELOG.md")
    
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    os.makedirs(os.path.dirname(docs_changelog_path), exist_ok=True)
    with open(docs_changelog_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Successfully updated CHANGELOG.md and docs/CHANGELOG.md ({len(commits)} commits logged).")

if __name__ == "__main__":
    main()
