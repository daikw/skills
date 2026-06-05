#!/usr/bin/env python3
"""Claude Code hook: サプライチェーンセキュリティガード

PreToolUse: npx/bunx/uvx の使用と install script 保護の緩和を deny
PostToolUse: package.json/pyproject.toml/Dockerfile 編集後に lockfile 整合性と digest pinning を検証
"""
import json
import re
import subprocess
import sys
from pathlib import Path

NODE_LOCKFILES = ("pnpm-lock.yaml", "package-lock.json", "npm-shrinkwrap.json")
PY_LOCKFILES = ("uv.lock",)
NODE_DEP_KEYS = ("dependencies", "devDependencies", "optionalDependencies", "overrides")
PYPROJECT_TABLES = (
    ("project", "dependencies"),
    ("dependency-groups",),
    ("tool", "uv", "dev-dependencies"),
)


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))


def git_root(start: Path):
    result = run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def rel_to_root(root: Path, path: Path):
    return path.resolve().relative_to(root.resolve()).as_posix()


def find_upwards(start: Path, names, stop_at=None):
    current = start.resolve()
    stop = stop_at.resolve() if stop_at else None
    while True:
        for name in names:
            candidate = current / name
            if candidate.exists():
                return candidate
        if stop and current == stop:
            return None
        if current.parent == current:
            return None
        current = current.parent


def is_modified(path: Path):
    root = git_root(path.parent)
    if not root:
        return False
    result = run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", rel_to_root(root, path)]
    )
    return bool(result.stdout.strip())


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_head_json(path: Path):
    root = git_root(path.parent)
    if not root:
        return {}
    result = run(["git", "-C", str(root), "show", f"HEAD:{rel_to_root(root, path)}"])
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except Exception:
        return {}


def node_dependency_changed(path: Path):
    current = load_json(path)
    head = load_head_json(path)
    for key in NODE_DEP_KEYS:
        if (current.get(key) or {}) != (head.get(key) or {}):
            return True
    return False


def python_dependency_changed(path: Path):
    try:
        import tomllib
    except ModuleNotFoundError:
        return True

    def load_toml_file(file_path: Path):
        try:
            return tomllib.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def load_head_toml(file_path: Path):
        root = git_root(file_path.parent)
        if not root:
            return {}
        result = run(["git", "-C", str(root), "show", f"HEAD:{rel_to_root(root, file_path)}"])
        if result.returncode != 0:
            return {}
        try:
            return tomllib.loads(result.stdout)
        except Exception:
            return {}

    def get_nested(obj, keys):
        cur = obj
        for key in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
        return cur

    current = load_toml_file(path)
    head = load_head_toml(path)
    for keys in PYPROJECT_TABLES:
        if get_nested(current, keys) != get_nested(head, keys):
            return True
    project_current = ((current.get("project") or {}).get("optional-dependencies") or {})
    project_head = ((head.get("project") or {}).get("optional-dependencies") or {})
    return project_current != project_head


def is_dockerfile(path: Path):
    name = path.name
    return name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile")


def check_package_json(path: Path):
    if not path.exists() or not node_dependency_changed(path):
        return []
    root = git_root(path.parent)
    lockfile = find_upwards(path.parent, NODE_LOCKFILES, stop_at=root) if root else None
    issues = []
    if not lockfile:
        issues.append(f"{path}: package.json の依存変更に対応する lockfile が見つからない")
    elif not is_modified(lockfile):
        issues.append(f"{path}: package.json の依存変更後に {lockfile.name} が更新されていない")
    return issues


def check_pyproject(path: Path):
    if not path.exists() or not python_dependency_changed(path):
        return []
    root = git_root(path.parent)
    lockfile = find_upwards(path.parent, PY_LOCKFILES, stop_at=root) if root else None
    issues = []
    if not lockfile:
        issues.append(f"{path}: pyproject.toml の依存変更に対応する uv.lock が見つからない")
    elif not is_modified(lockfile):
        issues.append(f"{path}: pyproject.toml の依存変更後に uv.lock が更新されていない")
    return issues


