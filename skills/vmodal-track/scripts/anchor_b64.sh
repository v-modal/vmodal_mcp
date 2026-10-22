#!/usr/bin/env bash
help='
  Crop a subject out of a frame and print it as a small base64 JPEG, for
  search_video(image_query=...). The VModal API expects plain base64 image bytes
  (a URL is rejected with "cannot decode image_query base64").
  Output is ~3-4 KB of base64 (112 px wide, JPEG quality 40), small enough to pass in a tool call.
  Needs sips (macOS) or ImageMagick (magick/convert).

  anchor_b64.sh <frame.png> [x y w h]                  # default: img_b64
  anchor_b64.sh img_b64 /tmp/vmodal-find/city/a.png 225 190 210 160
  anchor_b64.sh img_b64 /tmp/vmodal-find/city/a.png     # whole frame
'

img_b64() {
  local help='
    ## Usage:
      anchor_b64.sh img_b64 /tmp/vmodal-find/city/a.png 225 190 210 160
  '
  local src="$1" x="${2:-}" y="${3:-}" w="${4:-}" h="${5:-}" tmp
  [[ -f "$src" ]] || { echo "missing file: $src" >&2; return 1; }
  tmp=$(mktemp -d)
  if command -v sips >/dev/null; then
    cp "$src" "$tmp/in.png"
    [[ -n "$h" ]] && sips -c "$h" "$w" --cropOffset "$y" "$x" "$tmp/in.png" --out "$tmp/in.png" >/dev/null
    sips -s format jpeg -s formatOptions 40 --resampleWidth 112 "$tmp/in.png" --out "$tmp/out.jpg" >/dev/null
  else
    local im; im=$(command -v magick || command -v convert) || { echo "need sips or ImageMagick" >&2; return 1; }
    local crop=(); [[ -n "$h" ]] && crop=(-crop "${w}x${h}+${x}+${y}" +repage)
    "$im" "$src" "${crop[@]}" -resize 112x -quality 40 "$tmp/out.jpg"
  fi
  base64 < "$tmp/out.jpg" | tr -d '\n'
  echo
  rm -rf "$tmp"
}

case "${1:-}" in
  ""|-h|--help|help) echo "$help" ;;
  img_b64) shift; img_b64 "$@" ;;
  *) img_b64 "$@" ;;
esac
