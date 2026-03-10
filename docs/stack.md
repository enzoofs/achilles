# Stack Tecnológica

## Linguagens e Runtime
- **Python 3** (3.14+ no sistema atual)
- Runtime: CPython via venv isolado em `.venv/`

## Frameworks Principais
- **CustomTkinter 5.2.2** — GUI moderna sobre tkinter, com suporte a temas escuros e widgets estilizados
- **tkinter** — Backend de rendering (Tcl/Tk), requer pacote `tk` no Arch Linux

## Bibliotecas Chave
| Biblioteca | Propósito |
|------------|-----------|
| `customtkinter` | Interface gráfica com tema escuro |
| `subprocess` | Execução de Wine/Proton e comandos do sistema |
| `threading` + `queue` | Paralelismo sem travar a GUI |
| `json` | Persistência de biblioteca e configurações |
| `shutil` | Detecção de binários (`which`), remoção de pastas |
| `re` | Parsing de nomes, detecção de chunks, erros conhecidos |
| `glob` | Busca de padrões de instaladores |

## Dependências do Sistema
| Pacote | Propósito | Instalação |
|--------|-----------|------------|
| `wine-staging` | Runtime para executáveis Windows | `sudo pacman -S wine-staging` |
| `winetricks` | Configuração de dependências Wine | `sudo pacman -S winetricks` |
| `tk` | Backend tkinter para Python | `sudo pacman -S tk` |
| `freetype2` / `lib32-freetype2` | Fontes para Wine | `sudo pacman -S freetype2 lib32-freetype2` |
| Proton-GE (opcional) | Runtime otimizado para jogos | `yay -S proton-ge-custom-bin` |

## Infraestrutura
- **Plataforma alvo**: Arch Linux com Hyprland (Wayland + XWayland)
- **GPU**: NVIDIA GTX 1650 com drivers proprietários
- **Display**: XWayland (requer `DISPLAY=:0`)
- **Empacotamento**: Script único `main.py` rodando via venv
- **Desktop entry**: `.desktop` para integração com rofi/launcher

## Arquitetura Geral

```
main.py (arquivo único, ~1780 linhas)
├── Constantes e tema (Catppuccin Mocha)
├── Backend
│   ├── DetectorRuntime      — Detecta Wine/Proton/Proton-GE
│   ├── Biblioteca           — CRUD de jogos + tempo jogado
│   ├── Configuracao         — Persistência de preferências
│   ├── DetectorInstaladores — Monitora pasta de downloads
│   ├── VerificadorDependencias — Checa wine/winetricks
│   ├── ExecutorWine         — Roda exe via Wine/Proton
│   └── MonitorProcesso     — Monitora CPU/IO/chunks via /proc
└── GUI (App)
    ├── Sidebar com navegação
    ├── Página: Biblioteca (cards de jogos)
    ├── Página: Instalar (seleção + log + monitor)
    ├── Página: Wine/Proton (detecção + recomendação)
    └── Página: Configurações
```

## Decisões Arquiteturais Importantes

1. **Arquivo único**: Todo o código em `main.py` para simplicidade de distribuição e manutenção. Sem necessidade de build system.

2. **CustomTkinter sobre tkinter puro**: Aparência moderna com tema Catppuccin Mocha sem dependências pesadas como Qt ou GTK.

3. **Venv isolado**: Evita conflitos com PEP 668 do Arch Linux que bloqueia `pip install` global.

4. **WINEPREFIX isolado por jogo**: Cada jogo recebe seu próprio prefix em `~/.local/share/achilles/prefixes/` para evitar conflitos entre jogos.

5. **Monitoramento via /proc**: Leitura direta de `/proc/[pid]/stat`, `/proc/[pid]/io` e `/proc/[pid]/fd` para monitorar processo sem dependências externas.

6. **Wine para instalação, Proton-GE para jogar**: O sistema detecta runtimes disponíveis e recomenda o melhor para cada caso de uso.
