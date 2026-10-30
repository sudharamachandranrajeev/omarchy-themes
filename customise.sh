#!/bin/bash
# Theme customiser: one menu for the whole collection. Switch or remove
# themes, change a theme's accent colour, and set up the animated boot screen
# (text, font, your name, preview, install).
#
#   ./customise.sh              open the menu
#   ./customise.sh --add-menu   add "Theme Customiser" under Style in the Omarchy menu

set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
themes_dir=$HOME/.config/omarchy/themes
menu_file=$HOME/.config/omarchy/extensions/omarchy-menu.jsonc
marker=.omarchy-themes

say() { printf '\e[33m%s\e[0m\n' "$*"; }
die() { printf '\e[31m%s\e[0m\n' "$*" >&2; exit 1; }
boot() { python3 "$here/generators/boot_unlock.py" "$@"; }
pause() { gum input --placeholder "Press Enter to go back" >/dev/null || true; }

command -v omarchy >/dev/null || die "This needs Omarchy (https://omarchy.org)."

add_menu() {
  # The menu file is JSONC that Omarchy reloads on save. Replace our row if it is there, else add it last.
  python3 - "$menu_file" "omarchy-launch-floating-terminal-with-presentation $(printf %q "$here/customise.sh")" <<'EOF'
import json, os, sys
path, action = sys.argv[1], sys.argv[2]
row = ('  "style.omarchy-themes": {"icon":"󰏘","label":"Theme Customiser",'
       '"description":"omarchy-themes: accent colour, boot screen text and font",'
       f'"action":{json.dumps(action)}}},')
text = open(path).read() if os.path.exists(path) else "{\n}\n"
lines = [l for l in text.splitlines() if '"style.omarchy-themes"' not in l]
end = max(i for i, l in enumerate(lines) if l.strip() == "}")
lines.insert(end, row)
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path, "w").write("\n".join(lines) + "\n")
EOF
  say "Added Theme Customiser to the Omarchy menu: Super + Space, then Style."
}

if [[ ${1:-} == "--add-menu" ]]; then
  add_menu
  exit 0
fi

command -v gum >/dev/null || die "The customiser needs gum, which comes with Omarchy."

title() { sed -n '1s/^# \(.*\) — .*/\1/p' "$here/themes/$1/colors.toml"; }

current_slug() {
  local current
  current=$(omarchy theme current 2>/dev/null || true)
  current=${current,,}
  echo "${current// /-}"
}

