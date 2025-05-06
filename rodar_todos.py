import os
import shutil
import subprocess
from time import sleep

def limpar_logs():
    for arquivo in ['/tmp/ffmpeg.log', '/tmp/ffplay.log'] + [f'/tmp/iperf_{i}.log' for i in range(3)]:
        if os.path.exists(arquivo):
            os.remove(arquivo)

def mover_logs(tecnica):
    pasta_destino = f'resultados/tecnica_{tecnica}'
    os.makedirs(pasta_destino, exist_ok=True)
    shutil.move('/tmp/ffmpeg.log', os.path.join(pasta_destino, 'ffmpeg.log'))
    for i in range(3):
        shutil.move(f'/tmp/iperf_{i}.log', os.path.join(pasta_destino, f'iperf_{i}.log'))
    if os.path.exists('/tmp/ifstat.log'):
        shutil.move('/tmp/ifstat.log', os.path.join(pasta_destino, 'ifstat.log'))

def rodar_tecnica(tecnica):
    print(f"\n=== Executando técnica {tecnica} ===")
    limpar_logs()
    comando = f'python3 experimento_qos.py --tecnica {tecnica}'
    subprocess.run(comando, shell=True)
    mover_logs(tecnica)
    print(f"=== Técnica {tecnica} finalizada ===")

if __name__ == '__main__':
    os.makedirs('resultados', exist_ok=True)
    for tecnica in range(5):
        rodar_tecnica(tecnica)
        print("Esperando 5 segundos antes da próxima técnica...")
        sleep(5)
    print("\n✅ Todos os testes foram executados. Resultados salvos em ./resultados")
