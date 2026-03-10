# Lógica de Negócio — Achilles

## Conceitos de Domínio

### Jogo
Entidade central. Representa um jogo instalado no sistema.
```python
{
    "nome": "Resident Evil Village",   # Nome exibido na biblioteca
    "exe": "/path/to/game.exe",        # Caminho do executável
    "pasta": "/path/to/game/",         # Pasta da instalação
    "data": "2026-03-10 14:30",        # Data de adição
    "runtime": "proton-ge",            # wine | proton | proton-ge
    "wineprefix": "/path/to/prefix",   # WINEPREFIX isolado
    "tempo_jogado": 7200,              # Segundos totais jogados
    "ultima_sessao": "2026-03-10 16:30", # Última vez que jogou
    "tags": ["Horror", "FPS"],         # Categorias do usuário
    "args": "-dx11"                    # Argumentos extras para o exe
}
```

### Repack
Pasta contendo um instalador de jogo. Detectado automaticamente na pasta monitorada.
```python
{
    "nome": "Resident Evil - Village [FitGirl Repack]",
    "caminho": "/home/user/Downloads/RE Village...",
    "instalador": "/home/user/Downloads/RE.../setup.exe"
}
```

### Runtime
Wine, Proton ou Proton-GE instalado no sistema.
```python
# Wine
{"tipo": "wine", "caminho": "/usr/bin/wine", "versao": "wine-9.0"}

# Proton
{"tipo": "proton", "nome": "Proton 9.0-1", "caminho": "/path/proton", "origem": "Steam (oficial)"}

# Proton-GE
{"tipo": "proton-ge", "nome": "GE-Proton9-7", "caminho": "/path/proton", "origem": "Proton-GE"}
```

## Regras de Negócio

### R1: Prioridade de Runtime
**Regra**: Proton-GE > Proton oficial > Wine puro
**Motivo**: Proton-GE tem patches para anti-cheat, codecs de vídeo e correções específicas
**Exceção**: Wine é usado para instalação (setup.exe sempre roda via Wine)

### R2: Slug de WINEPREFIX
**Regra**: `nome.lower()` → substituir `[^a-zA-Z0-9]` por `-` → strip `-`
**Exemplo**: "Resident Evil Village" → `resident-evil-village`
**Localização**: `~/.local/share/achilles/prefixes/{slug}/`

### R3: Sessão Mínima
**Regra**: Sessões < 10 segundos não são registradas
**Motivo**: Evitar contabilizar aberturas acidentais ou crashes imediatos

### R4: Detecção de Travamento
**Regra**: Se CPU delta = 0 E IO delta = 0 por > 120 segundos → status "travado"
**Exibição**: Label vermelho "SEM ATIVIDADE (Xmin)" + log warning aos 2 minutos

### R5: Filtro de Log Visual
**Regra**: No modo install, linhas de stderr só aparecem na UI se contêm keywords relevantes
**Keywords**: `err:`, `error`, `warn:`, `fixme:`, `critical`, `fail`, `exception`, `chunk`, `.pak`, `extract`, `decompress`, `unpack`, `write`, `create`, `open`, `loaddll`, `loading`, `loaded`
**Todo o output** vai para o arquivo de log sem filtro

### R6: Detecção de Instalador
**Prioridade de busca**:
1. `setup.exe` (case insensitive)
2. `install.exe`
3. `installer.exe`
4. `setup-*.exe` (glob)
5. `autorun.exe`
6. `start.exe`
7. Se há exatamente 1 `.exe` na pasta → usa esse

### R7: Auto-delete
**Regra**: Se `config.auto_delete == True` e instalação bem-sucedida → oferece deletar pasta do repack
**Proteção**: Sempre pede confirmação mostrando nome e tamanho da pasta

### R8: Migração de Schema
**Regra**: Ao carregar `biblioteca.json`, `setdefault()` é chamado para cada campo novo
**Motivo**: Jogos adicionados em versões anteriores do Achilles podem não ter campos como `tags` ou `args`

## Cálculos

### Progresso por Chunks
```
progresso = ((chunk_atual + 1) / total_chunks) * 100
```
- `total_chunks` = quantidade de arquivos `re_chunk_XXX.pak` na pasta do repack
- `chunk_atual` = maior número de chunk aberto em `/proc/[pid]/fd`

### Tempo Jogado Formatado
```
< 60s → "< 1 min"
< 1h  → "{minutos} min"
≥ 1h  → "{horas:.1f}h"
```

### Tamanho Formatado
```
< 1 MB → "{KB:.1f} KB"
< 1 GB → "{MB:.1f} MB"
≥ 1 GB → "{GB:.1f} GB"
```
