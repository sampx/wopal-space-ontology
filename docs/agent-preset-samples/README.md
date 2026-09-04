# dsh agent preset 样例 — 评审用生成物说明

本目录是 `AGENT-TOOL-MAP.review.md`（能力映射表）第 4 节的实证附件：把 ellamaka 的 wopal / fae / rook 三个灵魂**翻译成 dsh 的 agent preset**，persona 完整复刻 `.wopal/agents/*.md` 的灵魂正文。

> **重要**：这些是**评审附件**，不是已安装到 dsh 的配置单。评审通过后才会真正启用。

---

## 这套东西是干什么的

ellamaka 用 Markdown 定义 agent（`agents/*.md`），dsh 用 `agent.cordis.yml` 定义 agent。dsh 不认识 ellamaka 的格式，ellamaka 也不认识 dsh 的格式。本目录的每个子目录，就是把一个 ellamaka agent「翻译」成 dsh 能读的格式的产物。

每个 agent preset 由两类文件组成：

| 文件 | 作用 |
|---|---|
| `preset.yml` | 给 dsh UI 看的「名片」：名字、一句话描述、排序 |
| `agent.cordis.yml` | 真正的配置单：**persona**（灵魂/系统提示词）+ **一堆工具行**（这个 agent 能调用哪些能力） |

---

## 三个角色一图看懂

| 目录 | 角色 | 一句话 | 给了哪些工具 |
|---|---|---|---|
| `wopal/` | 全能巫师 | 什么都做：规划、委派、审查、解决任何问题 | 工具最全：文件、shell、全部技能、plan、委派、询问、todo、goal |
| `fae/` | 执行精灵 | 只执行明确工作，不做规划/审查/委派 | 工具最少：文件、shell、仅 skill-creator 技能、todo。**没有**询问用户、**没有** plan、**没有**委派 |
| `rook/` | 黑门乌鸦 | 只读审查，绝不写文件/执行修复 | 文件(读)、shell(读输出取证)、仅两个 review 技能、todo。**没有**询问、**没有**委派、**禁写** |

「给了哪些工具」不是随手列的，是照着 `AGENT-TOOL-MAP.review.md` 第 4 节的意图翻译表填的——每个 agent 的灵魂正文里声明了它该不该有某项能力，翻译表决定它在 dsh 里挂哪些工具行。

---

## 每个工具行是什么

配置单里的每一条 `- id: tool-xxx` 就是给这个 agent 装的一个「能力」= 模型能看到并调用的一类工具。

| 工具行 id | 是干什么的 | 装给谁 |
|---|---|---|
| `persona` | 灵魂：一段系统提示词，定义这个 agent 是谁、怎么思考、怎么说话 | 三个都有 |
| `tool-fs` | 文件系统读写（读文件 / 写文件 / 编辑） | 三个都有 |
| `tool-fs-search` | 文件检索（glob / grep 找代码） | 三个都有 |
| `tool-bash` / `tool-pwsh` | 跑 shell 命令（构建、测试） | 三个都有 |
| `skill-filesystem` | 让技能目录里的 skill 生效 | 三个都有 |
| `tool-skill` | 让 agent 能查看和加载技能 | 三个都有 |
| `tool-ask-user` | 向用户提问确认 | 只给 wopal（fae/rook 权限声明里 question=deny） |
| `tool-todo` | TodoWrite 任务追踪 | 三个都有（灵魂正文都要求用 todo） |
| `plan-mode` 组 | 进入规划模式 | 只给 wopal（fae 声明 plan_enter=deny） |
| `tool-subagent` 等委派组 | 生成子代理、委派协作 | 只给 wopal（fae/rook 声明 task=deny） |
| `tool-goal` | 长期目标 | 只给 wopal |
| 上面的 `compaction` 组 | 上下文自动压缩，防止 token 爆炸 | 只给 wopal（样例；fae/rook 可自行加） |

「不挂某个工具行」不是 bug，是**权限意图的翻译**：ellamaka 说 question=deny，dsh 就不给 `tool-ask-user`；说 task=deny，就不给委派组。这样模型在 dsh 里**根本看不到**不该有的工具，从源头做不到越权，还省 token。

---

## 技能白名单 = 物理目录隔离（评审关注点）

dsh 没有「技能白名单」这个字段。ellamaka 的 `skill: {"*": deny, skill-creator: allow}`（fae）和 `skill: {df-plan-review, df-implement-review}`（rook）翻译成 dsh 时，靠的是：

- `skill-filesystem` 的 `customSkillDirs` 只指向一个**只含白名单技能的目录**
- 也就是要为 fae / rook **各建一个 `skills/` 子目录**，把允许的技能副本放进去

代价：技能内容更新后要同步到这些 `skills/` 副本。这是评审时要裁决的点（见评审文档第 5 节）。

---

## 怎么真正安装运行（评审通过后）

1. 把目录复制到 dsh 的用户 preset 根：
   ```bash
   cp -r wopal fae rook ~/.wopal/dsh/state/.agent-presets/
   ```
2. fae / rook 需把技能就位到各自的 `skills/` 子目录（见上节）：
   ```bash
   # fae — 只放 skill-creator
   mkdir -p ~/.wopal/dsh/state/.agent-presets/fae/skills
   cp -r .wopal/skills/skill-creator ~/.wopal/dsh/state/.agent-presets/fae/skills/
   # rook — 只放两个 review 技能
   mkdir -p ~/.wopal/dsh/state/.agent-presets/rook/skills
   cp -r .wopal/skills/df-plan-review ~/.wopal/dsh/state/.agent-presets/rook/skills/
   cp -r .wopal/skills/df-implement-review ~/.wopal/dsh/state/.agent-presets/rook/skills/
   ```
3. 需要在 dsh web 的配置单 roster 里把这些 preset 挂为可选项（见 poc DESIGN-dsh-poc 的空间定制流程）。
4. 重启 dsh / 新建会话，选择对应 preset，验证工具可见性与灵魂生效。

---

## persona 里为什么有一些 `[CSS-x]` 标记

复刻灵魂时，个别句子提到 ellamaka 特有、dsh 里不存在的东西，我用 `[CSS-x]` 标出并做了最小改动，方便你评审时核对每一处裁剪是否合理。具体裁剪点见各 `agent.cordis.yml` 文件头部的注释。

**wopal 裁剪 1 处**：Phase 7 里的 `memory_manage command=search` 工具名引用 — dsh 无此工具，改成「主动召回记忆/空间上下文」的原则表述。

**fae 裁剪 2 处**：①「Prefer Task tool」— fae 无委派、dsh 无 Task 工具，改用文件搜索工具；② WebFetch 重定向句 — fae 无 web 工具。

**rook 裁剪 0 处**：全文与 dsh 兼容，零裁剪。
