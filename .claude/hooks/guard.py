#!/usr/bin/env python3
"""PreToolUse guard dla Claude Code – egzekwuje CONTRIBUTING januszex-ai.

Exit 0 = przepuść, exit 2 = zablokuj (stderr trafia do Claude jako powód).
Tylko biblioteka standardowa.
"""
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "master"}
BRANCH_RE = re.compile(r"^[A-Za-z]?\d+/(feature|fix|chore|docs)/[a-z0-9]+(-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^([A-Z]\d{3} - )?(feat|fix|docs|chore|test|refactor|ci|style)(\([a-z0-9-]+\))?!?: \S.*")
SECRET_FILE_RE = re.compile(r"(^|/)\.env(\.(?!example$)[^/]+)?$")
SEPARATORS = {"&&", "||", ";", "|", "&", ";;", "(", ")"}


def block(msg: str) -> None:
    print(f"[guard] ZABLOKOWANO: {msg}", file=sys.stderr)
    sys.exit(2)


def git(cwd: str, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def segments(command: str):
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        tokens = command.split()
    seg = []
    for tok in tokens:
        if tok in SEPARATORS:
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def opt_value(args, *names):
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                return args[i + 1]
            if n.startswith("--") and a.startswith(n + "="):
                return a.split("=", 1)[1]
            if not n.startswith("--") and a.startswith(n) and len(a) > len(n):
                return a[len(n):]
    return None


def check_git(args, cwd):
    # pomiń globalne opcje git typu -C <dir>
    while args and args[0].startswith("-"):
        if args[0] in ("-C", "-c") and len(args) > 1:
            if args[0] == "-C":
                cwd = os.path.join(cwd, args[1])
            args = args[2:]
        else:
            args = args[1:]
    if not args:
        return
    sub, rest = args[0], args[1:]
    branch = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")

    if "--no-verify" in rest or (sub == "commit" and "-n" in rest):
        block("--no-verify jest zabronione.")

    if sub in ("checkout", "switch", "branch"):
        new = opt_value(rest, "-b", "-B", "-c", "-C", "--create")
        if sub == "branch" and new is None:
            plain = [a for a in rest if not a.startswith("-")]
            if len(plain) == 1 and not any(a in rest for a in ("-d", "-D", "--delete", "-m", "-M")):
                new = plain[0]
        if new and not BRANCH_RE.match(new):
            block(f"nazwa brancha '{new}' niezgodna z <P><NNN>/<feature|fix|chore|docs>/<opis-kebab>, "
                  "np. B012/feature/user-registration.")

    if sub == "commit":
        if branch in PROTECTED:
            block(f"commit na '{branch}' – utwórz branch dla issue.")
        if "--amend" not in rest:
            msg = opt_value(rest, "-m", "--message")
            if msg is None:
                block("używaj git commit -m \"<typ>: <opis>\".")
            first = msg.strip().splitlines()[0] if msg.strip() else ""
            if not COMMIT_RE.match(first):
                block(f"commit '{first}' niezgodny z Conventional Commits "
                      "(feat|fix|docs|chore|test|refactor|ci|style): <opis w trybie rozkazującym>. "
                      "Podaj temat wprost w -m (bez heredoc/$(...)); treść w drugim -m.")
        staged = git(cwd, "diff", "--cached", "--name-only").splitlines()
        if "-a" in rest or "--all" in rest:
            staged += git(cwd, "diff", "--name-only").splitlines()
        leaked = [f for f in staged if SECRET_FILE_RE.search(f)]
        if leaked:
            block(f"w commicie są pliki z sekretami: {', '.join(leaked)}.")

    if sub == "add":
        if any(SECRET_FILE_RE.search(a) for a in rest):
            block("nie dodawaj plików .env do repo.")
        if any(a in ("-A", "--all", ".", "-u") for a in rest):
            block("dodawaj pliki jawnie (git add <ścieżki>), nie -A / . / -u.")

    if sub == "push":
        if any(a in ("-f", "--force", "--force-with-lease", "--mirror", "--delete", "-d") or a.startswith("--force")
               or a.startswith("+") for a in rest):
            block("force push / usuwanie zdalnych branchy jest zabronione.")
        targets = [a.split(":")[-1] for a in rest if not a.startswith("-")][1:]
        if branch in PROTECTED or any(t.replace("refs/heads/", "") in PROTECTED for t in targets):
            block("push na main jest zabroniony – tylko przez PR.")
        if branch and branch != "HEAD" and not BRANCH_RE.match(branch):
            block(f"branch '{branch}' ma niepoprawną nazwę – zmień ją przed pushem (git branch -m).")

    if sub == "reset" and "--hard" in rest:
        block("git reset --hard – zapytaj użytkownika.")
    if sub == "clean" and any(a.startswith("-") and "f" in a for a in rest):
        block("git clean -f – zapytaj użytkownika.")


def check_gh(args, cwd):
    if len(args) < 2:
        return
    area, action, rest = args[0], args[1], args[2:]

    if area == "pr" and action == "create":
        title = opt_value(rest, "-t", "--title")
        if not title or not re.match(r"^[A-Z]\d{3} - ", title) or not COMMIT_RE.match(title):
            block("tytuł PR: \"<ID> - <typ>: <opis>\", np. --title \"B012 - feat: add report endpoint\".")
        body = opt_value(rest, "-b", "--body")
        body_file = opt_value(rest, "-F", "--body-file")
        if body_file:
            try:
                with open(os.path.join(cwd, body_file), encoding="utf-8") as fh:
                    body = fh.read()
            except OSError:
                block(f"nie mogę odczytać {body_file}.")
        if not body or not re.search(r"(?i)\b(closes|fixes|resolves) #\d+", body):
            block("opis PR musi być wypełnionym szablonem i zawierać 'Closes #<numer>'.")
        for section in ("## Description of changes", "## How to test", "## Pre-merge checklist"):
            if section not in body:
                block(f"w opisie PR brakuje sekcji szablonu: {section}.")
        base = opt_value(rest, "-B", "--base")
        if base and base not in PROTECTED:
            block("PR-y kierujemy do main (bez stacked PR).")

    if area == "pr" and action == "merge":
        if "--admin" in rest:
            block("merge z --admin (obejście branch protection) jest zabroniony.")
        if "--squash" not in rest and "-s" not in rest:
            block("mergujemy wyłącznie metodą --squash.")

    if area == "pr" and action == "review" and any(a in ("--approve", "-a") for a in rest):
        block("Claude nie zatwierdza PR-ów – approve daje człowiek.")

    if area == "issue" and action in ("close", "delete", "transfer", "lock"):
        block(f"gh issue {action} – issues zamyka merge PR-a z 'Closes #N'.")

    if area == "issue" and action == "edit":
        who = opt_value(rest, "--add-assignee")
        if who and who != "@me":
            block("przypisuj issues tylko do siebie (@me).")

    if area == "repo" and action in ("delete", "edit", "rename", "archive"):
        block(f"gh repo {action} jest zabronione.")

    if area == "api" and any(re.search(r"/(protection|rulesets|collaborators|hooks)", a) for a in rest):
        block("zmiany ustawień repo przez gh api są zabronione.")


def check_bash(command: str, cwd: str):
    for seg in segments(command):
        # zdejmij prefiksy typu VAR=1, sudo, env
        while seg and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0]) or seg[0] in ("sudo", "env", "command")):
            seg = seg[1:]
        if not seg:
            continue
        prog = os.path.basename(seg[0])
        if prog == "git":
            check_git(seg[1:], cwd)
        elif prog == "gh":
            check_gh(seg[1:], cwd)
        elif prog == "docker" and "compose" in seg and "down" in seg and any(a in ("-v", "--volumes") for a in seg):
            block("docker compose down -v kasuje bazę – zapytaj użytkownika.")
        elif prog in ("cat", "less", "more", "head", "tail", "grep", "source", ".") and \
                any(SECRET_FILE_RE.search(a) for a in seg[1:]):
            block("nie czytaj plików .env – użyj .env.example.")


def check_file(path: str):
    if path and SECRET_FILE_RE.search(path.replace("\\", "/")):
        block("operacje na .env są zabronione – zmieniaj .env.example.")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or os.getcwd()

    if tool == "Bash":
        check_bash(inp.get("command", ""), cwd)
    elif tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        check_file(inp.get("file_path") or inp.get("notebook_path") or "")
    sys.exit(0)


if __name__ == "__main__":
    main()