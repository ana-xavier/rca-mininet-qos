import pandas as pd
import matplotlib.pyplot as plt

# Carrega o CSV exportado do tshark
# Substitua "$USER" por seu nome real de usuário ou use os.path.expanduser("~") no Python para generalizar.
df = pd.read_csv("/home/$USER/rtp.csv")
df = df.dropna(subset=["rtp.seq", "frame.time_relative"])

# Conversão de tipos
df["rtp.seq"] = df["rtp.seq"].astype(int)
df["frame.time_relative"] = df["frame.time_relative"].astype(float)

# Ordena por sequência RTP
df = df.sort_values("rtp.seq")
seqs = df["rtp.seq"].to_list()
times = df["frame.time_relative"].to_list()

# Cálculo do jitter (diferença entre chegadas consecutivas)
jitters = [abs(times[i] - times[i-1]) for i in range(1, len(times))]
avg_jitter = sum(jitters) / len(jitters) if jitters else 0

# Cálculo de perda de pacotes
expected = seqs[-1] - seqs[0] + 1
received = len(seqs)
lost = expected - received
loss_percent = (lost / expected) * 100 if expected else 0

# --- Impressão dos resultados ---
print(f"[4/5] Jitter médio estimado: {avg_jitter:.6f} segundos")
print(f"[5/5] Pacotes RTP esperados: {expected}, recebidos: {received}, perdidos: {lost}")
print(f"      Porcentagem de perda: {loss_percent:.2f}%")

# --- Plot: Jitter ---
plt.figure(figsize=(10, 4))
plt.plot(jitters, label="Jitter (s)", color="blue")
plt.title("Jitter entre pacotes RTP")
plt.xlabel("Pacote")
plt.ylabel("Jitter (segundos)")
plt.grid(True)
plt.tight_layout()
plt.savefig("/home/$USER/jitter_plot.png")
plt.close()

# --- Plot: Sequência RTP ---
plt.figure(figsize=(10, 4))
plt.plot(seqs, label="Seq", color="green")
plt.title("Sequência RTP Recebida")
plt.xlabel("Ordem de chegada")
plt.ylabel("Número de sequência RTP")
plt.grid(True)
plt.tight_layout()
plt.savefig("/home/$USER/seq_rtp_plot.png")
plt.close()

print("Gráficos salvos como:")
print("  - /home/$USER/jitter_plot.png")
print("  - /home/$USER/seq_rtp_plot.png")

#Após rodar o script .sh, você terá:
#/home/seu_user/jitter_plot.png: linha mostrando jitter por pacote.
#/home/seu_user/seq_rtp_plot.png: gráfico mostrando quebras na sequência RTP (indicando perdas).