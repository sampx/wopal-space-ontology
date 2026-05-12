#!/usr/bin/env python3
# workspace.py - Workspace root and space repo detection for dev-flow
#
# Provides:
#   - find_workspace_root: Locate workspace root using .wopal/.git worktree signature
#   - detect_space_repo: Parse owner/repo from workspace root's git remote URL

import os
import re
from pathlib import Path

from dev_flow.infra.git import get_remote_url


def find_workspace_root(start: Path | None = None) -> Path:
    """Find workspace root by locating .wopal/.git worktree file.
    
    The workspace root has a .wopal/ directory where .git is a file
    containing "gitdir: ..." (git worktree signature), not a regular
    directory. This distinguishes it from project-level .wopal/ dirs.
    
    Args:
        start: Starting directory for search (defaults to cwd)
        
    Returns:
        Path to workspace root
        
    Raises:
        RuntimeError: If workspace root cannot be found
    """
    if start is None:
        start = Path.cwd()
    else:
        start = Path(start).resolve()
    
    current = start
    
    while current != current.parent:
        wopal_git = current / ".wopal" / ".git"
        
        # Check for worktree signature: .wopal/.git is a file starting with "gitdir:"
        if wopal_git.exists() and wopal_git.is_file():
            try:
                content = wopal_git.read_text().strip()
                if content.startswith("gitdir:"):
                    return current
            except Exception:
                pass
        
        current = current.parent
    
    # Fallback: return start if we can't find worktree signature
    # This allows running from workspace root itself
    wopal_git = start / ".wopal" / ".git"
    if wopal_git.exists() and wopal_git.is_file():
        try:
            content = wopal_git.read_text().strip()
            if content.startswith("gitdir:"):
                return start
        except Exception:
            pass
    
    raise RuntimeError(f"Cannot find workspace root from {start}. "
                       "Expected .wopal/.git worktree file at workspace root.")


def detect_space_repo(workspace_root: Path) -> str:
    """Detect space repository (owner/repo) from workspace root's origin URL.
    
    Uses git remote get-url origin and parses both HTTPS and SSH formats.
    
    Args:
        workspace_root: Path to workspace root directory
        
    Returns:
        Repository in owner/repo format (e.g., "sampx/wopal-space")
        
    Raises:
        RuntimeError: If URL cannot be parsed or remote not configured
    """
    url = get_remote_url(str(workspace_root))
    
    if not url:
        raise RuntimeError(f"No origin remote configured at {workspace_root}")
    
    # Parse HTTPS format: https://github.com/owner/repo.git or https://github.com/owner/repo
    https_match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)(\.git)?$', url)
    if https_match:
        return f"{https_match.group(1)}/{https_match.group(2)}"
    
    # Parse SSH format: git@github.com:owner/repo.git or git@github.com:owner/repo
    ssh_match = re.match(r'git@github\.com:([^/]+)/([^/]+?)(\.git)?$', url)
    if ssh_match:
        return f"{ssh_match.group(1)}/{ssh_match.group(2)}"
    
    raise RuntimeError(f"Cannot parse GitHub URL: {url}. "
                       "Expected HTTPS (https://github.com/owner/repo) "
                       "or SSH (git@github.com:owner/repo) format.")