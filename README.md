# Achilles

Game Manager para Arch Linux — instala, organiza e lança jogos via Wine/Proton a partir de repacks.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Platform](https://img.shields.io/badge/Platform-Arch%20Linux-1793D1)
![DE](https://img.shields.io/badge/DE-Hyprland-58E1FF)

## Funcionalidades

- **Instalação com 3 cliques** — seleciona a pasta do repack, instala via Wine, adiciona à biblioteca
- **Detecção automática de runtime** — encontra Wine, Proton e Proton-GE instalados e recomenda o melhor
- **Biblioteca visual** — cards com indicador de runtime, tempo jogado, tags e launch rápido
- **Monitoramento em tempo real** — CPU, Disk I/O e progresso de chunks durante instalação
- **WINEPREFIX isolado** — cada jogo tem seu próprio prefix, sem conflitos
- **Tracking de tempo** — registra duração de cada sessão (ignora <10s)
- **Detecção automática de instaladores** — monitora a pasta de Downloads e avisa quando encontra um repack novo
- **Debug completo** — logs detalhados salvos em `~/.config/achilles/logs/`

## Stack

| Componente | Tecnologia |
|---|---|
| GUI | CustomTkinter (Catppuccin Mocha) |
| Runtime | Wine-staging, Proton-GE |
| Monitoramento | `/proc` (CPU, I/O) direto do kernel |
| Persistência | JSON (`~/.config/achilles/`) |

## Instalação

```bash
# Dependências (Arch Linux)
sudo pacman -S wine-staging winetricks tk freetype2 lib32-freetype2

# Opcional: runtime otimizado pra jogos
yay -S proton-ge-custom-bin

# Rodar
cd achilles
python -m venv .venv
.venv/bin/pip install customtkinter
.venv/bin/python main.py
```

## Como funciona

```
Repack detectado → Instalador via Wine (debug mode)
    → Monitoramento CPU/IO/chunks em tempo real
    → Jogo adicionado à biblioteca com WINEPREFIX isolado
    → Launch via Proton-GE (silent mode, melhor performance)
```

## Screenshots

> TODO: adicionar screenshots da interface

## Estrutura

```
main.py                    # Aplicação completa (~1780 linhas)
~/.config/achilles/
├── biblioteca.json        # Biblioteca de jogos
├── config.json            # Preferências
└── logs/                  # Logs de instalação
~/.local/share/achilles/
└── prefixes/              # WINEPREFIXes isolados por jogo
```
