#!/usr/bin/env python3
# approve.py - Approve command for dev-flow
#
# Command (requires --confirm):
#   approve <issue> --confirm - Approve Plan and transition to executing phase
#   approve <plan-name> --confirm - Approve Plan (no-issue mode)
#   approve <issue> --confirm --no-worktree - Skip worktree creation
#
# Flow (--confirm required):
#   1. Find Plan file (by issue number OR plan name)
#   2. Run check_doc validation
#   3. Preflight checks + status transition (reviewing/planning → executing)
#   4. Issue sync + worktree creation
#
# Preflight checks (--confirm mode):
#   - check_doc validation
#   - Target Project dirty workspace check (BLOCK or stash if worktree)
#   - Worktree creation (default; skip with --no-worktree)
#
# Issue sync (--confirm mode):
#   - Sync status label (reviewing -> in-progress)
#   - Sync plan content to Issue body
#   - Ensure Issue labels (type, project)

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from lib.logging import log_info, log_success, log_error, log_warn, log_step
from lib.workspace import find_workspace_root, detect_space_repo, get_ontology_main_repo
from workflow import update_plan_status, parse_plan_status, STATUS_PLANNING, STATUS_REVIEWING
from plan import find_plan
from plan import get_plan_project, get_plan_issue, get_plan_status, get_plan_field
from plan import resolve_project_path, ProjectType
from validation import check_doc_plan, ValidationError
from issue import (
    sync_status_label,
    sync_plan_to_issue_body,
    ensure_issue_labels,
)
from lib.git import (
    is_repo_dirty,
    get_current_branch,
    get_branch_head,
)
from lib.plan_commit import commit_and_push_plan, RESULT_OK, RESULT_PUSH_FAILED
from lib.worktree import create_worktree, write_worktree_context
from plan import set_plan_field


# ============================================
# Helpers
# ============================================

def _derive_branch(project: str, plan_name: str) -> str:
    """Derive branch name from Plan name: <project>-<plan-name>.

    The branch uses the full Plan name (including issue number/type/scope/slug),
    so it strictly corresponds to the Plan and can be mapped back to it.

    Args:
        project: Target project name
        plan_name: Plan name (without .md extension)

    Returns:
        Branch name string
    """
    return f"{project}-{plan_name}"


