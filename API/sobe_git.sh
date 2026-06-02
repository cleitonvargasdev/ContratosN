#!/bin/sh
set -eu

if [ "$#" -lt 1 ]; then
    echo "Uso: ./sobe_git.sh \"mensagem do commit\"" >&2
    exit 1
fi

commit_message="$*"
current_branch=$(git rev-parse --abbrev-ref HEAD)

git add -A
git commit -m "$commit_message"
git push origin "$current_branch"