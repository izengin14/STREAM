#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p logs

# Kullanım: ./run_one.sh [THREADS] [ARRAY_SIZE] [DURATION] [NTIMES]
THREADS="${1:-4}"
SIZE="${2:-10000000}"
DUR="${3:-30}"
NTIMES="${4:-50}"

# 1) STREAM'i derle
./build_stream.sh "${SIZE}" "${NTIMES}"
BIN="stream.${SIZE}"

# 2) Logger'ı başlat (varsa)
LOGGER_PATH="$HOME/Desktop/current_reader/current_logger.py"
OUTCSV="logs/power_${THREADS}thr_${SIZE}.csv"
LOGGER_PID=""   # <-- ÖNEMLİ: boş olarak baştan tanımla

if [[ -f "${LOGGER_PATH}" ]]; then
  python3 "${LOGGER_PATH}" --dur "${DUR}" --out "${OUTCSV}" & LOGGER_PID=$!
  echo "[OK] Logger PID=${LOGGER_PID} -> ${OUTCSV}"
else
  echo "[WARN] ${LOGGER_PATH} bulunamadı; güç logu alınmayacak."
fi

# 3) Logger stabilizasyonu
sleep 1

# 4) STREAM'i çalıştır ve çıktıyı kaydet
export OMP_NUM_THREADS="${THREADS}"
STATS="logs/stream_${THREADS}thr_${SIZE}.txt"
"./${BIN}" | tee "${STATS}"

# 5) Logger’ı bekle (başladıysa)
if [[ -n "${LOGGER_PID:-}" ]]; then
  wait "${LOGGER_PID}"
fi

echo "[OK] Bitti: ${STATS} $( [[ -n "${LOGGER_PID:-}" ]] && echo "&& ${OUTCSV}" )"
