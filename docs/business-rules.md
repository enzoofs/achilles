# Regras de Negócio

## Regras Críticas

### Variáveis de Ambiente para Wine
**Descrição**: Toda execução via Wine/Proton precisa de variáveis específicas para funcionar no Hyprland (Wayland).
**Justificativa**: Sem `DISPLAY=:0`, Wine não encontra o display via XWayland. Sem `WINEPREFIX`, usa o prefix global e causa conflitos.
**Implementação**: `ExecutorWine._executar()` (linha ~437)
**Variáveis obrigatórias**:
- `DISPLAY=:0` — XWayland no Hyprland
- `WINEPREFIX=<caminho>` — Prefix isolado por jogo
- `WINEDEBUG=<nível>` — Debug para instalação, silêncio para jogos

### Detecção de Instalador
**Descrição**: O sistema procura executáveis de instalação em uma ordem específica de prioridade.
**Justificativa**: Nem todo repack usa `setup.exe`. Alguns usam `install.exe`, `autorun.exe`, etc.
**Implementação**: `DetectorInstaladores._encontrar_instalador()` (linha ~336)
**Ordem de busca**:
1. Patterns conhecidos: `setup.exe`, `install.exe`, `installer.exe`, `setup-*.exe`, `autorun.exe`, `start.exe`
2. Glob para patterns com wildcard
3. Fallback: se há exatamente 1 `.exe` na pasta, usa esse

### WINEPREFIX Isolado por Jogo
**Descrição**: Cada jogo adicionado à biblioteca recebe automaticamente um prefix próprio.
**Justificativa**: Jogos diferentes podem precisar de configurações Wine incompatíveis. Isolamento previne que um jogo quebre outro.
**Implementação**: `Biblioteca.adicionar()` (linha ~224)
**Regra de slug**: nome do jogo → lowercase → caracteres não-alfanuméricos viram `-`
**Caminho**: `~/.local/share/achilles/prefixes/{slug}/`

### Debug Wine por Modo
**Descrição**: Instalações usam debug ativo, jogos usam silêncio total.
**Justificativa**: Debug é essencial para diagnosticar falhas na instalação, mas polui e reduz performance ao jogar.
**Implementação**: `ExecutorWine` (linhas ~408-446)
- Instalação: `WINEDEBUG=+file,+loaddll,+seh`
- Jogo: `WINEDEBUG=-all`

### Recomendação de Runtime
**Descrição**: O sistema recomenda automaticamente o melhor runtime disponível.
**Justificativa**: Proton-GE tem patches extras para jogos que Wine/Proton oficial não tem.
**Implementação**: `DetectorRuntime.recomendar()` (linha ~148)
**Prioridade**: Proton-GE > Proton oficial Valve > Wine puro

## Validações e Restrições

### Verificação de Dependências
- Checa `wine` e `winetricks` via `shutil.which()`
- Botão "Instalar" fica desabilitado se faltar dependência
- Mensagem mostra o comando exato para instalar

### Verificação de Executável
- Card de jogo mostra nome em vermelho se o `.exe` não existe mais no disco
- Botão "Jogar" fica desabilitado para executáveis inexistentes

### Sessão Mínima
- Sessões de jogo menores que 10 segundos são ignoradas no registro de tempo jogado
- Evita registrar aberturas acidentais ou crashes imediatos

## Políticas e Workflows

### Workflow de Instalação
```
Selecionar pasta → Detectar instalador → Checar deps → Instalar (Wine) → Log + Monitor → Pós-instalação
```

### Workflow Pós-Instalação
```
Sucesso/Falha → [Adicionar à biblioteca] → [Deletar instalador] → [Ver log] → [Nova instalação]
```

### Detecção Automática
```
Escanear pasta monitorada (10s) → Novo repack? → Banner na sidebar → Instalar/Ignorar
```

## Mapeamento de Erros Conhecidos

| Padrão no Wine | Mensagem para o Usuário | Causa Provável |
|----------------|------------------------|----------------|
| `no driver could be loaded` | Erro de display. Verifique se o XWayland está ativo. | XWayland não rodando |
| `FreeType font library` | FreeType não encontrado. | Pacotes `freetype2`/`lib32-freetype2` faltando |
| `c0000135` | Arquivo não encontrado ou caminho inválido. | Caminho do exe incorreto ou DLL faltando |

## Filtragem de Log
No modo debug, o log visual mostra apenas linhas contendo:
- Erros: `err:`, `error`, `warn:`, `fixme:`, `critical`, `fail`, `exception`
- Progresso: `chunk`, `.pak`, `extract`, `decompress`, `unpack`
- Operações: `write`, `create`, `open`, `loaddll`, `loading`, `loaded`

Todo o output vai para o arquivo de log completo em `~/.config/achilles/logs/`.
