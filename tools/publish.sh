#!/bin/bash
# Build the stand-alone repo for one theme, so `omarchy theme install <url>` works.
#
#   tools/publish.sh <slug>          build or update ../omarchy-<slug>-theme and commit
#   tools/publish.sh <slug> --push   also create the public GitHub repo (first time) and push
#
# The mirror holds only themes/<slug>/ plus a short README and the licences.
# Extras (icons, screensaver hook, ultrawide wallpapers) stay in this collection.

set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
slug=${1:?usage: tools/publish.sh <slug> [--push]}
push=${2:-}
[[ $slug =~ ^[a-z0-9][a-z0-9-]*$ && -d $root/themes/$slug ]] || { echo "No theme $slug" >&2; exit 1; }

repo=omarchy-$slug-theme
mirror=${MIRROR_DIR:-$(dirname "$root")}/$repo
owner=$(gh api user -q .login 2>/dev/null || git -C "$root" config user.name)
title=$(sed -n 's/^# \(.*\) — .*/\1/p' "$root/themes/$slug/colors.toml" | head -1)
title=${title:-$slug}
summary=$(sed -n '2s/^# //p' "$root/themes/$slug/colors.toml")

python3 "$root/tools/check.py" "$root/themes/$slug"

mkdir -p "$mirror"
[[ -d $mirror/.git ]] || git -C "$mirror" init -q -b main
git -C "$mirror" config user.name "$(git -C "$root" config user.name)"
git -C "$mirror" config user.email "$(git -C "$root" config user.email)"

# Replace everything except .git with a fresh copy of the theme.
find "$mirror" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -r "$root/themes/$slug/." "$mirror/"
cp "$root/LICENSE" "$root/LICENSE-ART.md" "$mirror/"

cat >"$mirror/README.md" <<EOF
<div align="center">

<img src="preview.png" alt="$title theme preview" width="720">

# $title

#### $summary

</div>

A theme for [Omarchy](https://omarchy.org) 4.

## Install

Run this in a terminal:

\`\`\`bash
omarchy theme install https://github.com/$owner/$repo
\`\`\`

That sets the colours for every app, plus the wallpapers, lock screen and boot unlock logo.

## Get the full set

The matching icons, the screensaver art and the ultrawide wallpapers come from the
[omarchy-themes collection](https://github.com/$owner/omarchy-themes). Its installer adds them:

\`\`\`bash
git clone https://github.com/$owner/omarchy-themes
cd omarchy-themes
./install.sh $slug
\`\`\`

## Licence

Code: MIT. Artwork: CC BY 4.0. See \`LICENSE-ART.md\`.

This repository is generated from [omarchy-themes](https://github.com/$owner/omarchy-themes). Please send changes there.
EOF

source_rev=$(git -C "$root" rev-parse --short HEAD 2>/dev/null || echo uncommitted)
git -C "$mirror" add -A
if git -C "$mirror" diff --cached --quiet; then
  echo "$repo: no changes"
else
  git -C "$mirror" commit -q -m "Sync $slug from omarchy-themes $source_rev"
  echo "$repo: committed in $mirror"
fi

if [[ $push == --push ]]; then
  if gh repo view "$owner/$repo" >/dev/null 2>&1; then
    git -C "$mirror" push -q origin main
  else
    gh repo create "$owner/$repo" --public --source "$mirror" --push \
      --description "$title: $summary An Omarchy theme."
  fi
  echo "Pushed https://github.com/$owner/$repo"
fi
