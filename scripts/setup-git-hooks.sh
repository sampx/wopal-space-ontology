#!/bin/bash
#
# Git Hooks 安装脚本
# 自动检测 projects/ 下所有子项目，根据 hooks 机制（husky 或原生）安装 commit-msg hook
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_HOOK="$SCRIPT_DIR/git-hooks/commit-msg"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   Git Hooks 安装脚本${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 检查源 hook 文件
if [ ! -f "$SOURCE_HOOK" ]; then
    echo -e "${RED}错误: 未找到源 hook 文件: $SOURCE_HOOK${NC}"
    exit 1
fi

# 收集所有需要安装的项目（空间根 + projects/ 下独立 git 仓库）
PROJECTS=()
PROJECTS+=("$WORKSPACE_ROOT")

# 遍历 projects/ 目录
for dir in "$WORKSPACE_ROOT/projects"/*; do
    if [ -d "$dir/.git" ]; then
        PROJECTS+=("$dir")
    fi
done

echo -e "${CYAN}检测到的项目:${NC}"
for p in "${PROJECTS[@]}"; do
    name=$(basename "$p")
    if [ "$p" = "$WORKSPACE_ROOT" ]; then
        name="workspace-root"
    fi
    echo "  - $name"
done
echo ""

# 检测项目的 hooks 机制
detect_hooks_mechanism() {
    local project_dir="$1"
    
    # 检查 husky: core.hooksPath 指向 .husky 或存在 .husky/_/ 目录
    local hooks_path
    hooks_path=$(cd "$project_dir" && git config core.hooksPath 2>/dev/null || echo "")
    
    if [[ "$hooks_path" =~ ^\.husky ]] || [ -d "$project_dir/.husky/_" ]; then
        echo "husky"
        return
    fi
    
    echo "native"
}

# 安装 hook 到项目
install_hook() {
    local project_dir="$1"
    local mechanism="$2"
    local target_file
    local project_name
    project_name=$(basename "$project_dir")
    [ "$project_dir" = "$WORKSPACE_ROOT" ] && project_name="workspace-root"
    
    if [ "$mechanism" = "husky" ]; then
        # Husky 项目: hook 放在 .husky/ 目录（不是 .husky/_/）
        # .husky/_/h 是 wrapper，会调用 .husky/<hook-name>
        target_file="$project_dir/.husky/commit-msg"
        
        # 确保 .husky 目录存在
        mkdir -p "$project_dir/.husky"
    else
        # 原生 Git hooks
        target_file="$project_dir/.git/hooks/commit-msg"
        
        # 确保 .git/hooks 目录存在
        mkdir -p "$project_dir/.git/hooks"
    fi
    
    # 检查是否已存在且内容相同
    if [ -f "$target_file" ]; then
        if cmp -s "$SOURCE_HOOK" "$target_file"; then
            echo -e "${GREEN}  ✓ $project_name: commit-msg 已存在且内容一致 (跳过)${NC}"
            return 0
        else
            echo -e "${YELLOW}  ⚠ $project_name: commit-msg 已存在但内容不同${NC}"
            if [ -t 0 ]; then
                echo -n "    是否覆盖? [y/N] "
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    echo -e "${BLUE}    跳过 $project_name${NC}"
                    return 0
                fi
            else
                # 非交互模式，自动覆盖
                echo -e "${CYAN}    自动覆盖${NC}"
            fi
        fi
    fi
    
    # 复制 hook 文件
    cp "$SOURCE_HOOK" "$target_file"
    chmod +x "$target_file"
    
    echo -e "${GREEN}  ✓ $project_name: 已安装 commit-msg ($mechanism)${NC}"
}

# 安装到每个项目
echo -e "${CYAN}安装 hooks:${NC}"
for project in "${PROJECTS[@]}"; do
    mechanism=$(detect_hooks_mechanism "$project")
    install_hook "$project" "$mechanism"
done

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   安装完成！${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "${BLUE}提示:${NC}"
echo "  - 提交消息必须遵循 Conventional Commits 规范"
echo "  - 格式: <type>: <description>"
echo "  - 示例: feat: 添加用户认证模块"
echo ""