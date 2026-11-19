#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 path/to/trans_ru.qm output/KoboRoot.tgz" >&2
    exit 2
fi
repo=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

qm=usr/local/Kobo/translations/trans_ru.qm
fonts=usr/local/Trolltech/QtEmbedded-4.6.2-arm/lib/fonts
install -Dm644 "$1" "$stage/$qm"
mkdir -p "$stage/$fonts"
install -m644 "$repo"/patch/fonts/{Avenir,Avenir-Bold,Avenir-Italic,Avenir-BoldItalic,georgia,georgiab,georgiai,georgiaz}.ttf "$stage/$fonts/"

# Only package the payload files, not parent directories on the device.
(cd "$stage" && tar --owner=0 --group=0 --mtime=@0 -czf - "./$qm" "./$fonts/"*.ttf) > "$2"
