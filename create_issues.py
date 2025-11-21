#!/usr/bin/env python3
"""
Script to create GitHub issues from issues_definition.yaml

This script reads the YAML file containing issue definitions and creates
GitHub issues using the GitHub CLI (gh).

Prerequisites:
1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: gh auth login
3. Install PyYAML: pip install pyyaml

Usage:
    python create_issues.py [--dry-run]

Options:
    --dry-run    Print issues that would be created without actually creating them
"""

import subprocess
import sys
import json
import yaml
import argparse
from pathlib import Path


def check_prerequisites():
    """Check if required tools are installed and configured."""
    # Check if gh is installed
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) is not installed.")
        print("Please install it from: https://cli.github.com/")
        return False
    
    # Check if authenticated
    try:
        subprocess.run(['gh', 'auth', 'status'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Not authenticated with GitHub CLI.")
        print("Please run: gh auth login")
        return False
    
    return True


def load_issues_definition(yaml_file):
    """Load issue definitions from YAML file."""
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        return data.get('issues', [])
    except FileNotFoundError:
        print(f"Error: {yaml_file} not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None


def create_milestone(repo, milestone_title, dry_run=False):
    """Create a milestone if it doesn't exist."""
    if dry_run:
        print(f"  [DRY RUN] Would create milestone: {milestone_title}")
        return True
    
    # Check if milestone already exists
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/{repo}/milestones', '--jq', '.[].title'],
            capture_output=True,
            text=True,
            check=True
        )
        if milestone_title in result.stdout.split('\n'):
            print(f"  ✓ Milestone already exists: {milestone_title}")
            return True
    except subprocess.CalledProcessError:
        pass
    
    # Create milestone
    try:
        subprocess.run(
            ['gh', 'api', f'repos/{repo}/milestones',
             '-f', f'title={milestone_title}',
             '-f', 'state=open'],
            capture_output=True,
            check=True
        )
        print(f"  ✓ Created milestone: {milestone_title}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to create milestone: {milestone_title}")
        print(f"    Error: {e}")
        return False


def create_issue(repo, issue_def, dry_run=False):
    """Create a GitHub issue from definition."""
    title = issue_def.get('title', 'Untitled')
    body = issue_def.get('body', '')
    labels = issue_def.get('labels', [])
    milestone = issue_def.get('milestone')
    
    if dry_run:
        print(f"\n  [DRY RUN] Would create issue:")
        print(f"    Title: {title}")
        print(f"    Labels: {', '.join(labels)}")
        print(f"    Milestone: {milestone}")
        print(f"    Body length: {len(body)} chars")
        return True
    
    # Build command
    cmd = [
        'gh', 'issue', 'create',
        '--repo', repo,
        '--title', title,
        '--body', body
    ]
    
    # Add labels
    if labels:
        for label in labels:
            cmd.extend(['--label', label])
    
    # Add milestone
    if milestone:
        cmd.extend(['--milestone', milestone])
    
    # Execute command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"  ✓ Created: {title}")
        print(f"    URL: {issue_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to create: {title}")
        print(f"    Error: {e.stderr}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Create GitHub issues from YAML definition')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print what would be done without actually doing it')
    parser.add_argument('--repo', default='dhar174/research_corpus_organizer',
                       help='GitHub repository (owner/repo)')
    parser.add_argument('--yaml-file', default='issues_definition.yaml',
                       help='Path to YAML file with issue definitions')
    args = parser.parse_args()
    
    print("=" * 60)
    print("GitHub Issues Creation Script")
    print("=" * 60)
    print(f"Repository: {args.repo}")
    print(f"YAML File: {args.yaml_file}")
    if args.dry_run:
        print("MODE: DRY RUN (no issues will be created)")
    print("=" * 60)
    print()
    
    # Check prerequisites
    if not args.dry_run and not check_prerequisites():
        return 1
    
    # Load issues
    issues = load_issues_definition(args.yaml_file)
    if issues is None:
        return 1
    
    print(f"Found {len(issues)} issue definitions\n")
    
    # Confirm with user
    if not args.dry_run:
        response = input(f"Create {len(issues)} issues in {args.repo}? (y/n) ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
        print()
    
    # Collect unique milestones
    milestones = set()
    for issue in issues:
        milestone = issue.get('milestone')
        if milestone:
            milestones.add(milestone)
    
    # Create milestones
    if milestones:
        print(f"Creating {len(milestones)} milestones...")
        for milestone in sorted(milestones):
            create_milestone(args.repo, milestone, dry_run=args.dry_run)
        print()
    
    # Create issues
    print(f"Creating {len(issues)} issues...")
    print()
    
    success_count = 0
    fail_count = 0
    
    for i, issue in enumerate(issues, 1):
        print(f"[{i}/{len(issues)}]")
        if create_issue(args.repo, issue, dry_run=args.dry_run):
            success_count += 1
        else:
            fail_count += 1
        print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total issues: {len(issues)}")
    print(f"Created successfully: {success_count}")
    if fail_count > 0:
        print(f"Failed: {fail_count}")
    print("=" * 60)
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
