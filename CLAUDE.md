# Achilles — Game Manager para Arch Linux

## O que é
Gerenciador de jogos Linux com GUI em Python/CustomTkinter. Instala jogos via Wine/Proton a partir de repacks e organiza uma biblioteca pessoal com tempo jogado, configuração por jogo e detecção automática de runtimes.

## Comandos
```bash
# Rodar
.venv/bin/python main.py

# Checar sintaxe
.venv/bin/python -m py_compile main.py

# Instalar dependências
.venv/bin/pip install customtkinter
```

## Arquitetura
Arquivo único `main.py` (~1780 linhas) com separação clara:
- **Backend** (linhas 1-700): Classes puras sem dependência de GUI
  - `DetectorRuntime`, `Biblioteca`, `Configuracao`, `DetectorInstaladores`, `VerificadorDependencias`, `ExecutorWine`, `MonitorProcesso`
- **Frontend** (linhas 700+): Classe `App(ctk.CTk)` com páginas
  - Biblioteca, Instalar, Wine/Proton, Configurações

## Padrões obrigatórios
- Comentários em **português brasileiro**
- Nomes de variáveis/funções em português (snake_case)
- Comunicação thread→GUI via `queue.Queue` (nunca modificar widgets de threads)
- Usar `widget.bind()` ao invés de `widget.bind_all()` (causa TclError)
- `DISPLAY=:0` obrigatório para Wine no Hyprland
- WINEPREFIX isolado por jogo em `~/.local/share/achilles/prefixes/`

## Caminhos importantes
- Código: `/home/enzof/projetos/achilles/main.py`
- Venv: `/home/enzof/projetos/achilles/.venv/`
- Config: `~/.config/achilles/` (biblioteca.json, config.json, logs/)
- Prefixes: `~/.local/share/achilles/prefixes/`
- Desktop entry: `~/.local/share/applications/achilles.desktop`

## Documentação
- `docs/` — Documentação do repositório (repodocs)
- `metaspecs/technical/` — Especificações técnicas e ADRs

## Dependências do sistema
wine-staging, winetricks, tk, freetype2, lib32-freetype2
Opcional: proton-ge-custom-bin (AUR)
