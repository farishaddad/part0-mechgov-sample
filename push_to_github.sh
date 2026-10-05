#!/usr/bin/env bash
# Create a git repo for the Part 0 sample and push it to GitHub.
# Usage:  ./push_to_github.sh                 (private repo, default name)
#         REPO_NAME=my-name ./push_to_github.sh
#         VISIBILITY=public ./push_to_github.sh   (only after open-source approval)
set -euo pipefail

cd "$(dirname "$0")"
REPO_NAME="${REPO_NAME:-part0-mechgov-sample}"
VISIBILITY="${VISIBILITY:-private}"

command -v git >/dev/null || { echo "git not found. Install Xcode command line tools: xcode-select --install"; exit 1; }
command -v gh  >/dev/null || { echo "GitHub CLI not found. Install with: brew install gh"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Not signed in to GitHub. Run: gh auth login"; exit 1; }

case "$VISIBILITY" in private|public|internal) ;; *) echo "VISIBILITY must be private, public or internal"; exit 1;; esac

# Basic safety check: no real AWS account IDs or keys in the files being committed
if grep -rEn --exclude-dir=.git --exclude=push_to_github.sh 'AKIA[0-9A-Z]{16}|aws_secret_access_key' . ; then
  echo "Possible credentials found above. Remove them before pushing."; exit 1
fi
if grep -rEho --exclude-dir=.git --exclude=push_to_github.sh '\b[0-9]{12}\b' . | grep -v '^123456789012$' | sort -u | grep -q . ; then
  echo "Warning: 12-digit numbers other than the 123456789012 placeholder were found:"
  grep -rEn --exclude-dir=.git --exclude=push_to_github.sh '\b[0-9]{12}\b' . | grep -v 123456789012 || true
  read -r -p "Continue anyway? [y/N] " ans; [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

if [ "$(git rev-parse --show-toplevel 2>/dev/null || true)" != "$(pwd)" ]; then
  git init -b main
fi

git add -A
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "Part 0 sample: hard gates, entropy commit-reveal on S3 Object Lock, AgentCore Policy (Cedar)"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote 'origin' already set: $(git remote get-url origin)"
  git push -u origin main
else
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push \
    --description "Mechanical enforcement around an LLM decision: deterministic gates, S3 Object Lock commit-reveal, AgentCore Policy (Cedar). Companion to the AWS Builder Center article."
fi

echo
echo "Done: $(gh repo view --json url -q .url)"
