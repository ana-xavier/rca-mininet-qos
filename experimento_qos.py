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


def apply_qos_tc(switch, iface):
    print(f"[QoS] Aplicando HTB + prio + tbf em {iface} de {switch.name}...")

    # Resetando configurações anteriores
    switch.cmd(f'tc qdisc del dev {iface} root || true')

    # 1. HTB Root
    switch.cmd(f'tc qdisc add dev {iface} root handle 1: htb default 30')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:1 htb rate 10mbit ceil 10mbit')

    # 2. Classes com rate garantido
    switch.cmd(f'tc class add dev {iface} parent 1:1 classid 1:10 htb rate 4mbit ceil 8mbit')  # RTP
    switch.cmd(f'tc class add dev {iface} parent 1:1 classid 1:20 htb rate 2mbit ceil 5mbit')  # Iperf
    switch.cmd(f'tc class add dev {iface} parent 1:1 classid 1:30 htb rate 1mbit ceil 2mbit')  # Best-effort

    # 3. Filters para classificar pacotes
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip dport 5004 0xffff flowid 1:10')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip dport 5006 0xffff flowid 1:10')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 2 u32 match ip dport 5001 0xffff flowid 1:20')

    # 4. TBF para limitar burst de tráfego iperf
    switch.cmd(f'tc qdisc add dev {iface} parent 1:20 handle 20: tbf rate 5mbit burst 10kb latency 70ms')


def show_tc_config(switch, iface):
    print(f"[INFO] Configuração de QoS no {iface} de {switch.name}:\n")
    print(switch.cmd(f'tc -s qdisc show dev {iface}'))
    print(switch.cmd(f'tc -s class show dev {iface}'))
    print(switch.cmd(f'tc -s filter show dev {iface}'))


def run():
    topo = RTPTopo()
    net = Mininet(topo=topo, link=TCLink, switch=OVSKernelSwitch, controller=DefaultController)
    net.start()

    h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
    s1 = net.get('s1')

    iface = 's1-eth3'
    apply_qos_tc(s1, iface)
    show_tc_config(s1, iface)

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

    print("Iniciando captura de pacotes RTP com tcpdump em h2...")
    h2.cmd('tcpdump -i h2-eth0 udp port 5004 -w /tmp/video_rtp.pcap &')


    print("Iniciando ffplay em h2...")
    h2.cmd('ffplay -report -protocol_whitelist "file,udp,rtp" -fflags nobuffer -flags low_delay -i video.sdp '
           '> /tmp/ffplay.log 2>&1 &')

    sleep(2)

    print("Iniciando monitoramento da interface do link s1 <-> s2...")
    monitor = s1.popen(f'ifstat -i {iface} 0.5', stdout=sys.stdout)

    sleep(10)

    print("Iniciando tráfego iperf UDP de h3 para h4...")
    for i in range(3):
        h3.cmd(f'iperf -c 10.0.0.4 -u -b 3M -t 20 > /tmp/iperf_{i}.log 2>&1 &')

    print("Executando experimento por mais 40 segundos...")
    sleep(40)

    print("Encerrando monitoramento...")
    monitor.terminate()

    print("Encerrando rede...")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
