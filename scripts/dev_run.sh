#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADDON_ID="cat_menus"
BLENDER_BINARY="${BLENDER_BINARY:-/Applications/Blender.app/Contents/MacOS/Blender}"

if [[ ! -x "$BLENDER_BINARY" ]]; then
  echo "Blender 실행 파일을 찾을 수 없습니다: $BLENDER_BINARY" >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/blender_manifest.toml" ]]; then
  echo "저장소 루트에 blender_manifest.toml이 없습니다: $ROOT_DIR" >&2
  exit 1
fi

BLENDER_VERSION="$("$BLENDER_BINARY" --background --factory-startup --version | awk 'NR==1 {print $2}')"
PROFILE_DIR="${CATMENUS_BLENDER_PROFILE:-$HOME/Library/Application Support/Blender/CatMenusBlenderDev/$BLENDER_VERSION}"
EXTENSIONS_DIR="$PROFILE_DIR/extensions/user_default"
LINK_PATH="$EXTENSIONS_DIR/$ADDON_ID"

mkdir -p "$EXTENSIONS_DIR"

if [[ -L "$LINK_PATH" ]]; then
  CURRENT_TARGET="$(readlink "$LINK_PATH")"
  if [[ "$CURRENT_TARGET" != "$ROOT_DIR" ]]; then
    rm "$LINK_PATH"
    ln -s "$ROOT_DIR" "$LINK_PATH"
  fi
elif [[ -e "$LINK_PATH" ]]; then
  echo "Extension 링크 위치에 실제 파일 또는 폴더가 있습니다: $LINK_PATH" >&2
  exit 1
else
  ln -s "$ROOT_DIR" "$LINK_PATH"
fi

export BLENDER_USER_RESOURCES="$PROFILE_DIR"
export CATMENUS_SOURCE_DIR="$ROOT_DIR"
export CATMENUS_ADDON_ID="$ADDON_ID"

exec "$BLENDER_BINARY" --python-exit-code 1 --python "$ROOT_DIR/scripts/dev_bootstrap.py" "$@"