def _has_unmerged_files(repo_path: str) -> bool:
    """Check if git repo has unmerged (UU) files from incomplete merge.
    
    Args:
        repo_path: Path to git repository root
        
    Returns:
        True if any file is in unmerged state
    """
    result = subprocess.run(
        ["git", "ls-files", "--unmerged"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


# ============================================
# Worktree Creation
# ============================================

def _create_worktree(project_dir: Path, branch: str, workspace_root: Path) -> Path | None:
    """Create isolated worktree for project execution.
    
    Args:
        project_dir: Resolved project git root path
        branch: Branch name for worktree
        workspace_root: Workspace root path
        
    Returns:
        Path to created worktree, or None on failure
    """
    worktree_base = workspace_root / ".worktrees"
    
    log_step("Pre-flight: creating worktree...")
    log_info(f"Project: {project_dir.name}, Branch: {branch}")
    
    try:
        wt_path = create_worktree(project_dir, branch, worktree_base)
        log_success(f"Worktree created successfully: {wt_path}")
        return wt_path
    except Exception as e:
        log_error(f"Worktree creation failed - aborting approve: {e}")
        return None


# ============================================
# approve command
# ============================================

def cmd_approve(args: argparse.Namespace) -> int:
    """Approve Plan and transition to executing phase (--confirm required).
    
    Modes:
    1. approve <issue-or-name> --confirm - preflight + status transition + Issue sync
    2. approve <issue-or-name> --confirm --no-worktree - skip worktree creation
    
    Returns:
        0 on success, 1 on error
    """
    input_ref = args.target
    confirm = args.confirm
    existing_worktree = getattr(args, "existing_worktree", None)
    use_worktree = (not args.no_worktree) and (not existing_worktree)  # default: worktree enabled unless --no-worktree or --existing-worktree
    
    if not input_ref:
        log_error("Issue number or Plan name required")
        log_error("Usage: flow.sh approve <issue-or-name> [--confirm] [--no-worktree] [--existing-worktree <path>]")
        return 1
    
    workspace_root = find_workspace_root()
    
    # 1. Smart lookup: Issue number OR Plan name
    try:
        plan_path = find_plan(input_ref, str(workspace_root))
    except FileNotFoundError:
        log_error(f"No plan found for: {input_ref}")
        return 1
    
    log_info(f"Found plan: {plan_path}")
    
    # Get plan name (for output)
    plan_name = Path(plan_path).stem
    
    # ============================================
    # --confirm is required
    # ============================================
    if not confirm:
        log_error("submit command replaces approve without --confirm")
        log_error("Use: flow.sh submit <plan>")
        return 1
    
    # 2. Check Plan status is "planning" or "reviewing"
    current_status = parse_plan_status(plan_path)
    
    if not current_status:
        current_status = get_plan_status(plan_path)
    
    if current_status not in (STATUS_PLANNING, STATUS_REVIEWING):
        log_error(f"Plan must be in planning or reviewing state to approve (current: {current_status})")
        log_error("")
        
        if current_status == "executing":
            log_error("Plan already approved. Next: flow.sh complete <plan>")
        elif current_status == "verifying":
            log_error("Plan awaiting verification. Next: flow.sh verify <plan> --confirm")
        elif current_status == "done":
            log_error("Plan already archived.")
        else:
            log_error("Unknown status. Check plan file.")
        
        return 1
    
    # 3. Run check_doc validation (before any state changes)
    try:
        check_doc_plan(plan_path)
    except ValidationError as e:
        log_error("Plan failed check-doc validation")
        print(str(e))
        log_error(f"Fix the issues and retry: flow.sh submit {input_ref}")
        return 1
    
    # 4. Extract Issue number (if plan has Issue link)
    issue_number = get_plan_issue(plan_path)
    
    # ============================================
    # --confirm mode: preflight checks + state transition
    # ============================================
    
    repo = detect_space_repo(workspace_root)
    project = get_plan_project(plan_path)
    
    # --- Preflight Check 1: Target Project dirty workspace ---
    # Exclude Plan file itself from dirty check — approve will commit it as part of state transition
    project_path = resolve_project_path(plan_path, project, workspace_root) if project else None
    dirty_workspace = False

    if project_path:
        dirty_workspace = is_repo_dirty(str(project_path), ignore_paths=[plan_path])
    
    # --- Preflight: compute worktree parameters ---
    worktree_created = False
    branch = ""
    worktree_path = None  # type: Path | None

    if existing_worktree:
        if not project:
            log_error("Cannot bind existing worktree: no Target Project in plan")
            return 1
        # Resolve existing worktree path
        wt_p = Path(existing_worktree)
        if not wt_p.is_absolute():
            wt_p = workspace_root / wt_p
        if not wt_p.exists():
            log_error(f"Specified existing worktree path does not exist: {wt_p}")
            return 1
        if not wt_p.is_dir():
            log_error(f"Specified existing worktree path is not a directory: {wt_p}")
            return 1

        # Resolve project repo root and verify that wt_p is a valid worktree of this project
        project_type_str = get_plan_field(plan_path, "Project Type")
        if project_type_str == ProjectType.ONTOLOGY_WORKTREE.value:
            main_repo = get_ontology_main_repo(workspace_root)
            repo_root = main_repo
        else:
            repo_root = Path(project_path) if project_path else None

        if not repo_root or not repo_root.exists():
            log_error(f"Cannot resolve project repository root for: {project}")
            return 1

        # Reject pointing to the primary integration worktree (main checkout)
        try:
            if wt_p.resolve() == repo_root.resolve():
                log_error(
                    f"Specified worktree path is the primary repository checkout ({repo_root}), "
                    "not an isolated feature worktree. Use --no-worktree for direct main execution."
                )
                return 1
        except Exception:
            pass

        # Detect the checked-out branch in that worktree
        branch = get_current_branch(wt_p)
        if not branch:
            log_error(f"Could not determine branch of existing worktree at: {wt_p}")
            return 1

        # Reject integration branches (main, master, space/<name>) as evolution worktrees
        if branch in ("main", "master") or branch.startswith("space/"):
            log_error(
                f"Existing worktree is on integration branch '{branch}'. "
                "Evolution mode requires an isolated feature branch."
            )
            return 1

        worktree_path = wt_p
        wt_rel = existing_worktree
        if write_worktree_context(plan_path, branch, wt_rel):
            log_success(f"Plan Worktree metadata bound to existing worktree: {branch} ({wt_rel})")
        else:
            log_error("Failed to write Worktree metadata to Plan")
            return 1

    elif use_worktree:
        if not project:
            log_error("Cannot create worktree: no Target Project in plan")
            return 1

        # Read Project Type from Plan metadata
        project_type_str = get_plan_field(plan_path, "Project Type")

        # Generate branch name from full Plan name: <project>-<plan-name>
        branch = _derive_branch(project, plan_name)

        # Determine planned worktree path (without creating it yet)
        if project_type_str == ProjectType.ONTOLOGY_WORKTREE.value:
            worktrees_dir = workspace_root / ".worktrees"
            worktree_name = branch
            worktree_path = worktrees_dir / worktree_name
        else:
            # Standard: worktree dir = branch (branch already has project prefix)
            worktree_base = workspace_root / ".worktrees"
            branch_slug = branch.replace("/", "-")
            worktree_path = worktree_base / branch_slug
        
        # Block on unmerged files for standard projects
        if project_type_str != ProjectType.ONTOLOGY_WORKTREE.value:
            if project_path and _has_unmerged_files(str(project_path)):
                log_error(f"目标项目 {project} 有未解决的合并冲突（UU 状态），请先解决后再执行 approve")
                return 1
            
            # Warn about dirty workspace but proceed
            if dirty_workspace:
                log_warn(f"目标项目 {project} 有未提交的变更，建议先提交后再执行 approve")

        # Write minimal Worktree metadata (branch + path) to Plan
        wt_rel = str(worktree_path)
        if write_worktree_context(plan_path, branch, wt_rel):
            log_success(f"Plan Worktree metadata written: {branch}")
        else:
            log_warn("Failed to write Worktree metadata to Plan")

    elif dirty_workspace:
        # --no-worktree with dirty workspace: block and warn
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
        )
        git_status = status_result.stdout.strip()
        
        log_error(f"目标项目 {project} 有未提交的变更")
        print("")
        print("未提交文件列表:")
        for line in git_status.split('\n')[:10]:
            if line:
                print(f"  {line}")
        print("")
        print("风险: 新任务与旧变更混在一起会污染当前 Issue，增加回滚与验证成本")
        print("")
        print("建议处理方式:")
        print(f"  1. 先提交当前变更: cd {project_path} && git add . && git commit")
        print(f"  2. 默认会创建 worktree 隔离（当前使用了 --no-worktree）")
        print("")
        return 1
    
    # ============================================
    # STATE TRANSITION (commit Plan BEFORE worktree creation)
    # ============================================
    
    log_step(f"Transitioning state: {current_status} -> executing")
    
    # Update Plan status to executing
    if not update_plan_status(plan_path, "executing"):
        log_error("Failed to update Plan status")
        return 1
    
    log_success("Plan status updated to: executing")
    
    # Commit/push the Plan baseline (executing + Worktree metadata) on integration branch
    result = commit_and_push_plan(plan_path, issue_number, workspace_root, message_prefix="approve")
    if result == RESULT_PUSH_FAILED:
        log_error("Approve succeeded locally but push failed. See error above.")
        return 1
    if result != RESULT_OK:
        log_error("Failed to commit Plan baseline")
        return 1
    
    # ============================================
    # WORKTREE CREATION (after Plan baseline is committed)
    # ============================================
    
    if use_worktree and branch and worktree_path:
        project_type_str = get_plan_field(plan_path, "Project Type")

        if project_type_str == ProjectType.ONTOLOGY_WORKTREE.value:
            # Resolve ontology main repo path
            main_repo = get_ontology_main_repo(workspace_root)
            if main_repo is None:
                log_error("无法解析 ontology 主仓库路径")
                log_error("请检查 .wopal/.git 文件是否存在且格式正确（worktree 指针）")
                return 1
            
            log_step("Creating ontology worktree from committed baseline...")
            log_info(f"Main repo: {main_repo}")
            log_info(f"Branch: {branch}")
            
            # Determine base branch from .wopal/ worktree's current branch
            ontology_worktree = workspace_root / ".wopal"
            base_branch = get_current_branch(ontology_worktree)
            if not base_branch:
                log_error("无法解析 ontology worktree 当前分支")
                return 1

            # Create feature branch from base branch in the main repo
            branch_result = subprocess.run(
                ["git", "branch", branch, base_branch],
                cwd=str(main_repo),
                capture_output=True,
                text=True,
            )
            if branch_result.returncode != 0:
                log_error(f"创建 feature 分支失败: {branch}")
                print(branch_result.stderr)
                return 1
            log_info(f"Created branch: {branch} (from {base_branch})")
            
            # Create worktree from the new branch
            wt_result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch],
                cwd=str(main_repo),
                capture_output=True,
                text=True,
            )
            if wt_result.returncode != 0:
                log_error("Ontology worktree 创建失败")
                print(wt_result.stderr)
                # Cleanup: delete the branch we just created
                subprocess.run(
                    ["git", "branch", "-d", branch],
                    cwd=str(main_repo),
                    capture_output=True,
                )
                return 1
            
            log_success(f"Ontology worktree created: {worktree_path}")
            worktree_created = True

        else:
            # Standard project: create worktree from committed baseline
            if not project_path:
                log_error(f"无法解析项目路径: {project}")
                return 1
            
            log_step("Creating worktree from committed baseline...")
            actual_wt_path = _create_worktree(project_path, branch, workspace_root)
            if actual_wt_path is not None:
                worktree_created = True
                worktree_path = actual_wt_path
                log_success(f"Worktree created: {worktree_path}")
            else:
                log_error("Worktree creation failed - aborting approve")
                print("")
                print("Plan 状态保持 planning，未进入 executing")
                print("请检查 worktree 创建失败原因后重试")
                return 1
    
    # ============================================
    # Record Base Commit (implementation baseline)
    # ============================================
    # 记录实施基线。对于独立分支是集成分支 HEAD；对于 --existing-worktree 演进模式，
    # 记录该 worktree 当前分支的 HEAD（即上个 Plan 实施产物的终点）。
    base_commit = ""
    try:
        if existing_worktree and worktree_path and branch:
            base_commit = get_branch_head(str(worktree_path), branch)
        else:
            project_type_str = get_plan_field(plan_path, "Project Type")
            if project_type_str == ProjectType.ONTOLOGY_WORKTREE.value:
                main_repo = get_ontology_main_repo(workspace_root)
                if main_repo:
                    base_commit = get_branch_head(str(main_repo), get_current_branch(workspace_root / ".wopal"))
            elif project_path:
                base_commit = get_branch_head(str(project_path), "main")
    except (subprocess.CalledProcessError, FileNotFoundError):
        base_commit = ""

    if base_commit:
        set_plan_field(plan_path, "Base Commit", base_commit)
        log_success(f"Base Commit recorded: {base_commit}")

    # ============================================
    # Issue sync (if plan has Issue link)
    # ============================================

    if issue_number:
        # Sync Issue status label (planning -> in-progress)
        sync_status_label(issue_number, "executing", repo)
        
        # Sync approved plan to Issue body (automatic)
        sync_plan_to_issue_body(issue_number, plan_path, repo, str(workspace_root))
        
        # Ensure Issue labels are correct
        ensure_issue_labels(issue_number, plan_path, repo)
    
    # Output confirmation
    print("Status: executing")
    if issue_number:
        print(f"Issue: #{issue_number}")
    if worktree_created:
        print(f"Worktree: {worktree_path}")
    
    # Use issue_number for Issue-driven mode, plan_name for no-issue mode
    next_ref = str(issue_number) if issue_number else plan_name
    print("")
    print(f"Next: flow.sh complete {next_ref}")
    print("")
    print(f"实施完成后，执行: flow.sh complete {next_ref}")
    
    return 0


# ============================================
# argparse registration
# ============================================

def register_approve_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register approve subcommand."""
    approve_parser = subparsers.add_parser(
        "approve",
        help="Approve Plan and transition to executing phase"
    )
    approve_parser.add_argument(
        "target",
        nargs="?",
        help="Issue number or Plan name"
    )
    approve_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm approval and transition state"
    )
    approve_parser.add_argument(
        "--no-worktree",
        action="store_true",
        help="Skip worktree creation (worktree is created by default)"
    )
    approve_parser.add_argument(
        "--existing-worktree",
        type=str,
        default=None,
        help="Reuse an existing worktree directory/branch instead of creating a new one (evolution mode)"
    )