collection() {
  local d
  for d in "$here"/themes/*/; do basename "$d"; done
}

installed() { [[ -f $themes_dir/$1/$marker ]]; }

# Show "Title (slug)" rows and give back the slug that was picked.
pick_theme() {
  local header=$1 slug label rows=()
  shift
  for slug in "$@"; do
    label="$(title "$slug") ($slug)"
    installed "$slug" && label+="  · installed"
    [[ $slug == "$(current_slug)" ]] && label+="  · current"
    rows+=("$label")
  done
  ((${#rows[@]})) || return 1
  label=$(gum choose --header "$header" "${rows[@]}") || return 1
  label=${label%%)*}
  echo "${label##*(}"
}

switch_theme() {
  local slug slugs
  mapfile -t slugs < <(collection)
  slug=$(pick_theme "Switch to which theme?" "${slugs[@]}") || return 0
  if installed "$slug"; then
    omarchy theme set "$slug"
  else
    "$here/install.sh" "$slug"
  fi
}

remove_theme() {
  local slug slugs=()
  while read -r slug; do
    installed "$slug" && [[ $slug != "$(current_slug)" ]] && slugs+=("$slug")
  done < <(collection)
  if ((${#slugs[@]} == 0)); then
    say "Nothing to remove: the only installed collection theme is the one you are using."
    pause
    return 0
  fi
  slug=$(pick_theme "Remove which theme?" "${slugs[@]}") || return 0
  gum confirm "Remove $(title "$slug")?" && "$here/install.sh" --remove "$slug"
}

accent() {
  local slug file colour name names
  slug=$(current_slug)
  file=$themes_dir/$slug/colors.toml
  if [[ ! -d $here/themes/$slug ]] || ! installed "$slug"; then
    say "The current theme is not from this collection. Switch to one first."
    pause
    return 0
  fi
  colour=$(sed -n 's/^accent = "\(#[0-9a-fA-F]*\)"/\1/p' "$file")
  names=(orange yellow green cyan blue magenta red "Type a colour" "Reset to the theme's own")
  name=$(gum choose --header "Accent colour for $(title "$slug") (now $colour)" "${names[@]}") || return 0
  case $name in
  "Type a colour") colour=$(gum input --placeholder "#rrggbb" --value "$colour") || return 0 ;;
  "Reset to the theme's own") colour=$(sed -n 's/^accent = "\(#[0-9a-fA-F]*\)"/\1/p' "$here/themes/$slug/colors.toml") ;;
  *) colour=$(sed -n "s/^$name = \"\(#[0-9a-fA-F]*\)\"/\1/p" "$file") ;;
  esac
  [[ $colour =~ ^#[0-9a-fA-F]{6}$ ]] || { say "That is not a #rrggbb colour."; pause; return 0; }

  cp "$file" "$file.before-accent"
  sed -i "s/^accent = \".*\"/accent = \"$colour\"/" "$file"
  if ! python3 "$here/tools/contrast.py" "$file" >/tmp/omarchy-themes-contrast.$$; then
    mv "$file.before-accent" "$file"
    say "Not changed: $colour is hard to read against this theme's background."
    grep '^FAIL' /tmp/omarchy-themes-contrast.$$ | grep accent || true
    rm -f /tmp/omarchy-themes-contrast.$$
    pause
    return 0
  fi
  rm -f "$file.before-accent" /tmp/omarchy-themes-contrast.$$
  omarchy theme set "$slug"
  say "Accent is now $colour. Reinstalling the theme with ./install.sh puts the original back."
  pause
}

font_menu() {
  local slug=$1 family style choice
  choice=$(gum choose --header "Font for the boot screen" \
    "Omarchy font ($(omarchy font current))" "C059 (classic serif)" "Pick any installed font") || return 0
  case $choice in
  Omarchy*) family=omarchy ;;
  C059*) family=C059 ;;
  *) family=$(fc-list : family | cut -d, -f1 | sort -u | gum filter --placeholder "Type to search fonts") || return 0 ;;
  esac
  style=$(gum choose --header "Weight" Bold Regular) || return 0
  boot set "$slug" font "$family:${style,,}"
}

boot_menu() {
  local slug choice value
  slug=$(current_slug)
  [[ -f $here/plymouth/$slug.toml ]] || slug=halloween-night
  while true; do
    choice=$(gum choose --header "Boot screen: \"$(boot show "$slug")\" in $(title "$slug") style" \
      "Text: $(boot get "$slug" text)" \
      "Font: $(boot get "$slug" font)" \
      "Your name: $(boot get-name)" \
      "Style: $(title "$slug")" \
      "Preview (opens a window, changes nothing)" \
      "Install (asks for your password)" \
      "Go back to Omarchy's boot screen" \
      "Back") || return 0
    case $choice in
    Text:*)
      say "Use {NAME} for your name in capitals, {name} as typed. Up to 32 characters in all."
      value=$(gum input --value "$(boot get "$slug" text)" --char-limit 40) || continue
      boot set "$slug" text "$value" || pause
      ;;
    Font:*) font_menu "$slug" || pause ;;
    "Your name:"*)
      value=$(gum input --value "$(boot get-name)" --char-limit 20) || continue
      boot set-name "$value" || pause
      ;;
    Style:*)
      local slugs=() f
      for f in "$here"/plymouth/*.toml; do slugs+=("$(basename "${f%.toml}")"); done
      slug=$(pick_theme "Which theme's boot screen?" "${slugs[@]}") || slug=$(current_slug)
      [[ -f $here/plymouth/$slug.toml ]] || slug=halloween-night
      ;;
    Preview*) "$here/boot-unlock.sh" --preview "$slug" || pause ;;
    Install*) "$here/boot-unlock.sh" "$slug" || true; pause ;;
    "Go back"*) "$here/boot-unlock.sh" --restore || true; pause ;;
    Back) return 0 ;;
    esac
  done
}

while true; do
  clear
  gum style --border rounded --padding "0 2" --border-foreground 212 \
    "Theme Customiser" "Current theme: $(omarchy theme current 2>/dev/null || echo unknown)"
  choice=$(gum choose "Switch theme" "Accent colour" "Boot screen" "Remove a theme" \
    "Add to the Omarchy menu" "Quit") || exit 0
  case $choice in
  "Switch theme") switch_theme ;;
  "Accent colour") accent ;;
  "Boot screen") boot_menu ;;
  "Remove a theme") remove_theme ;;
  "Add to the Omarchy menu") add_menu; pause ;;
  Quit) exit 0 ;;
  esac
done
