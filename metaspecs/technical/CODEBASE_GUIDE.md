# Guia de Navegação da Base de Código

## Estrutura de Diretórios

```
achilles/
├── main.py                  # Aplicação inteira (backend + GUI)
├── .venv/                   # Virtualenv Python (customtkinter)
├── docs/                    # Documentação do repositório (repodocs)
│   ├── index.md
│   ├── stack.md
│   ├── patterns.md
│   ├── features.md
│   ├── business-rules.md
│   └── integrations.md
└── metaspecs/               # Especificações técnicas e arquiteturais
    └── technical/
        ├── index.md
        ├── project_charter.md
        ├── CLAUDE.meta.md
        ├── CODEBASE_GUIDE.md   (este arquivo)
        ├── BUSINESS_LOGIC.md
        ├── CONTRIBUTING.md
        ├── TROUBLESHOOTING.md
        └── adr/
            ├── 001-arquivo-unico.md
            ├── 002-customtkinter.md
            ├── 003-wineprefix-isolado.md
            ├── 004-monitoramento-proc.md
            └── 005-debug-wine-modo.md
```

## Arquivos em Runtime

```
~/.config/achilles/
├── biblioteca.json          # Lista de jogos (JSON array)
├── config.json              # Preferências do app
└── logs/                    # Logs de debug de instalações
    └── setup_20260310_143022.log

~/.local/share/achilles/
└── prefixes/                # WINEPREFIXes isolados por jogo
    ├── resident-evil-village/
    └── cyberpunk-2077/

~/.local/share/applications/
└── achilles.desktop         # Integração com launcher/rofi
```

## Arquivos Chave e Seus Papéis

### main.py — O Aplicativo
| Seção | Linhas | Responsabilidade |
|-------|--------|------------------|
| Constantes | 1-67 | Cores (Catppuccin Mocha), caminhos, configs padrão, erros mapeados |
| DetectorRuntime | 73-192 | Busca Wine/Proton no sistema, recomenda o melhor |
| Biblioteca | 198-273 | CRUD de jogos, persistência JSON, tempo jogado |
| Configuracao | 279-302 | Preferências do app (pasta monitorada, auto-delete) |
| DetectorInstaladores | 308-388 | Escaneia pasta, encontra setup.exe, calcula tamanho |
| VerificadorDependencias | 394-399 | Checa se wine/winetricks estão instalados |
| ExecutorWine | 405-556 | Roda exe via Wine/Proton, log debug, callback |
| MonitorProcesso | 562-697 | CPU/IO/chunks via /proc, detecção de travamento |
| App.__init__ | 704-733 | Estado inicial, layout, timers |
| App sidebar | 738-797 | Navegação + banner de detecção |
| App navegação | 800-819 | Troca de páginas, destrói/reconstrói widgets |
| App biblioteca | 824-1178 | Cards de jogos, jogar, config, remover |
| App instalar | 1183-1491 | Seleção de pasta, instalação, log, pós-install |
| App runtime | 1496-1610 | Página de detecção Wine/Proton |
| App config | 1615-1708 | Configurações do app |
| App detector | 1713-1754 | Escaneia downloads periodicamente |
| App fila log | 1759-1774 | Consumer da queue de log |

## Fluxo de Dados

### Instalação
```
Usuário seleciona pasta
    → DetectorInstaladores._encontrar_instalador()
    → VerificadorDependencias.faltando()
    → ExecutorWine(modo="install")
        → subprocess.Popen(wine/proton, env={DISPLAY, WINEPREFIX, WINEDEBUG})
        → threads leem stdout/stderr → queue.Queue → App._processar_fila()
        → MonitorProcesso lê /proc → App._loop_monitor()
    → callback_fim → App._pos_instalacao()
```

### Jogar
```
Usuário clica "Jogar" no card
    → DetectorRuntime.detectar_proton()
    → ExecutorWine(modo="play")
        → subprocess.Popen(wine/proton, WINEDEBUG=-all)
    → callback_fim → App._jogo_fim() → Biblioteca.registrar_sessao()
```

### Detecção Automática
```
App.after(10000, _escanear_downloads)
    → DetectorInstaladores.escanear()
    → Novo repack? → _atualizar_banner()
    → Usuário clica "Instalar" → _selecionar_pasta()
```

## Dependências Externas
| Dependência | Tipo | Obrigatória |
|-------------|------|-------------|
| customtkinter | pip (venv) | Sim |
| wine-staging | pacman | Sim |
| winetricks | pacman | Sim |
| tk | pacman | Sim |
| proton-ge-custom-bin | AUR | Não (recomendado) |
| freetype2 + lib32-freetype2 | pacman | Para fontes Wine |
