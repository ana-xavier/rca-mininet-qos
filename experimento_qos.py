#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSKernelSwitch, DefaultController
from mininet.log import setLogLevel
from time import sleep
import sys

class RTPTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1')  # vídeo origem
        h2 = self.addHost('h2')  # vídeo destino
        h3 = self.addHost('h3')  # iperf origem
        h4 = self.addHost('h4')  # iperf destino

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h3, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(h4, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)


def show_tc_config(switch, iface):
    print(f"Configuração atual do tc em {iface} de {switch.name}:\n")
    print(switch.cmd(f'tc qdisc show dev {iface}'))
    print(switch.cmd(f'tc class show dev {iface}'))
    print(switch.cmd(f'tc filter show dev {iface}'))


def apply_egress_with_priority(switch, iface):
    """
    Aplica prioridade absoluta ao tráfego RTP usando a disciplina de enfileiramento 'prio'.

    Esta técnica implementa Programação (Scheduling) com Filas por Prioridade,
    permitindo que pacotes RTP (vídeo e áudio) sejam sempre transmitidos antes
    de qualquer outro tipo de tráfego, independentemente da taxa de transmissão.

    O Mininet já aplica automaticamente os seguintes comandos ao usar TCLink(bw=10):
        tc qdisc add dev <iface> root handle 5: htb default 1
        tc class add dev <iface> parent 5: classid 5:1 htb rate 10mbit

    Esta função respeita essa configuração existente e funciona adicionando uma
    qdisc do tipo 'prio' como filha da classe HTB padrão (5:1), permitindo que
    pacotes RTP sejam atendidos com prioridade máxima dentro do limite de banda
    de 10mbit definida a configuração da topologia do Mininet.

    Técnicas de QoS utilizadas:
    - Programação (Scheduling): prio com 3 bandas de prioridade (0 > 1 > 2)
    - Filas por prioridade: banda 0 só esvaziada antes das outras
    - Classificação de pacotes: com base na porta de destino (u32 match)
    """

    print(f"[QoS] Adicionando disciplina 'prio' como filha de HTB em {iface} de {switch.name}...")

    # Programação (Scheduling):
    # Adiciona qdisc 'prio' com 3 bandas (0 = mais prioritária) dentro da classe 5:1 do HTB
    switch.cmd(f'tc qdisc add dev {iface} parent 5:1 handle 10: prio bands 3')

    # Classificação de pacotes:
    # Direciona tráfego RTP (portas 5004 e 5006) para banda 0 (prioridade mais alta)
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 10: prio 1 u32 match ip dport 5004 0xffff flowid 10:1')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 10: prio 1 u32 match ip dport 5006 0xffff flowid 10:1')

    # Direciona tráfego iperf (porta 5001) para banda 1 (prioridade intermediária)
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 10: prio 2 u32 match ip dport 5001 0xffff flowid 10:2')

    # Todo o restante do tráfego irá automaticamente para a banda 2 (sem prioridade)


def run():
    topo = RTPTopo()
    net = Mininet(topo=topo, link=TCLink, switch=OVSKernelSwitch, controller=DefaultController)
    net.start()

    h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
    s1, s2 = net.get('s1', 's2')

    print("Aplicando regras de QoS entre os switches s1 e s2...")
    apply_egress_with_priority(s1, 's1-eth3')  # tráfego s1 → s2
    show_tc_config(s1, 's1-eth3')

    print("Iniciando transmissão RTP de h1 para h2...")

    h1.cmd(
        'ffmpeg -re -i video.mp4 '
        '-map 0:v:0 -c:v libx264 -preset ultrafast -tune zerolatency '
        '-x264-params "keyint=25:scenecut=0:repeat-headers=1" '
        '-f rtp rtp://10.0.0.2:5004?pkt_size=1200 '
        '-map 0:a:0 -c:a aac -ar 44100 -b:a 128k '
        '-f rtp rtp://10.0.0.2:5006?pkt_size=1200 '
        '-sdp_file video.sdp > /tmp/ffmpeg.log 2>&1 &'
    )

    sleep(2)

    print("Iniciando ffplay em h2...")

    h2.cmd('ffplay -report -protocol_whitelist "file,udp,rtp" -fflags nobuffer -flags low_delay -i video.sdp '
       '> /tmp/ffplay.log 2>&1 &')

    sleep(2)

    print("Iniciando monitoramento da interface do link s1 <-> s2...")
    monitor = s1.popen('ifstat -i s1-eth3 0.5', stdout=sys.stdout)

    sleep(10)

    num_streams = 3
    duration = 20
    print(f"Iniciando {num_streams} fluxo(s) iperf UDP de h3 para h4 por {duration} segundos...")
    for i in range(num_streams):
        h3.cmd(f'iperf -c 10.0.0.4 -u -b 3M -t {duration} > /tmp/iperf_{i}.log 2>&1 &')

    print("Executando experimento por mais 40 segundos...")
    sleep(40)

    print("Encerrando monitoramento...")
    monitor.terminate()

    print("Encerrando rede...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
