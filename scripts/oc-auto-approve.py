#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode 权限弹窗自动批准脚本

功能：
- 监控 tmux 会话中的 OpenCode 权限弹窗
- 普通命令延迟后自动批准
- 高危命令播放警告声，永不自动批准
- 目标会话退出后自动退出

用法：
  python3 auto-approve.py start [session] [debug] [delay] [log_dir]
  python3 auto-approve.py status
"""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

# === 配置 ===
DEFAULT_TARGET = "my-opencode"
DEFAULT_DELAY = 5
CHECK_INTERVAL = 0.5

SOUND_FILE = "/System/Library/Sounds/Glass.aiff"
SOUND_WARNING = "/System/Library/Sounds/Hero.aiff"

# 全局日志目录（可选）
_log_dir: Path | None = None


def set_log_dir(log_dir: str | None) -> None:
    """设置日志目录，None 表示不记录日志。"""
    global _log_dir
    _log_dir = None
    if log_dir and (path := Path(log_dir)).is_dir():
        _log_dir = path


# === 高危命令规则 ===
HIGH_RISK_COMMANDS = [
    r"\bsudo\b",
    r"\bdoas\b",
    r"\bpkexec\b",
    r"\breboot\b",
    r"\bshutdown\b",
    r"\bhalt\b",
    r"\bpoweroff\b",
    r"\binit\s+[06]\b",
    r"\bsystemctl\s+(reboot|poweroff|halt|rescue|emergency)\b",
    r"\brm\s+-rf\s+/$",
    r"\brm\s+-rf\s+~",
    r"\brm\s+-rf\s+/home\b",
    r"\bchown\s+.*-R\s+/",
    r"\bchmod\s+.*-R\s+/",
    r"\bmkfs\b",
    r"\bfdisk\b",
    r"\bparted\b",
    r"\bdd\s+if=",
    r"\b:\(\)\{.*:\|:&\}",
    r">\s*/dev/sd[a-z]",
    r">\s*/dev/null\s+2>&1\s+&",
    r"\biptables\s+-F",
    r"\bip6tables\s+-F",
    r"\bnc\s+.*-e\s+/",
    r"\bcurl\s+.*\|\s*bash",
    r"\bwget\s+.*\|\s*bash",
    r"\bgit\s+reset\b",
]

USER_SYSTEM_DIRS = [
    "*/Library/*",
]

ROOT_SYSTEM_DIRS = [
    "/etc/",
    "/usr/",
    "/var/",
    "/System/",
    "/Applications/",
    "/private/",
]


def matchWildcard(text: str, pattern: str) -> bool:
    """简单的通配符匹配，* 匹配 0 或多个普通字符

    例如：
    - */Library/* 匹配 ~/Library/xxx, ../../Library/xxx
    - /etc/* 匹配 /etc/passwd
    """
    text = text.replace("~", "/").replace("../", "/").replace("./", "/")

    if "*" in pattern:
        prefix = pattern.replace("*", "").rstrip("/")
        return prefix in text
    return pattern in text


def is_root_system_dir_access(cmd: str) -> bool:
    """检查是否访问根系统目录（任何操作都高危）"""
    for pattern in ROOT_SYSTEM_DIRS:
        if matchWildcard(cmd, pattern):
            return True
    return False


def is_user_system_dir_access(cmd: str) -> bool:
    """检查是否访问用户系统目录（仅 rm/写入高危）"""
    for pattern in USER_SYSTEM_DIRS:
        if matchWildcard(cmd, pattern):
            return True
    return False


def is_high_risk(cmd: str) -> bool:
    """判断命令是否高危

    规则：
    - 根系统目录 (/etc, /usr 等) 任何访问都高危
    - 用户系统目录 (~/Library) 仅 rm/写入高危
    """
    if is_root_system_dir_access(cmd):
        return True

    if is_user_system_dir_access(cmd):
        if re.search(r"\brm\s", cmd):
            return True
        if re.search(r">(?!&)", cmd):
            return True

    return False


def has_dialog(screen_text: str) -> bool:
    """检查屏幕中是否有权限弹窗。"""
    return "Permission required" in screen_text and "Allow once" in screen_text


def find_dialog_bounds(lines: list[str]) -> tuple[int, int] | None:
    """定位弹窗边界，返回 (起始行, 结束行) 或 None。"""
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if "Permission required" in line and "△" in line:
            start_idx = i
        elif start_idx is not None and "Allow once" in line:
            end_idx = i
            break

    return (
        (start_idx, end_idx) if start_idx is not None and end_idx is not None else None
    )


INTERNAL_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Delete"]
ARROWS = ["←", "→"]


def extract_operation(screen_text: str) -> tuple[str, str | tuple[str, str]]:
    """从屏幕内容提取操作。

    策略：一次循环从下向上搜索，同时检查 bash 命令和内部工具特征。

    返回 (类型, 内容)：
    - ("bash", "rm ~/Library/xxx") - bash 命令
    - ("internal", ("Edit", "~/Library/xxx")) - 内部工具
    - ("unknown", "") - 未识别
    """
    if not has_dialog(screen_text):
        return ("unknown", "")

    lines = screen_text.split("\n")
    bounds = find_dialog_bounds(lines)
    if bounds is None:
        return ("unknown", "")

    dialog_start, dialog_end = bounds

    def check_line(line: str) -> tuple[str, str | tuple[str, str]]:
        after_bar = line
        if "┃" in line:
            after_bar = line.split("┃")[-1]
        after_bar = after_bar.strip()

        if not after_bar:
            return ("", "")

        for tool in INTERNAL_TOOLS:
            for arrow in ARROWS:
                pattern = f"{arrow} {tool}"
                if after_bar.startswith(pattern):
                    target = after_bar[len(pattern) :].strip()
                    return ("internal", (tool, target))

        if "$" in after_bar:
            cmd = after_bar.split("$", 1)[-1].strip()
            cmd = re.sub(r"\s+", " ", cmd).strip()
            if cmd:
                return ("bash", cmd)

        return ("", "")

    for i in range(dialog_end, max(0, dialog_start - 20), -1):
        if i >= len(lines):
            continue
        op_type, op_content = check_line(lines[i])
        if op_type:
            return (op_type, op_content)

    return ("unknown", "")


def play_sound(sound_file: str) -> None:
    """播放声音提示。"""
    subprocess.Popen(
        ["afplay", sound_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def tmux_capture(target: str, lines: int = 30) -> str:
    """捕获 tmux 会话屏幕内容。"""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", target, "-p"],
            capture_output=True,
            text=True,
        )
        output_lines = result.stdout.split("\n")
        return "\n".join(output_lines[-lines:])
    except Exception:
        return ""


def tmux_session_exists(session: str) -> bool:
    """检查 tmux 会话是否存在。"""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        capture_output=True,
    )
    return result.returncode == 0


def tmux_send_keys(target: str, *keys: str) -> None:
    """向 tmux 会话发送按键。"""
    subprocess.run(
        ["tmux", "send-keys", "-t", target] + list(keys),
        capture_output=True,
    )


def log(message: str, target: str, debug: bool = False) -> None:
    """记录日志。"""
    if _log_dir is None:
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_file = (
        _log_dir / f"auto-approve-{target}.log"
        if not debug
        else _log_dir / f"auto-approve-{target}-debug.log"
    )
    with open(log_file, "a") as f:
        f.write(f"{timestamp} {message}\n")


def log_print(message: str, target: str) -> None:
    """记录并打印日志。"""
    log(message, target)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}")


def cleanup_logs(target: str, debug: bool) -> None:
    """清理目标会话的日志文件。"""
    if _log_dir is None:
        return

    log_files = [_log_dir / f"auto-approve-{target}.log"]
    if debug:
        log_files.append(_log_dir / f"auto-approve-{target}-debug.log")

    for log_file in log_files:
        log_file.exists() and log_file.unlink(missing_ok=True)


def run_monitor(target: str, delay: int, debug: bool) -> None:
    """主监控循环。"""
    log_print(f"[START] target={target} delay={delay}s", target)

    waiting = False
    high_risk_mode = False
    wait_start = 0.0
    wait_log_count = 0
    MAX_WAIT_LOGS = 3
    current_op: tuple[str, str | tuple[str, str]] = ("unknown", "")
    missing_count = 0
    MAX_MISSING = 10

    while True:
        if not tmux_session_exists(target):
            missing_count += 1
            if missing_count >= MAX_MISSING:
                log_print(f"[EXIT] session '{target}' gone", target)
                cleanup_logs(target, debug)
                break
            time.sleep(CHECK_INTERVAL)
            continue

        missing_count = 0

        screen = tmux_capture(target, lines=30)

        if not has_dialog(screen):
            if waiting:
                log_print("[APPROVED] manual", target)
                waiting = False
                high_risk_mode = False
                wait_log_count = 0
                current_op = ("unknown", "")
            time.sleep(CHECK_INTERVAL)
            continue

        op_type, op_content = extract_operation(screen)

        if not waiting or (op_type, op_content) != current_op:
            if waiting:
                wait_log_count = 0

            if debug:
                log("=== Dialog ===", target, debug)
                log(screen, target, debug)
                log(f"Operation: ({op_type}, {op_content})", target, debug)

            if op_type == "internal":
                tool_type, tool_target = op_content
                if tool_type in ["Read", "Glob", "Grep"]:
                    log_print(f"[SAFE] {tool_type}: {tool_target}", target)
                    play_sound(SOUND_FILE)
                    high_risk_mode = False
                else:
                    log_print(f"[RISK] {tool_type}: {tool_target}", target)
                    play_sound(SOUND_WARNING)
                    high_risk_mode = True
            elif op_type == "bash":
                cmd = str(op_content)
                if is_high_risk(cmd):
                    log_print(f"[RISK] bash: {cmd}", target)
                    play_sound(SOUND_WARNING)
                    high_risk_mode = True
                else:
                    log_print(f"[SAFE] bash: {cmd}", target)
                    play_sound(SOUND_FILE)
                    high_risk_mode = False
            else:
                log_print("[SAFE] unknown (auto-approve)", target)
                play_sound(SOUND_FILE)
                high_risk_mode = False

            waiting = True
            current_op = (op_type, op_content)
            wait_start = time.time()
            wait_log_count = 0
            time.sleep(CHECK_INTERVAL)
            continue

        elapsed = time.time() - wait_start
        if elapsed >= delay:
            if high_risk_mode:
                if wait_log_count < MAX_WAIT_LOGS:
                    log_print(f"[WAIT] risk blocked ({wait_log_count + 1})", target)
                wait_log_count += 1
                wait_start = time.time()
            else:
                log_print("[APPROVED] auto", target)
                tmux_send_keys(target, "y", "Enter")
                waiting = False
                wait_log_count = 0
                current_op = ("unknown", "")
                time.sleep(2)

        time.sleep(CHECK_INTERVAL)


def start_monitor(target: str, debug: bool, delay: int, log_dir: str | None) -> None:
    """在 tmux 会话中启动监控。"""
    monitor_session = f"auto-approver-{target}"

    if tmux_session_exists(monitor_session):
        print(f"Restarting monitor for '{target}'...")
        subprocess.run(["tmux", "kill-session", "-t", monitor_session])
        time.sleep(0.5)

    print(f"Starting auto-approver for: {target}")
    print(f"Delay: {delay}s | Debug: {debug}")
    if log_dir:
        print(f"Log: {log_dir}/auto-approve-{target}.log")
    else:
        print("Log: disabled")

    cmd = f"python3 {sys.argv[0]} _run {target} {str(debug).lower()} {delay} '{log_dir or ''}'"

    subprocess.run(
        ["tmux", "new-session", "-d", "-s", monitor_session, cmd],
        check=True,
    )
    print(f"Monitor session: {monitor_session}")


def status_monitor() -> None:
    """显示监控状态。"""
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True,
        text=True,
    )

    monitors = [s for s in result.stdout.splitlines() if s.startswith("auto-approver")]

    if monitors:
        print("Running monitors:")
        for m in monitors:
            print(f"  - {m.removeprefix('auto-approver-')} ({m})")
    else:
        print("No monitors running")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenCode 权限弹窗自动批准",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s start                    # 使用默认配置启动
  %(prog)s start my-session true 5  # 指定会话、调试模式、延迟5秒
  %(prog)s start my-session false 10 ./logs  # 指定日志目录
  %(prog)s status                   # 查看状态

高危命令:
  - sudo, doas, pkexec
  - reboot, shutdown, halt, poweroff
  - rm -rf /, rm -rf ~
  - mkfs, fdisk, dd
  - 写入/删除系统目录 (/etc, /usr, /var 等)
""",
    )
    parser.add_argument(
        "command",
        choices=["start", "status", "_run"],
        help="操作命令",
    )
    parser.add_argument(
        "session",
        nargs="?",
        default=DEFAULT_TARGET,
        help="tmux 会话名",
    )
    parser.add_argument(
        "debug",
        nargs="?",
        default="false",
        help="调试模式 (true/false)",
    )
    parser.add_argument(
        "delay",
        nargs="?",
        type=int,
        default=DEFAULT_DELAY,
        help="延迟秒数",
    )
    parser.add_argument(
        "log_dir",
        nargs="?",
        default="",
        help="日志目录（空则不记录）",
    )

    args = parser.parse_args()

    debug = args.debug.lower() == "true"
    log_dir = args.log_dir or None

    if args.command == "start":
        start_monitor(args.session, debug, args.delay, log_dir)
    elif args.command == "status":
        status_monitor()
    elif args.command == "_run":
        set_log_dir(log_dir)
        run_monitor(args.session, args.delay, debug)


if __name__ == "__main__":
    main()
