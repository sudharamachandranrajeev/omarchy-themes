#!/bin/bash
# Make the README images for one theme in docs/screenshots/<slug>/.
# Everything comes from the theme's own files, never from a screen capture.
#
#   tools/screenshots.sh <slug>

set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
slug=${1:?usage: tools/screenshots.sh <slug>}
theme=$root/themes/$slug
out=$root/docs/screenshots/$slug
[[ -d $theme ]] || { echo "No theme $slug" >&2; exit 1; }
mkdir -p "$out"

bg=$(sed -n 's/^background = "\(#[0-9a-fA-F]*\)"/\1/p' "$theme/colors.toml")
accent=$(sed -n 's/^accent = "\(#[0-9a-fA-F]*\)"/\1/p' "$theme/colors.toml")

magick "$theme/preview.png" -resize 1200x -quality 82 "$out/hero.jpg"
magick "$theme/preview-unlock.png" -gravity center -crop 1200x500+0+0 +repage -resize 900x -quality 85 "$out/unlock.jpg"

for img in "$theme"/backgrounds/*.png; do
  magick "$img" -resize 640x -quality 80 "$out/wall-$(basename "${img%.png}").jpg"
done

if [[ -f $theme/screensaver.txt ]]; then
  font=$(fc-match -f '%{file}' 'JetBrainsMono Nerd Font')
  magick -background "$bg" -fill "$accent" -font "$font" -pointsize 14 \
    label:@"$theme/screensaver.txt" -bordercolor "$bg" -border 40 -quality 85 "$out/screensaver.jpg"
fi

for overlay in "$root"/icons/"$slug"/*/; do
  [[ -d $overlay ]] || continue
  tmp=$(mktemp -d)
  for svg in "$overlay"scalable/*/*.svg; do
    case $(basename "$svg") in folder-open.svg | org.gnome.Terminal.svg) continue ;; esac # duplicates
    rsvg-convert -w 96 "$svg" -o "$tmp/$(basename "${svg%.svg}").png"
  done
  magick montage "$tmp"/*.png -tile 8x -geometry 96x96+12+12 -background "$bg" "$out/icons.png"
  rm -rf "$tmp"
done

ls -la "$out"
