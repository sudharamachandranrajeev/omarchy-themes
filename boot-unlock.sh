#!/bin/bash
# Animated boot unlock screen (the password screen you see before Omarchy
# starts) with your own text, drawn in the current theme's colours.
#
#   ./boot-unlock.sh [theme]             build it and install it (asks for your password)
#   ./boot-unlock.sh --preview [theme]   show it in a window for 15 seconds; changes nothing
#   ./boot-unlock.sh --restore           go back to Omarchy's own boot screen
#
# The look comes from [theme], else the current theme when it is from this
# collection, else Halloween Night. Change the text, font and your name with
# ./customise.sh (they are kept in ~/.config/omarchy-themes/settings.toml),
# then run this again.

set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
settings=${XDG_CONFIG_HOME:-$HOME/.config}/omarchy-themes/settings.toml
build=${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-themes/boot-unlock
name=omarchy-themes
dest=/usr/share/plymouth/themes/$name

say() { printf '\e[33m%s\e[0m\n' "$*"; }
die() { printf '\e[31m%s\e[0m\n' "$*" >&2; exit 1; }

command -v plymouth-set-default-theme >/dev/null || die "Plymouth is not installed, so there is no boot screen to change."

rebuild_boot_image() {
  say "Rebuilding the boot image. This takes a minute."
  if command -v limine-mkinitcpio >/dev/null; then
    sudo limine-mkinitcpio
  else
    sudo mkinitcpio -P
  fi
}

mode=install
case ${1:-} in
--preview | --restore) mode=${1#--}; shift ;;
esac

if [[ $mode == restore ]]; then
  sudo plymouth-set-default-theme omarchy
  sudo rm -rf "$dest"
  rebuild_boot_image
  say "Back to Omarchy's own boot screen. Pick a theme's logo with: omarchy plymouth switcher"
  exit 0
fi

if [[ -n ${1:-} ]]; then
  slug=$1
  [[ $slug =~ ^[a-z0-9][a-z0-9-]*$ && -f $here/plymouth/$slug.toml ]] || die "No boot screen for a theme called '$slug' in this collection."
else
  current=$(omarchy theme current 2>/dev/null || true)
  current=${current,,}
  slug=${current// /-}
  [[ $slug =~ ^[a-z0-9][a-z0-9-]*$ && -f $here/plymouth/$slug.toml ]] || slug=halloween-night
fi

rm -rf "$build"
text=$(python3 "$here/generators/boot_unlock.py" build "$slug" "$build")
say "Built the boot screen: \"$text\" in $slug colours."

if [[ $mode == preview ]]; then
  command -v bwrap >/dev/null || die "The preview needs bubblewrap: omarchy pkg add bubblewrap"
  [[ -n ${DISPLAY:-} ]] || die "The preview needs Xwayland (DISPLAY is not set)."
  preview=$(mktemp -d)
  trap 'rm -rf "$preview"' EXIT
  cp "$build"/* "$preview/"
  sed -i "s#$dest#/run/plymouth/themes/$name#" "$preview/$name.plymouth"
  say "Showing the boot screen in a window. The password box appears after 5 seconds; it closes itself."
  # plymouthd only runs as root, so it gets a private user namespace where it looks like root
  # but can change nothing, and draws into an X11 window instead of the screen.
  bwrap --unshare-user --uid 0 --gid 0 --dev-bind / / --tmpfs /run/plymouth \
    --bind "$preview" "/run/plymouth/themes/$name" /bin/bash -c '
      plymouthd --no-daemon --no-boot-log --kernel-command-line="splash plymouth.splash='"$name"'" 2>/dev/null &
      sleep 1
      plymouth --show-splash
      sleep 5
      plymouth ask-for-password --prompt=Password >/dev/null 2>&1 &
      sleep 10
      plymouth --quit
      wait'
  exit 0
fi

[[ -t 0 ]] || die "Run this in a terminal: it asks for your password to install the boot screen."
for file in "$build"/*; do
  [[ -f $file && ! -L $file ]] || die "Unexpected file in $build: $file"
done
say "Installing to $dest (needs your password)."
sudo rm -rf "$dest"
sudo install -d -o root -g root -m 755 "$dest"
sudo install -o root -g root -m 644 "$build"/* "$dest/"
sudo plymouth-set-default-theme "$name"
rebuild_boot_image
say "Done. You will see it the next time you start the computer."
say "To undo: ./boot-unlock.sh --restore"
