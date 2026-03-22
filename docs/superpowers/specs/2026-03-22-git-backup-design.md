# Git Backup Feature Design

## Overview

为 QuidClaw 用户数据目录添加 Git 版本控制和远程备份能力。所有写操作完成后自动 commit，并异步 push 到用户配置的远程仓库。

**核心原则：** 纯标准 Git 操作，不依赖任何平台 API。用户提供仓库 URL，其余全自动。支持多个远程仓库实现多重备份。

## 1. Onboarding 流程

### 1.1 Git 检测

在 `quidclaw init` 执行时：

1. 检测 `git` 是否可用（`git --version`）
2. 如果不可用：
   - macOS：提示 `xcode-select --install` 或 `brew install git`
   - Linux：提示 `sudo apt install git` / `sudo yum install git`
   - 输出提示后继续初始化（Git 不是必须的，不阻塞）

### 1.2 Git 初始化

检测到 `git` 可用后：

1. 询问用户是否启用 Git 备份
2. 如果启用：
   - `git init` 初始化数据目录
   - 生成 `.gitignore`（见 §4）
   - 生成 `.gitattributes`（见 §5 LFS 配置）
   - 初始提交："Initialize QuidClaw data directory"
3. 如果不启用：跳过，后续可通过 `quidclaw backup init` 手动启用

### 1.3 远程仓库配置（支持多个）

启用 Git 后，询问用户是否要备份到远程：

1. 提示支持的平台：GitHub、Gitee、GitLab、Gitea 或任意 Git 服务
2. 用户提供仓库 URL 和一个名称（如 "github"、"gitee"）
3. 执行 `git remote add <name> <URL>`
4. 提示用户确保：
   - 仓库已创建（提供各平台创建仓库的链接）
   - 仓库设为 **Private**（财务数据！）
   - SSH key 或 HTTPS credential 已配置
   - 如果使用 LFS：平台已启用 LFS 支持
5. 尝试 `git push -u <name> main`，成功则配置完成
6. 如果失败，输出具体错误和排查建议，用户自行解决后可重试 `quidclaw backup push`
7. **可重复此步骤添加多个远程** — 如同时备份到 GitHub 和 Gitee

**注意：** 授权配置由用户自行完成，QuidClaw 只提示操作步骤。

**多远程示例：**
```bash
git remote add github https://github.com/user/my-finances.git
git remote add gitee  https://gitee.com/user/my-finances.git
# push 时逐个推送，任一失败不影响其他
```

## 2. 核心模块：`core/backup.py`

### 2.1 BackupManager 类

```python
class BackupManager:
    """Git-based backup for QuidClaw data directories."""

    def __init__(self, config: QuidClawConfig):
        self.data_dir = config.data_dir

    # --- 检测 ---

    def is_git_available(self) -> bool:
        """Check if git CLI is installed."""

    def is_initialized(self) -> bool:
        """Check if data_dir is a git repo."""

    def list_remotes(self) -> list[dict]:
        """List all configured remotes. Returns [{"name": "github", "url": "..."}]."""

    def has_remotes(self) -> bool:
        """Check if any remote is configured."""

    def is_lfs_available(self) -> bool:
        """Check if git-lfs is installed."""

    # --- 初始化 ---

    def init(self) -> None:
        """Initialize git repo, .gitignore, .gitattributes, initial commit."""

    def add_remote(self, name: str, url: str) -> None:
        """Add a named remote (e.g., 'github', 'gitee')."""

    def remove_remote(self, name: str) -> None:
        """Remove a named remote."""

    def setup_lfs(self) -> None:
        """Install LFS hooks and track patterns."""

    # --- 日常操作 ---

    def auto_commit(self, message: str) -> bool:
        """Stage all changes and commit. Returns True if committed (had changes)."""
        # git add -A
        # git diff --cached --quiet → if no changes, return False
        # git commit -m message
        # return True

    def auto_push(self) -> None:
        """Push to ALL remotes asynchronously. Each remote independent, fail silently."""
        # For each remote: fire-and-forget subprocess
        # Any single remote failure does not affect others

    def commit_and_push(self, message: str) -> bool:
        """auto_commit + auto_push. Returns True if committed."""
        if self.auto_commit(message):
            self.auto_push()
            return True
        return False

    # --- 状态 ---

    def status(self) -> dict:
        """Return backup status: initialized, remotes[], last_commit, unpushed_counts, lfs_tracked."""

    def get_install_instructions(self) -> str:
        """Return platform-specific git install instructions."""
```

