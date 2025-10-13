import pandas as pd
import matplotlib.pyplot as plt
import re

# Dosyaları oku
pwr = pd.read_csv("logs/power_memkernels.csv")
marks = []
with open("logs/memkernels_marks.txt") as f:
    for line in f:
        m = re.search(r'\[MARK\]\s+(\w+)', line)
        if m:
            marks.append(m.group(1))

# Zamanı relative saniyeye dönüştür
t0 = pwr['ts_sec'].iloc[0]
pwr['rel_s'] = pwr['ts_sec'] - t0

# Kaç mark varsa, eşit aralıklarla paylaştır
step = len(pwr) // (len(marks)+1)
marks_rel = [(i*step/pwr.shape[0]*pwr['rel_s'].max(), label) for i,label in enumerate(marks, start=1)]

# Grafik çiz
plt.figure(figsize=(12,5))
plt.plot(pwr['rel_s'], pwr['current_mA'], label="DRAM current (mA)")
for ts,label in marks_rel:
    plt.axvline(ts, color="red", linestyle="--")
    plt.text(ts, pwr['current_mA'].max()*0.9, label, rotation=90, va='top')
plt.xlabel("Time (s)")
plt.ylabel("Current (mA)")
plt.title("memkernels: COPY / SCALE / ADD / TRIAD fingerprinting")
plt.legend()
plt.tight_layout()
plt.savefig("logs/memkernels_plot.png")
print("Grafik kaydedildi -> logs/memkernels_plot.png")
