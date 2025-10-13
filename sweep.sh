#!/usr/bin/env bash
set -Eeuo pipefail

# Kullanım:
#   ./sweep.sh
# Parametreleri istersen aşağıdaki dizilerden değiştir.

# Denenecek thread sayıları ve dizi boyutları
THREADS=(1 2 4 8)
SIZES=(5000000 10000000 20000000 100000000)   # 5M, 10M, 20M, 100M

# Ortak ayarlar
DUR=30        # logger süresi (s)
NTIMES=50     # STREAM tekrar sayısı
ROOT_DIR="$(pwd)"   # STREAM klasörü
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

echo ">>> Sweep başlıyor. Loglar: ${LOG_DIR}"
echo ">>> THREADS=${THREADS[*]}  SIZES=${SIZES[*]}  DUR=${DUR}s  NTIMES=${NTIMES}"

# Ortamı sabitlemek istersen (isteğe bağlı; sudo gerekir):
# sudo nvpmodel -m 0
# sudo jetson_clocks

for sz in "${SIZES[@]}"; do
  for th in "${THREADS[@]}"; do
    echo "------------------------------------------------------------"
    echo ">>> RUN  threads=${th}, size=${sz}, dur=${DUR}, ntimes=${NTIMES}"
    ./run_one.sh "${th}" "${sz}" "${DUR}" "${NTIMES}" || {
      echo "[WARN] Bu kombinasyonda hata: threads=${th}, size=${sz}"
      continue
    }
  done
done

echo ">>> Sweep tamamlandı."
echo "Örnek dosyalar:"
echo "  - ${LOG_DIR}/power_4thr_100000000.csv"
echo "  - ${LOG_DIR}/stream_4thr_100000000.txt"
