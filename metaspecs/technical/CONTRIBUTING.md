# Guia de Contribuição — Achilles

## Setup do Ambiente

### Pré-requisitos
```bash
# Pacotes do sistema
sudo pacman -S python tk wine-staging winetricks freetype2 lib32-freetype2

# Opcional (recomendado para jogos)
yay -S proton-ge-custom-bin
```

### Instalação
```bash
cd /home/enzof/projetos/achilles

# Criar venv (se não existir)
python -m venv .venv

# Instalar dependências
.venv/bin/pip install customtkinter

# Rodar
.venv/bin/python main.py
```

### Desktop Entry
O arquivo `.desktop` já está em `~/.local/share/applications/achilles.desktop`. Para recriar:
```bash
cat > ~/.local/share/applications/achilles.desktop << 'EOF'
[Desktop Entry]
Name=Achilles
Comment=FitGirl Installer + Biblioteca de Jogos para Linux
Exec=/home/enzof/projetos/achilles/.venv/bin/python /home/enzof/projetos/achilles/main.py
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Utility;
Keywords=fitgirl;repack;wine;jogos;installer;
EOF
```

## Fluxo de Desenvolvimento

### Estrutura
Todo o código está em `main.py`. As classes de backend (DetectorRuntime, Biblioteca, etc.) são independentes da GUI e podem ser testadas isoladamente.

### Adicionando uma Nova Página
1. Criar método `_pag_nome(self)` na classe App
2. Adicionar ao dict de navegação em `_mostrar_pagina` (~linha 818)
3. Adicionar botão na sidebar em `_criar_sidebar` (~linha 759)

### Adicionando um Campo ao Jogo
1. Adicionar ao dicionário em `Biblioteca.adicionar()` (~linha 231)
2. Adicionar `setdefault()` em `Biblioteca._carregar()` (~linha 211)
3. Adicionar widget na `_config_jogo()` se editável
4. Atualizar exibição no `_card_jogo()` se visível

### Convenções
- Comentários em português brasileiro
- Nomes em português (snake_case para funções/variáveis, PascalCase para classes)
- Sem type hints, sem docstrings formais
- Threads com `daemon=True`
- Comunicação thread→GUI via `queue.Queue`
- Nunca modificar widgets fora da thread principal

## Verificação
```bash
# Sintaxe
.venv/bin/python -m py_compile main.py

# Rodar e testar manualmente
.venv/bin/python main.py
```

## Cuidados
- Não usar `bind_all()` em canvas — usar `bind()` local
- Não usar `os.system()` — sempre `subprocess.Popen` ou `subprocess.run`
- Não modificar widgets de threads — usar `self.after(0, callback)`
- Não instalar pip packages globalmente — sempre no venv
