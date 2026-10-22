#!/usr/bin/env bash
help='
  Build one contact sheet (3 columns, 320x180 tiles, left to right then top to bottom)
  from the frames of one event, so a whole timeline is one image to view.
  Pass frames in time order. Pass "-" for a missing second: its tile stays black.
  At most 12 frames. Prints "TILE <n> <input>" per tile (n from 1), then the sheet path.
  Inputs are converted with ../../vmodal-find/scripts/frames_to_png.sh (same path rules:
  relative paths resolve against $VMODAL_MCP_CWD, the current dir, then $HOME).
  If ffmpeg is missing, prints "NO_SHEET" and one PNG path per frame instead.

  frames_strip.sh <out.png> <frame|->...                     # default: strip_sheet
  frames_strip.sh strip_sheet /tmp/vmodal-incident/5m20.png ztmp/vmodal/x/dashcam_v1/a.webp - ztmp/.../b.webp
'

dir_skill="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
to_png="$dir_skill/../vmodal-find/scripts/frames_to_png.sh"
tile_w=320
tile_h=180
cols=3

strip_sheet() {
  local help='
    ## Usage:
      frames_strip.sh strip_sheet /tmp/vmodal-incident/5m20.png a.webp b.webp - c.webp
  '
  local out="$1" tmp p png i=0 n_real=0 args=() pos=() filter=""
  shift
  (( $# >= 1 && $# <= 12 )) || { echo "need 1 to 12 frames" >&2; return 1; }
  mkdir -p "$(dirname "$out")"
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/vmodal-strip.XXXXXX")

  local pngs=()
  for p in "$@"; do
    if [[ "$p" == "-" ]]; then
      pngs+=("-")
    else
      png=$(bash "$to_png" imgs_to_png "$tmp" "$p" | tail -n 1)
      if [[ "$png" == FAIL* ]]; then pngs+=("-"); p="$p (FAIL)"; else pngs+=("$png"); fi
    fi
    echo "TILE ${#pngs[@]} $p"
  done

  if ! command -v ffmpeg >/dev/null; then
    echo "NO_SHEET"
    for png in "${pngs[@]}"; do [[ "$png" != "-" ]] && echo "$png"; done
    return 0
  fi

  for png in "${pngs[@]}"; do
    if [[ "$png" != "-" ]]; then
      args+=(-i "$png")
      pos+=("$(( (i % cols) * tile_w )):$(( (i / cols) * tile_h ))")
    fi
    i=$((i + 1))
  done
  n_real=${#pos[@]}
  (( n_real >= 1 )) || { echo "no frame could be converted" >&2; return 1; }

  # Black canvas the size of the grid; each tile is scaled and overlaid at its slot,
  # so a "-" gap or a short last row stays black.
  local rows=$(( (i + cols - 1) / cols )) prev="bg" k
  args+=(-f lavfi -i "color=c=black:s=$((cols * tile_w))x$((rows * tile_h))")
  filter="[$n_real:v]null[bg]"
  for ((k = 0; k < n_real; k++)); do
    filter+=";[$k:v]scale=${tile_w}:${tile_h}[t$k];[$prev][t$k]overlay=${pos[$k]}[o$k]"
    prev="o$k"
  done
  ffmpeg -loglevel error -y "${args[@]}" -filter_complex "$filter" -map "[$prev]" -frames:v 1 "$out" || return 1
  rm -rf "$tmp"
  echo "$out"
}

case "${1:-}" in
  ""|-h|--help|help) echo "$help" ;;
  strip_sheet) "$@" ;;
  *) strip_sheet "$@" ;;
esac