### 2.2 Git 命令执行

所有 Git 操作通过 `subprocess.run()` 调用，在 `data_dir` 下执行：

```python
def _run_git(self, *args, check=True, capture=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=self.data_dir,
        check=check,
        capture_output=capture,
        text=True,
    )
```

### 2.3 异步 Push（多远程）

push 为每个 remote 启动独立的 `subprocess.Popen` fire-and-forget，不阻塞主流程：

```python
def auto_push(self) -> None:
    remotes = self.list_remotes()
    if not remotes:
        return
    for remote in remotes:
        try:
            subprocess.Popen(
                ["git", "push", remote["name"]],
                cwd=self.data_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass  # silently skip
```

每个 remote 独立推送，互不影响。GitHub 推送失败不影响 Gitee。

## 3. CLI 集成

### 3.1 新增命令组：`quidclaw backup`

```
quidclaw backup init                    # 手动初始化 Git 备份
quidclaw backup add-remote NAME URL     # 添加远程仓库（可多次调用）
quidclaw backup remove-remote NAME      # 移除远程仓库
quidclaw backup push [--remote NAME]    # 手动触发 push（默认全部，可指定）
quidclaw backup status [--json]         # 查看备份状态（含各 remote 状态）
```

### 3.2 写操作自动 commit + push

所有修改数据的 CLI 命令，在成功执行后调用 `backup.commit_and_push(message)`：

| CLI 命令 | Commit Message |
|----------|---------------|
| `init` | "Initialize QuidClaw data directory" |
| `setup` | "Set up default accounts" |
| `set-config K V` | "Update config: {K}" |
| `add-account NAME` | "Add account: {NAME}" |
| `close-account NAME` | "Close account: {NAME}" |
| `add-txn` | "Add transaction: {payee} {amount}" |
| `balance-check` | "Add balance assertion: {account}" |
| `add-commodity` | "Add commodity: {name}" |
| `fetch-prices` | "Fetch prices" |
| `sync` | "Sync: {new_count} new items from {source}" |
| `mark-processed` | "Mark processed: {source}/{dir}" |
| `add-source` | "Add data source: {name}" |
| `remove-source` | "Remove data source: {name}" |
| `upgrade` | "Upgrade QuidClaw workflows" |

**读操作不触发 backup：** `balance`、`query`、`report`、`list-accounts`、`list-sources`、`data-status` 等。

### 3.3 集成方式

在每个写命令的末尾添加 backup 调用：

```python
@cli.command()
@click.argument("name")
@click.pass_context
def add_account(ctx, name, ...):
    config = ctx.obj["config"]
    ledger = Ledger(config)
    ledger.add_account(name, ...)
    click.echo(f"Account opened: {name}")

    # Git backup
    backup = BackupManager(config)
    if backup.is_initialized():
        backup.commit_and_push(f"Add account: {name}")
```

为减少重复，提供一个辅助函数：

```python
def try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized. Never raises."""
    try:
        backup = BackupManager(config)
        if backup.is_initialized():
            backup.commit_and_push(message)
    except Exception:
        pass  # backup failure never blocks operations
```

## 4. .gitignore

`backup.init()` 生成的 `.gitignore`：

```gitignore
# QuidClaw — auto-generated, do not edit
# Temporary files
inbox/

# Secrets (API keys in config)
.quidclaw/config.yaml

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*~
```

**纳入 Git 的内容：**
- `ledger/` — 核心财务数据
- `documents/` — 归档文档
- `notes/` — 知识库
- `logs/` — 审计日志
- `sources/` — 原始邮件数据（审计可溯源）
- `reports/` — 生成的报告
- `.quidclaw/workflows/` — workflow 版本化

## 5. Git LFS 配置

### 5.1 .gitattributes

`backup.init()` 生成（当 LFS 可用时）：

```gitattributes
# QuidClaw LFS — track binary files
documents/**/*.pdf filter=lfs diff=lfs merge=lfs -text
documents/**/*.png filter=lfs diff=lfs merge=lfs -text
documents/**/*.jpg filter=lfs diff=lfs merge=lfs -text
documents/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
documents/**/*.gif filter=lfs diff=lfs merge=lfs -text
documents/**/*.xlsx filter=lfs diff=lfs merge=lfs -text
documents/**/*.xls filter=lfs diff=lfs merge=lfs -text
documents/**/*.docx filter=lfs diff=lfs merge=lfs -text
documents/**/*.doc filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.pdf filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.png filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.jpg filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.jpeg filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.gif filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.xlsx filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.xls filter=lfs diff=lfs merge=lfs -text
```

