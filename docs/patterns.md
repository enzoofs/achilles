# Padrões de Design

## Padrões Arquiteturais

### Separação Backend/Frontend
O código é organizado em duas camadas dentro de um único arquivo:
- **Backend** (linhas 1-700): Classes independentes da GUI que encapsulam toda lógica de negócio
- **Frontend** (linhas 700-1780): Classe `App` que herda de `ctk.CTk` e controla a interface

### Page Navigation Pattern
A GUI usa um padrão de navegação por páginas:
- Sidebar fixa com botões de navegação
- Área de conteúdo dinâmica que é reconstruída a cada troca de página
- Método `_mostrar_pagina(nome)` destrói widgets existentes e reconstrói a página selecionada

### Producer-Consumer (Log)
Comunicação entre threads de Wine e a GUI via `queue.Queue`:
- **Producer**: Threads de leitura de stdout/stderr do processo Wine
- **Consumer**: Loop `_processar_fila()` na thread principal (via `after(100, ...)`)
- Cada mensagem é uma tupla `(tipo, conteudo)` onde tipo controla a cor no log

## Padrões de Código

### Classe de Dados com JSON
`Biblioteca` e `Configuracao` seguem o mesmo padrão:
- `_carregar()` lê JSON do disco no `__init__`
- `_salvar()` escreve JSON no disco após cada mutação
- `setdefault()` para migração de schema (campos novos em dados antigos)

### Detecção por Scanning
`DetectorRuntime` e `DetectorInstaladores` escaneiam o filesystem:
- Buscam em caminhos conhecidos (`~/.steam/`, `/proc/`)
- Retornam listas de dicionários com metadados
- Usam padrões de fallback (ex: se não acha `setup.exe`, procura qualquer `.exe`)

### Thread com Callback
`ExecutorWine` usa threading com callback:
```python
threading.Thread(target=self._executar, daemon=True).start()
# No fim de _executar:
self.callback_fim(codigo)
```
O callback usa `self.after(0, ...)` para voltar à thread principal do tkinter.

### Monitor de Processo
`MonitorProcesso` lê `/proc` periodicamente:
- CPU: `/proc/[pid]/stat` campos 14+15 (utime + stime)
- IO: `/proc/[pid]/io` campo write_bytes
- Chunks: `/proc/[pid]/fd` procurando symlinks para `re_chunk_XXX.pak`
- Detecta inatividade comparando deltas entre leituras

## Organização de Código

```
main.py
├── Constantes (CORES, caminhos, configs, erros)
├── DetectorRuntime (77-192)
├── Biblioteca (198-273)
├── Configuracao (279-302)
├── DetectorInstaladores (308-388)
├── VerificadorDependencias (394-399)
├── ExecutorWine (405-556)
├── MonitorProcesso (562-697)
└── App (703-1779)
    ├── __init__ (704-733)
    ├── Sidebar (738-797)
    ├── Conteúdo/Navegação (800-819)
    ├── Página Biblioteca (824-1178)
    ├── Página Instalar (1183-1491)
    ├── Página Runtime (1496-1610)
    ├── Página Config (1615-1708)
    ├── Detector Downloads (1713-1754)
    └── Fila de Log (1759-1774)
```

## Convenções de Nomenclatura
- **Classes**: PascalCase em português (`DetectorRuntime`, `MonitorProcesso`)
- **Métodos privados**: `_prefixo_acao` (ex: `_pag_biblioteca`, `_log`, `_jogar`)
- **Variáveis**: snake_case em português (ex: `caminho_pasta`, `fila_log`, `tempo_jogado`)
- **Constantes**: UPPER_SNAKE_CASE (ex: `PASTA_CONFIG`, `CORES`, `NOMES_INSTALADOR`)
- **Dicionários de dados**: chaves em português (ex: `"nome"`, `"exe"`, `"tags"`)

## Padrões de Tratamento de Erros
- Wine stderr é classificado por keywords: `err:`, `warn:`, `fixme:`, `critical`
- Erros conhecidos mapeados via regex em `ERROS_CONHECIDOS` para mensagens amigáveis
- Threads daemon com `try/except` para evitar crashes silenciosos
- `PermissionError` tratado em escaneamento de pastas

## Tema Visual
Catppuccin Mocha com dicionário `CORES` centralizado:
- Background: `base` → `mantle` → `crust` (escuro para mais escuro)
- Superfícies: `surface0` → `surface1` → `surface2`
- Texto: `text` → `subtext1` → `subtext0` → `overlay0`
- Accents: `lavender` (nav), `blue` (ações), `green` (sucesso), `red` (erro), `mauve` (Wine), `sapphire` (Proton)
