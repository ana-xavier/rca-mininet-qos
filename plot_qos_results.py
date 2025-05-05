import os
import re
import matplotlib.pyplot as plt

base_path = "resultados"  # Pasta com subpastas tecnica_0 a tecnica_4

def extrair_bitrate_ffmpeg(caminho_log):
    bitrates = []
    with open(caminho_log, 'r') as f:
        for line in f:
            match = re.search(r'bitrate=\s*([\d.]+)\s*kbits', line)
            if match:
                try:
                    bitrate = float(match.group(1))
                    bitrates.append(bitrate)
                except ValueError:
                    continue
    return sum(bitrates) / len(bitrates) if bitrates else 0

def extrair_vazao_iperf(caminho_log):
    with open(caminho_log, 'r') as f:
        for line in f:
            if "Server Report" in line:
                continue
            match = re.search(r"([\d.]+)\s+Mbits/sec", line)
            if match:
                return float(match.group(1))
    return 0

bitrate_medios = []
iperf_medios = []

for i in range(5):
    dir_tec = os.path.join(base_path, f"tecnica_{i}")
    
    # Bitrate do ffmpeg
    ffmpeg_path = os.path.join(dir_tec, "ffmpeg.log")
    bitrate = extrair_bitrate_ffmpeg(ffmpeg_path)
    bitrate_medios.append(bitrate)

    # Vazões dos 3 iperf
    iperf_total = 0
    for j in range(3):
        iperf_path = os.path.join(dir_tec, f"iperf_{j}.log")
        iperf_total += extrair_vazao_iperf(iperf_path)
    iperf_medios.append(iperf_total)

# Plot - Bitrate
plt.figure(figsize=(8,5))
plt.bar(range(5), bitrate_medios, color='skyblue')
plt.xticks(range(5), [f'Técnica {i}' for i in range(5)])
plt.ylabel('Bitrate médio (kbits/s)')
plt.title('Bitrate do vídeo por técnica de QoS')
plt.grid(axis='y')
plt.tight_layout()
plt.savefig("grafico_bitrate.png")
plt.show()

# Plot - Vazão iperf
plt.figure(figsize=(8,5))
plt.bar(range(5), iperf_medios, color='lightgreen')
plt.xticks(range(5), [f'Técnica {i}' for i in range(5)])
plt.ylabel('Vazão total iperf (Mbits/s)')
plt.title('Vazão média dos fluxos iperf por técnica')
plt.grid(axis='y')
plt.tight_layout()
plt.savefig("grafico_iperf.png")
plt.show()
