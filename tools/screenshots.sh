#!/bin/bash
# Make the README images for one theme in docs/screenshots/<slug>/.
# Everything comes from the theme's own files, never from a screen capture.
#
#   tools/screenshots.sh <slug> [--boot-unlock]
#
# --boot-unlock also records boot-unlock.gif: it runs ./boot-unlock.sh --preview
# (with the theme's name as the text) and captures its window with grim, so it
# needs a Hyprland session. Keep the screen still while it records.

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

if [[ ${2:-} == "--boot-unlock" ]]; then
  tmp=$(mktemp -d)
  # Show an empty workspace first so the preview opens there with only the wallpaper behind it:
  # windows are slightly see-through, and nothing from the desktop may end up in the image.
  home_ws=$(hyprctl activeworkspace -j | jq .id)
  empty_ws=$(($(hyprctl workspaces -j | jq '[.[].id] | max') + 1))
  hyprctl dispatch "hl.dsp.focus({ workspace = \"$empty_ws\" })" >/dev/null
  XDG_CONFIG_HOME=$tmp/config XDG_STATE_HOME=$tmp/state "$root/boot-unlock.sh" --preview "$slug" >/dev/null &
  sleep 7 # the preview shows the password box after 6 seconds
  geometry=$(hyprctl clients -j | jq -r --argjson ws "$empty_ws" \
    '.[] | select(.class == "Plymouthd" and .workspace.id == $ws) | "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"' | head -1)
  [[ -n $geometry ]] || { hyprctl dispatch "hl.dsp.focus({ workspace = \"$home_ws\" })" >/dev/null; echo "No preview window on workspace $empty_ws" >&2; exit 1; }
  for i in $(seq -w 1 50); do grim -g "$geometry" "$tmp/frame-$i.png"; sleep 0.06; done
  hyprctl dispatch "hl.dsp.focus({ workspace = \"$home_ws\" })" >/dev/null
  wait
  magick -delay 8 -loop 0 "$tmp"/frame-*.png -gravity center -crop 72%x56%+0+40 +repage \
    -resize 900x -layers Optimize "$out/boot-unlock.gif"
  rm -rf "$tmp"
fi

ls -la "$out"