def check_dockerfile(path: Path):
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [f"{path}: Dockerfile を UTF-8 として読めないため検証できない"]

    issues = []
    stage_aliases = set()
    pattern = re.compile(r"^FROM(?:\s+--[^\s]+)*\s+([^\s]+)(?:\s+AS\s+([A-Za-z0-9._-]+))?\s*$", re.IGNORECASE)

    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        image_ref, alias = match.groups()
        image_lower = image_ref.lower()

        if image_lower == "scratch" or image_lower in stage_aliases:
            if alias:
                stage_aliases.add(alias.lower())
            continue

        if "${" in image_ref and "@sha256:" not in image_lower:
            issues.append(f"{path}:{lineno}: FROM {image_ref} は変数展開で digest を確認できない。tag@sha256 で固定する")
        elif ":latest" in image_lower:
            issues.append(f"{path}:{lineno}: FROM {image_ref} で latest タグは禁止")
        elif "@sha256:" not in image_lower:
            if ":" not in image_ref:
                issues.append(f"{path}:{lineno}: FROM {image_ref} は暗黙 latest。明示タグ + digest で固定する")
            else:
                issues.append(f"{path}:{lineno}: FROM {image_ref} は digest pinning がない。tag@sha256 で固定する")

        if alias:
            stage_aliases.add(alias.lower())

    return issues


def pre_tool_use(data):
    if data.get("tool_name") != "Bash":
        return

    command = (data.get("tool_input") or {}).get("command", "")

    banned_launcher = re.search(r"(^|[;&|()\s])(npx|bunx|uvx)(?=$|[\s])", command)
    banned_launcher = banned_launcher or re.search(r"(^|[;&|()\s])pnpm\s+dlx(?=$|[\s])", command)
    if banned_launcher:
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "ワンショット実行ランチャー（npx / bunx / pnpm dlx / uvx）は禁止。依存を明示追加し、lockfile を更新してから実行すること。",
                }
            }
        )
        return

    lowered_script_protection = [
        r"--ignore-scripts(?:=|\s+)false",
        r"npm_config_ignore_scripts=false",
        r"npm\s+config\s+set\s+ignore-scripts\s+false",
        r"pnpm\s+config\s+set\s+ignore-scripts\s+false",
        r"yarn\s+config\s+set\s+enableScripts\s+true",
    ]
    if any(re.search(pattern, command) for pattern in lowered_script_protection):
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "install script の保護を緩めるコマンドは禁止。必要なら依存の妥当性と script 実行理由を明示してレビューに回すこと。",
                }
            }
        )


def post_tool_use(data):
    files = []
    tool_input = data.get("tool_input") or {}
    tool_response = data.get("tool_response") or {}
    for candidate in (tool_input.get("file_path"), tool_response.get("filePath"), tool_response.get("file_path")):
        if candidate:
            files.append(Path(candidate))

    issues = []
    for path in files:
        if path.name == "package.json":
            issues.extend(check_package_json(path))
        elif path.name == "pyproject.toml":
            issues.extend(check_pyproject(path))
        elif is_dockerfile(path):
            issues.extend(check_dockerfile(path))

    if issues:
        emit(
            {
                "decision": "block",
                "reason": "Supply-chain policy violation:\n- " + "\n- ".join(issues),
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "Fix the supply-chain issue before continuing. Required fixes usually involve updating the lockfile or replacing an unpinned Docker base image with a digest-pinned reference.",
                },
            }
        )


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return
    data = json.loads(raw)
    event = data.get("hook_event_name")
    if event == "PreToolUse":
        pre_tool_use(data)
    elif event == "PostToolUse":
        post_tool_use(data)


if __name__ == "__main__":
    main()
