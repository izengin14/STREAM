#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p logs

export OMP_NUM_THREADS=4

# Güç logger'ı başlat
python3 ~/Desktop/current_reader/current_logger.py --dur 60 --out logs/power_memkernels.csv & 
LOGGER_PID=$!

# Kernel programını çalıştır, MARK logunu yaz
./memkernels | tee logs/memkernels_marks.txt

# Logger bitene kadar bekle
wait $LOGGER_PID

echo "[OK] Çalışma tamamlandı -> logs/power_memkernels.csv ve logs/memkernels_marks.txt"
