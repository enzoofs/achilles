# Guia de Desenvolvimento com IA — Achilles

## Visão Geral Rápida
Achilles é um gerenciador de jogos Linux em Python/CustomTkinter. Arquivo único (`main.py`, ~1780 linhas). Backend (classes puras) + Frontend (classe App herda ctk.CTk).

## Estrutura do Código
```
main.py
├── Constantes (1-67)       — Tema, caminhos, configs padrão, erros
├── DetectorRuntime (73-192) — Detecta Wine/Proton/Proton-GE
├── Biblioteca (198-273)     — CRUD jogos + tempo jogado (JSON)
├── Configuracao (279-302)   — Prefs do app (JSON)
├── DetectorInstaladores (308-388) — Monitora pasta downloads
├── VerificadorDeps (394-399)      — Checa wine/winetricks
├── ExecutorWine (405-556)   — Roda exe via Wine/Proton + debug
├── MonitorProcesso (562-697)— Monitora CPU/IO/chunks via /proc
└── App (703-1779)           — GUI completa
```

## Estilo de Código
- Comentários em **português brasileiro**
- Nomes de variáveis/funções em português (snake_case)
- Classes em PascalCase
- Sem docstrings formais, apenas comentários inline onde necessário
- Sem type hints (código simples o bastante para funcionar sem)

## Padrões Essenciais

### Adicionar nova página na GUI
1. Criar método `_pag_novoNome(self)` na classe `App`
2. Adicionar entrada no dicionário de navegação em `_mostrar_pagina()` (linha ~818)
3. Adicionar botão na sidebar em `_criar_sidebar()` (linha ~759)

### Adicionar campo novo na biblioteca
1. Adicionar no dicionário de `Biblioteca.adicionar()` (linha ~231)
2. Adicionar `jogo.setdefault("campo", valor)` no `_carregar()` (linha ~211) para migração

### Executar algo via Wine
```python
executor = ExecutorWine(
    caminho_exe="caminho.exe",
    fila_log=self.fila_log,
    wineprefix="~/.local/share/achilles/prefixes/slug",
    runtime="wine",  # ou "proton", "proton-ge"
    proton_path=None,  # caminho do proton se runtime != wine
    args="",
    modo="install",  # ou "play"
    callback_fim=lambda rc: self.after(0, lambda: self._handler(rc)),
)
executor.iniciar()
```

### Comunicação thread → GUI
```python
# Na thread:
self.fila_log.put(("tipo", "mensagem"))
# Tipos: "info", "aviso", "erro", "erro_conhecido", "sucesso", "fim"

# Na GUI (já implementado em _processar_fila):
# Loop automático a cada 100ms lê da fila e insere no log_text
```

## Pegadinhas Conhecidas
1. **bind_all no canvas**: Nunca usar `canvas.bind_all()` para scroll. Usar `canvas.bind()` local — o binding persiste após destruir o widget e causa TclError.
2. **PEP 668**: Arch Linux bloqueia pip global. Sempre usar venv em `.venv/`.
3. **tkinter não instalado**: Arch não inclui tk por padrão. Precisa de `sudo pacman -S tk`.
4. **DISPLAY=:0**: Obrigatório para Wine no Hyprland/Wayland. Sem isso, Wine não abre.
5. **Proton paths**: `STEAM_COMPAT_DATA_PATH` deve apontar para o prefix, não para `drive_c` dentro dele.
6. **Threading + tkinter**: Nunca modificar widgets de uma thread. Usar `self.after(0, callback)` para voltar à thread principal.

## Como Rodar
```bash
cd /home/enzof/projetos/achilles
.venv/bin/python main.py
```

## Testes
Não há testes automatizados. Testar manualmente:
1. Abrir o app
2. Selecionar uma pasta com setup.exe
3. Verificar detecção de runtime
4. Instalar e verificar log + monitor
5. Adicionar à biblioteca e lançar
