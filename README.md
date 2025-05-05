# Experimento de QoS com Mininet

Este projeto simula diferentes técnicas de QoS (Qualidade de Serviço) utilizando o Mininet, `tc` (traffic control), `iptables`, e ferramentas como `iperf` e `ffmpeg`. 

## Requisitos
- Python 3
- Mininet
- ffmpeg e ffplay
- iperf
- ifstat

## Estrutura
A topologia consiste em dois switches (`s1` e `s2`) conectando quatro hosts:
- `h1`: origem do fluxo de vídeo (via RTP com ffmpeg)
- `h2`: destino do vídeo (reprodução com ffplay)
- `h3`: origem de tráfego UDP (iperf)
- `h4`: destino do tráfego UDP

## Como executar

Execute o script principal com o argumento `--tecnica` para selecionar a técnica de QoS desejada:

```bash
sudo python3 experimento_qos.py --tecnica N
```

Onde `N` é um número de 0 a 4:

| Técnica | Descrição |
|--------:|-----------|
| 0 | Sem QoS (baseline) |
| 1 | TBF (Token Bucket Filter) - limite de banda simples |
| 2 | SFQ (Stochastic Fairness Queueing) - justiça entre fluxos |
| 3 | HTB (Hierarchical Token Bucket) - alocação hierárquica de banda |
| 4 | HTB + SFQ - aloca banda mínima por tipo de tráfego com justiça entre fluxos |

## Exemplo

Executar o experimento com a técnica HTB + SFQ:
```bash
sudo python3 experimento_qos.py --tecnica 4
```

## Autor
Ana Carolina Xavier, Érico Bis e Rubens Montanha.

---

