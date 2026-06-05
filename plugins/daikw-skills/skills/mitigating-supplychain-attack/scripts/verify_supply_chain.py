#!/usr/bin/env python3
"""サプライチェーンリスク静的検証スクリプト

2つのモードで動作する:
  diff モード (デフォルト): git の変更ファイルのみ検査
  full モード (--full):     リポジトリ内の全対象ファイルを検査

git の変更ファイルから package.json / pyproject.toml / Dockerfile を検出し、
lockfile 整合性、バージョン固定、digest pinning を検証する。
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

NODE_LOCKFILES = ("pnpm-lock.yaml", "package-lock.json", "npm-shrinkwrap.json")
NODE_DEP_KEYS = ("dependencies", "devDependencies", "optionalDependencies", "overrides")
PY_LOCKFILES = ("uv.lock",)
RANGE_PREFIXES = ("^", "~", ">", "<", "=", "*")


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def git_root(start: Path):
    result = run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise SystemExit("git リポジトリ内で実行してください")
    return Path(result.stdout.strip())


def rel_to_root(root: Path, path: Path):
    return path.resolve().relative_to(root.resolve()).as_posix()


def changed_files(root: Path):
    result = run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"])
    files = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        files.append(root / path_text)
    return files


def all_target_files(root: Path):
    """リポジトリ内の全 package.json / pyproject.toml / Dockerfile を列挙する。"""
    result = run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"])
    files = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = root / line
        if path.name in ("package.json", "pyproject.toml") or is_dockerfile(path):
            files.append(path)
    return files


def find_upwards(start: Path, names, stop_at: Path):
    current = start.resolve()
    stop = stop_at.resolve()
    while True:
        for name in names:
            candidate = current / name
            if candidate.exists():
                return candidate
        if current == stop or current.parent == current:
            return None
        current = current.parent


def is_modified(root: Path, path: Path):
    result = run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", rel_to_root(root, path)]
    )
    return bool(result.stdout.strip())


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_head_text(root: Path, path: Path):
    result = run(["git", "-C", str(root), "show", f"HEAD:{rel_to_root(root, path)}"])
    if result.returncode != 0:
        return None
    return result.stdout


def load_head_json(root: Path, path: Path):
    text = load_head_text(root, path)
    if text is None:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}


def added_node_packages(root: Path, path: Path):
    current = load_json(path)
    head = load_head_json(root, path)
    added = []
    for section in NODE_DEP_KEYS:
        current_map = current.get(section) or {}
        head_map = head.get(section) or {}
        for name, version in current_map.items():
            if name not in head_map:
                added.append((section, name, version))
    return added


def is_exact_node_version(spec: str):
    if spec.startswith(("workspace:", "file:", "link:", "portal:", "patch:")):
        return True
    if spec in ("latest", "*", "x"):
        return False
    if any(spec.startswith(prefix) for prefix in RANGE_PREFIXES):
        return False
    if any(token in spec for token in ("git+", "github:", "http://", "https://", "npm:")):
        return False
    return bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", spec))


def check_package_json(root: Path, path: Path, *, diff_mode: bool):
    findings = []
    data = load_json(path)
    lockfile = find_upwards(path.parent, NODE_LOCKFILES, root)

    if diff_mode:
        if not lockfile:
            findings.append(f"ERROR {path}: package.json はあるが対応する lockfile が見つからない")
        elif is_modified(root, path) and not is_modified(root, lockfile):
            findings.append(f"ERROR {path}: package.json 変更に対して {lockfile.name} が更新されていない")
    else:
        if not lockfile:
            findings.append(f"ERROR {path}: package.json はあるが対応する lockfile が見つからない")

    for section in NODE_DEP_KEYS:
        deps = data.get(section) or {}
        for name, spec in deps.items():
            if not is_exact_node_version(spec):
                findings.append(f"ERROR {path}: {section}.{name} が固定バージョンではない ({spec})")

    return findings


def load_toml(path: Path):
    import tomllib
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_head_toml(root: Path, path: Path):
    import tomllib
    text = load_head_text(root, path)
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except Exception:
        return {}


def pep508_is_pinned(spec: str):
    head = spec.split(";", 1)[0].strip()
    if " @ " in head or head.startswith(("git+", "http://", "https://")):
        return False
    if "==" not in head:
        return False
    if any(op in head for op in (">=", "<=", "~=", ">", "<", "!=", "===")):
        return False
    if head.count("==") != 1:
        return False
    if "*" in head:
        return False
    return True


def extract_dependency_strings(pyproject: dict):
    deps = []
    project = pyproject.get("project") or {}

    for item in project.get("dependencies") or []:
        deps.append(("project.dependencies", item))

    for group, items in (project.get("optional-dependencies") or {}).items():
        for item in items or []:
            deps.append((f"project.optional-dependencies.{group}", item))

    for group, items in (pyproject.get("dependency-groups") or {}).items():
        for item in items or []:
            if isinstance(item, str):
                deps.append((f"dependency-groups.{group}", item))

    uv_tool = ((pyproject.get("tool") or {}).get("uv") or {})
    for item in uv_tool.get("dev-dependencies") or []:
        deps.append(("tool.uv.dev-dependencies", item))

    return deps


def added_python_packages(root: Path, path: Path):
    current = load_toml(path)
    head = load_head_toml(root, path)
    current_items = {item for _, item in extract_dependency_strings(current)}
    head_items = {item for _, item in extract_dependency_strings(head)}
    return sorted(current_items - head_items)


def check_pyproject(root: Path, path: Path, *, diff_mode: bool):
    findings = []
    data = load_toml(path)
    lockfile = find_upwards(path.parent, PY_LOCKFILES, root)

    if diff_mode:
        if not lockfile:
            findings.append(f"ERROR {path}: pyproject.toml はあるが uv.lock が見つからない")
        elif is_modified(root, path) and not is_modified(root, lockfile):
            findings.append(f"ERROR {path}: pyproject.toml 変更に対して uv.lock が更新されていない")
    else:
        if not lockfile:
            findings.append(f"ERROR {path}: pyproject.toml はあるが uv.lock が見つからない")

    for scope, spec in extract_dependency_strings(data):
        if not pep508_is_pinned(spec):
            findings.append(f"ERROR {path}: {scope} の依存が固定されていない ({spec})")

    return findings


def is_dockerfile(path: Path):
    name = path.name
    return name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile")


def check_dockerfile(path: Path):
    findings = []
    stage_aliases = set()
    pattern = re.compile(r"^FROM(?:\s+--[^\s]+)*\s+([^\s]+)(?:\s+AS\s+([A-Za-z0-9._-]+))?\s*$", re.IGNORECASE)

    lines = path.read_text(encoding="utf-8").splitlines()
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
            findings.append(f"ERROR {path}:{lineno}: FROM {image_ref} は変数展開で digest 未検証")
        elif ":latest" in image_lower:
            findings.append(f"ERROR {path}:{lineno}: FROM {image_ref} で latest タグを使用している")
        elif "@sha256:" not in image_lower:
            findings.append(f"ERROR {path}:{lineno}: FROM {image_ref} に digest pinning がない")

        if alias:
            stage_aliases.add(alias.lower())

    return findings


def main():
    parser = argparse.ArgumentParser(description="サプライチェーンリスク静的検証")
    parser.add_argument("--full", action="store_true", help="リポジトリ内の全対象ファイルを検査する（デフォルトは git 変更分のみ）")
    args = parser.parse_args()

    root = git_root(Path.cwd())
    use_full = args.full
    fallback = False

    if not use_full:
        candidates = changed_files(root)
        relevant = [p for p in candidates if p.name in ("package.json", "pyproject.toml") or is_dockerfile(p)]
        relevant = [p for p in relevant if "node_modules" not in p.parts]
        if not relevant:
            # diff で対象なし → full にフォールバック
            use_full = True
            fallback = True

    if use_full:
        candidates = all_target_files(root)
        relevant = [p for p in candidates if p.name in ("package.json", "pyproject.toml") or is_dockerfile(p)]
        relevant = [p for p in relevant if "node_modules" not in p.parts]

    diff_mode = not use_full
    findings = []
    manual = []

    mode_label = "full" if use_full else "diff"
    if fallback:
        mode_label += " (auto: no diff targets found)"
    print(f"Mode: {mode_label}")
    print(f"Scanning {len(relevant)} file(s)...")
    print()

    for path in relevant:
        if path.name == "package.json" and path.exists():
            findings.extend(check_package_json(root, path, diff_mode=diff_mode))
            if diff_mode:
                for section, name, version in added_node_packages(root, path):
                    manual.append(f"MANUAL Node registry review: {name} ({section}={version})")
        elif path.name == "pyproject.toml" and path.exists():
            findings.extend(check_pyproject(root, path, diff_mode=diff_mode))
            if diff_mode:
                for spec in added_python_packages(root, path):
                    manual.append(f"MANUAL PyPI review: {spec}")
        elif is_dockerfile(path) and path.exists():
            findings.extend(check_dockerfile(path))

    if not relevant:
        print("No supply-chain-relevant files found.")
        return 0

    if not findings and not manual:
        print("All checks passed.")
        return 0

    for line in findings:
        print(line)
    for line in sorted(set(manual)):
        print(line)

    print()
    print(f"Summary: {len(findings)} error(s), {len(set(manual))} manual review(s)")

    if findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
