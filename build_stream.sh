#!/usr/bin/env bash
set -Eeuo pipefail

# Kullanım: ./build_stream.sh [ARRAY_SIZE] [NTIMES]
# Örn: ./build_stream.sh 100000000 50

SIZE="${1:-10000000}"   # Varsayılan: 10 milyon eleman
NT="${2:-100}"          # Varsayılan: 100 iterasyon
OUT="stream.${SIZE}"

# Derle
gcc -O3 -fopenmp \
    -DSTREAM_ARRAY_SIZE="${SIZE}" \
    -DNTIMES="${NT}" \
    stream.c -o "${OUT}"

echo "[OK] Derlendi: ${OUT} (SIZE=${SIZE}, NTIMES=${NT})"