### 5.2 LFS 初始化

```python
def setup_lfs(self) -> None:
    if not self.is_lfs_available():
        return
    self._run_git("lfs", "install", "--local")
    # .gitattributes is written by init(), lfs install hooks into the repo
```

### 5.3 LFS 不可用时的处理

如果用户没有安装 `git-lfs`：
- 提示安装方法（`brew install git-lfs` / `apt install git-lfs`）
- **不阻塞初始化** — 二进制文件仍然可以用普通 Git 管理，只是效率低
- 在 `backup status` 中提示 "LFS not installed, binary files stored without LFS"

## 6. 配置存储

在 `.quidclaw/config.yaml` 中新增 `backup` 配置段：

```yaml
operating_currency: CNY
backup:
  enabled: true
  auto_commit: true
  auto_push: true
  # Remote URLs are managed by git itself (git remote), not duplicated here.
  # Use `git remote -v` or `quidclaw backup status` to see configured remotes.
```

**注意：** `config.yaml` 本身在 `.gitignore` 中（含 API key），所以 `remote_url` 不会被提交。这是正确的 — 远程地址已经通过 `git remote` 配置在 `.git/config` 里了，`config.yaml` 里的 `remote_url` 仅用于 QuidClaw 自身的状态判断。

## 7. Onboarding Workflow 更新

更新 `workflows/onboarding.md`，在现有流程末尾（邮件设置之后）添加 Git 备份设置阶段：

```markdown
## Phase: Git Backup Setup

1. Run `quidclaw backup status --json` to check current state
2. If git is not available:
   - Inform user: "Git is not installed. Installing Git enables automatic backup of your financial data."
   - Provide install instructions for their platform
   - If user declines, skip this phase
3. If git is available but not initialized:
   - Ask: "Would you like to enable automatic backup for your data?"
   - If yes: Run `quidclaw backup init`
4. Ask if user wants remote backup:
   - "You can back up to a private repository on GitHub, Gitee, GitLab, or any Git hosting service."
   - "This keeps your data safe even if your computer is lost or damaged."
   - If yes: ask for repository URL and name (e.g., "github"), run `quidclaw backup add-remote NAME URL`
   - Ask if user wants to add another remote for multi-backup (e.g., "Also back up to Gitee?")
   - Remind: "Make sure the repository is set to Private — this is your financial data!"
   - Guide: provide platform-specific instructions for SSH/HTTPS auth setup
5. If LFS not installed but backup enabled:
   - Suggest installing git-lfs for efficient binary file storage
```

## 8. 错误处理

**核心原则：备份失败绝不阻塞正常操作。**

| 场景 | 处理方式 |
|------|----------|
| git 未安装 | `is_initialized()` 返回 False，跳过 backup |
| git repo 未初始化 | 同上 |
| commit 失败 | `try_backup` 捕获异常，静默跳过 |
| push 失败（网络） | Popen fire-and-forget，不影响主流程，不影响其他 remote |
| push 失败（权限） | 同上，`backup status` 会显示各 remote 的 unpushed 状态 |
| 部分 remote 失败 | 各 remote 独立推送，互不影响 |
| LFS 未安装 | 文件用普通 Git 管理，status 提示 |
| merge conflict（远程有变更） | `backup status` 提示，用户手动解决 |

## 9. 文件清单

### 新增文件
- `src/quidclaw/core/backup.py` — BackupManager 类
- `tests/core/test_backup.py` — 单元测试

### 修改文件
- `src/quidclaw/cli.py` — 新增 `backup` 命令组 + 写操作集成 `try_backup`
- `src/quidclaw/config.py` — 新增 backup 配置属性
- `src/quidclaw/workflows/onboarding.md` — 新增 Git Backup Setup 阶段
- `tests/test_cli.py` — 新增 backup 命令测试
- `docs/cli-reference.md` — 新增 backup 命令文档
- `docs/architecture.md` — 新增 backup 模块说明

### 不需要新增的
- 无平台适配层（纯标准 Git）
- 无新依赖（subprocess 调用 git CLI）
- 无后台进程（push 是 fire-and-forget subprocess）
