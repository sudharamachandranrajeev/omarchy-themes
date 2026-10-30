#!/bin/bash
# Install or remove themes from the omarchy-themes collection.
#
#   ./install.sh                     pick themes from a list
#   ./install.sh hallowed-night      install one or more themes by name
#   ./install.sh --remove hallowed-night
#
# Installing a theme from here (rather than `omarchy theme install <url>`)
# also installs its extras: the matching icon theme, the screensaver-art hook,
# and ultrawide wallpapers when a monitor is wider than 21:9.

set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
themes_dir=$HOME/.config/omarchy/themes
icons_dir=$HOME/.local/share/icons
backup_dir=$HOME/.local/state/omarchy-themes/backup
marker=.omarchy-themes
hook=omarchy-themes-screensaver

say() { printf '\e[33m%s\e[0m\n' "$*"; }
die() { printf '\e[31m%s\e[0m\n' "$*" >&2; exit 1; }

command -v omarchy >/dev/null || die "This needs Omarchy (https://omarchy.org)."

available() {
  local d
  for d in "$here"/themes/*/; do basename "$d"; done
}

valid_slug() {
  [[ $1 =~ ^[a-z0-9][a-z0-9-]*$ && -d $here/themes/$1 ]] || die "No theme called '$1'. Choose from: $(available | tr '\n' ' ')"
}

# The overlay icon theme a collection theme ships, if any (icons/<slug>/<Name>/index.theme).
overlay_icons() {
  local index
  for index in "$here"/icons/"$1"/*/index.theme; do
    [[ -f $index ]] && basename "$(dirname "$index")"
  done
  return 0
}

is_ultrawide() {
  command -v hyprctl >/dev/null || return 1
  hyprctl monitors -j 2>/dev/null | jq -e 'any(.[]; (.width / .height) > 2.2)' >/dev/null 2>&1
}

install_theme() {
  local slug=$1 dest=$themes_dir/$1 name
  valid_slug "$slug"

  if [[ -e $dest ]]; then
    mkdir -p "$backup_dir"
    mv "$dest" "$backup_dir/$slug-$(date +%Y%m%d-%H%M%S)"
    say "Moved your existing $slug theme to $backup_dir"
  fi
  mkdir -p "$themes_dir"
  cp -r "$here/themes/$slug" "$dest"
  touch "$dest/$marker"

  # Switch to the overlay icons only once they are really installed: Omarchy
  # passes icons.theme straight to GTK, and a missing name breaks every icon.
  for name in $(overlay_icons "$slug"); do
    mkdir -p "$icons_dir"
    rm -rf "${icons_dir:?}/$name"
    cp -r "$here/icons/$slug/$name" "$icons_dir/$name"
    if command -v gtk-update-icon-cache >/dev/null; then
      gtk-update-icon-cache -q -f -t "$icons_dir/$name" || true
    fi
    [[ -f $icons_dir/$name/index.theme ]] && echo "$name" >"$dest/icons.theme"
  done

  if [[ -d $here/wallpapers/$slug/ultrawide ]] && is_ultrawide; then
    mkdir -p "$HOME/.config/omarchy/backgrounds/$slug"
    cp "$here/wallpapers/$slug/ultrawide/"* "$HOME/.config/omarchy/backgrounds/$slug/"
    say "Added ultrawide wallpapers for your wide monitor."
  fi

  if [[ -f $dest/screensaver.txt ]]; then
    omarchy-hook-install theme-set "$here/hooks/$hook" >/dev/null
  fi

  say "Installed $slug."
}

remove_theme() {
  local slug=$1 dest=$themes_dir/$1 name
  [[ $slug =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "Not a theme name: $slug"
  [[ -f $dest/$marker ]] || die "$slug was not installed from this collection; leaving it alone."

  local current
  current=$(omarchy theme current 2>/dev/null || true)
  current=${current,,}
  if [[ ${current// /-} == "$slug" ]]; then
    die "$slug is your current theme. Switch to another theme first, then remove it."
  fi

  rm -rf "$dest"
  for name in $(overlay_icons "$slug"); do
    rm -rf "${icons_dir:?}/$name"
  done

  # Drop the hook once no collection theme is left; it restores the user's art on the next switch.
  if ! compgen -G "$themes_dir/*/$marker" >/dev/null; then
    rm -f "$HOME/.config/omarchy/hooks/theme-set.d/$hook"
  fi
  say "Removed $slug."
}

if [[ ${1:-} == "--remove" ]]; then
  shift
  (($#)) || die "Usage: ./install.sh --remove <theme>..."
  for slug in "$@"; do remove_theme "$slug"; done
  exit 0
fi

if (($# == 0)); then
  command -v gum >/dev/null || die "Usage: ./install.sh <theme>...  Themes: $(available | tr '\n' ' ')"
  mapfile -t picked < <(available | gum choose --no-limit --header "Pick themes to install (space selects, enter confirms)")
  ((${#picked[@]})) || exit 0
  set -- "${picked[@]}"
fi

for slug in "$@"; do install_theme "$slug"; done

if (($# == 1)); then
  if [[ -t 0 ]] && command -v gum >/dev/null && gum confirm "Switch to $1 now?"; then
    omarchy theme set "$1"
  else
    say "Switch with: omarchy theme set $1"
  fi
fi
say "Optional: an animated boot unlock screen with your own text: ./boot-unlock.sh --preview"
