#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSKernelSwitch, DefaultController
from mininet.log import setLogLevel
from time import sleep
import sys
import argparse

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

def apply_no_qos(switch, iface):
    print(f"[QoS 0] Sem configuração de QoS aplicada em {iface}.")

def apply_tbf(switch, iface):
    print(f"[QoS 1] Aplicando TBF (rate limit) em {iface}...")
    switch.cmd(f'tc qdisc add dev {iface} root tbf rate 100mbit burst 32kbit latency 70ms')

def apply_sfq(switch, iface):
    print(f"[QoS 2] Aplicando SFQ simples em {iface}...")
    switch.cmd(f'tc qdisc add dev {iface} root sfq perturb 10')

def apply_htb(switch, iface):
    print(f"[QoS 3] Aplicando HTB com múltiplas classes...")
    switch.cmd(f'tc qdisc add dev {iface} root handle 1: htb default 30')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:10 htb rate 5mbit ceil 10mbit')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:20 htb rate 3mbit ceil 10mbit')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:30 htb rate 2mbit ceil 10mbit')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip dport 5004 0xffff flowid 1:10')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip dport 5006 0xffff flowid 1:10')
    switch.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 2 u32 match ip dport 5001 0xffff flowid 1:20')

def apply_htb_sfq(switch, iface):
    print(f"[QoS 4] Aplicando HTB + SFQ por classe...")
    apply_htb(switch, iface)
    switch.cmd(f'tc qdisc add dev {iface} parent 1:10 handle 10: sfq perturb 10')
    switch.cmd(f'tc qdisc add dev {iface} parent 1:20 handle 20: sfq perturb 10')
    switch.cmd(f'tc qdisc add dev {iface} parent 1:30 handle 30: sfq perturb 10')

def apply_fwmark_filtering(switch, iface):
    print(f"[QoS 5] Aplicando HTB + SFQ com marcação por iptables...")
    switch.cmd(f'tc qdisc add dev {iface} root handle 1: htb default 30')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:10 htb rate 5mbit ceil 10mbit')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:20 htb rate 3mbit ceil 10mbit')
    switch.cmd(f'tc class add dev {iface} parent 1: classid 1:30 htb rate 2mbit ceil 10mbit')
    switch.cmd(f'tc qdisc add dev {iface} parent 1:10 handle 10: sfq perturb 10')
    switch.cmd(f'tc qdisc add dev {iface} parent 1:20 handle 20: sfq perturb 10')
    switch.cmd(f'tc qdisc add dev {iface} parent 1:30 handle 30: sfq perturb 10')
    switch.cmd('iptables -t mangle -A PREROUTING -p udp --dport 5004 -j MARK --set-mark 10')
    switch.cmd('iptables -t mangle -A PREROUTING -p udp --dport 5001 -j MARK --set-mark 20')
    switch.cmd(f'tc filter add dev {iface} parent 1:0 protocol ip handle 10 fw flowid 1:10')
    switch.cmd(f'tc filter add dev {iface} parent 1:0 protocol ip handle 20 fw flowid 1:20')

def run(tecnica):
    topo = RTPTopo()
    net = Mininet(topo=topo, link=TCLink, switch=OVSKernelSwitch, controller=DefaultController)
    net.start()

    h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
    s1, _ = net.get('s1', 's2')
    iface = 's1-eth3'

    if tecnica == 0:
        apply_no_qos(s1, iface)
    elif tecnica == 1:
        apply_tbf(s1, iface)
    elif tecnica == 2:
        apply_sfq(s1, iface)
    elif tecnica == 3:
        apply_htb(s1, iface)
    elif tecnica == 4:
        apply_htb_sfq(s1, iface)
    elif tecnica == 5:
        apply_fwmark_filtering(s1, iface)
    else:
        print("Técnica inválida. Escolha de 0 a 5.")
        net.stop()
        return

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
    print("Iniciando ffplay em h2...")
    h2.cmd('ffplay -protocol_whitelist "file,udp,rtp" -fflags nobuffer -flags low_delay -i video.sdp '
           '> /tmp/ffplay.log 2>&1 &')

    sleep(2)
    print("Monitorando interface {iface}...")
    monitor = s1.popen(f'ifstat -i {iface} 0.5', stdout=sys.stdout)

    sleep(10)
    print("Iniciando 3 fluxos iperf UDP de h3 para h4 por 20 segundos...")
    for i in range(3):
        h3.cmd(f'iperf -c 10.0.0.4 -u -b 3M -t 20 > /tmp/iperf_{i}.log 2>&1 &')

    sleep(40)
    print("Encerrando monitoramento e rede...")
    monitor.terminate()
    net.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tecnica', type=int, default=0, help='Técnica de QoS (0 a 5)')
    args = parser.parse_args()
    setLogLevel('info')
    run(args.tecnica)
