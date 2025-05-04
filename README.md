# Emulação de rede com Mininet

## Objetivo

Simular uma rede com transmissão de vídeo usando RTP entre dois nós, degradar a qualidade com tráfego iperf, e depois aplicar QoS para preservar a qualidade do vídeo. Este roteiro foi elaborado para computadores com Ubuntu Linux ou outras distribuições baseadas em Debian. Caso necessário, recomenda-se utilizar uma [máquina virtual](https://www.osboxes.org/ubuntu/#ubuntu-24-04-vbox) com Ubuntu 24.04 para VirtualBox.

## Instalar Mininet

Instalar pacotes:

```bash
apt-get install mininet 
apt-get install openvswitch-testcontroller
apt-get install iperf ifstat
```

Matar o controlador local:
```bash
sudo killall ovs-testcontroller
```

## Testar streaming de video via RTP

Baixar um video de exemplo no computador local:
```bash
wget https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4 -O video.mp4
```

Para permitir que o player de vídeo (executado como root dentro do Mininet) acesse o sistema de som e exiba janelas na interface gráfica do usuário, é necessário conceder permissão ao usuário root para usar o servidor gráfico. Execute o seguinte comando no terminal antes de iniciar o experimento:
```bash
xhost +SI:localuser:root
```

Executar o experimento:

```bash
sudo python experimento.py
```

## Limpar o ambiente após uma emulação

Quando o mininet é interrompido bruscamente pode ser necessário realizar o um `cleanup` do ambiente.

Execute este comando para limpar interfaces virtuais, bridges e processos Mininet antigos:

```bash
sudo mn -c
```

## Referências:

- Get Started With Mininet: https://mininet.org/download/
- Ubuntu 24.04 Virtual Machine: https://www.osboxes.org/ubuntu/#ubuntu-24-04-VirtualBox

