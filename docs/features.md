# Funcionalidades

## Funcionalidades Principais

### Instalação de Jogos via Wine/Proton
**Descrição**: Instala jogos a partir de repacks (FitGirl, etc.) usando Wine ou Proton como runtime.
**Casos de Uso**: Usuário baixa um repack, seleciona a pasta no Achilles, e o instalador roda automaticamente com as variáveis de ambiente corretas.
**Componentes**: `ExecutorWine`, `DetectorInstaladores`, `VerificadorDependencias`
**Fluxo**:
1. Usuário seleciona pasta do repack (ou é detectada automaticamente)
2. Sistema detecta o `setup.exe` (ou outro instalador) dentro da pasta
3. Verifica dependências (wine, winetricks)
4. Roda o instalador com `DISPLAY=:0`, `WINEPREFIX`, e `WINEDEBUG` corretos
5. Log em tempo real com filtro inteligente
6. Pós-instalação: adicionar à biblioteca, deletar instalador, ver log

### Biblioteca de Jogos
**Descrição**: Organiza jogos instalados com cards visuais, mostrando runtime, tags, tempo jogado e última sessão.
**Casos de Uso**: Gerenciar e lançar jogos rapidamente a partir de uma interface centralizada.
**Componentes**: `Biblioteca`, `App._pag_biblioteca`, `App._card_jogo`
**Dados por jogo**: nome, exe, pasta, data de adição, runtime, wineprefix, tempo jogado, última sessão, tags, argumentos extras

### Monitoramento de Instalação em Tempo Real
**Descrição**: Monitora CPU, I/O e progresso de chunks durante a instalação, detectando travamentos.
**Casos de Uso**: Saber se o instalador travou no unpacking de `re_chunk_000.pak` (comum em FitGirl repacks).
**Componentes**: `MonitorProcesso`
**Indicadores**:
- Tempo decorrido
- I/O total e delta (bytes escritos)
- Status: ATIVO / aguardando / SEM ATIVIDADE
- Progresso por chunk (barra + percentual)
- Alerta após 2 minutos sem atividade

### Debug Automático de Instalações
**Descrição**: Ativa `WINEDEBUG=+file,+loaddll,+seh` automaticamente durante instalações.
**Casos de Uso**: Diagnosticar por que uma instalação falhou ou travou.
**Componentes**: `ExecutorWine` (modos `install` vs `play`)
**Comportamento**:
- Modo install: debug Wine ativo, log completo salvo em `~/.config/achilles/logs/`
- Modo play: `WINEDEBUG=-all` (silencioso)
- UI filtra linhas verbosas, mostrando apenas erros, chunks, DLLs e operações relevantes
- Botão "Ver log" após instalação para abrir log completo

### Detecção e Recomendação de Runtime
**Descrição**: Detecta Wine, Proton e Proton-GE instalados, e recomenda o melhor para cada caso.
**Casos de Uso**: Usuário não sabe se deve usar Wine ou Proton para um jogo específico.
**Componentes**: `DetectorRuntime`
**Prioridade de recomendação**: Proton-GE > Proton oficial > Wine
**Locais escaneados**:
- `~/.steam/root/compatibilitytools.d`
- `~/.local/share/Steam/compatibilitytools.d`
- `~/.steam/steam/compatibilitytools.d`
- `~/.steam/root/steamapps/common`
- `~/.local/share/Steam/steamapps/common`

### Detecção Automática de Instaladores
**Descrição**: Monitora pasta de downloads e notifica quando um novo repack é detectado.
**Casos de Uso**: Usuário baixa um repack e o Achilles detecta automaticamente.
**Componentes**: `DetectorInstaladores`, `App._escanear_downloads`
**Comportamento**:
- Escaneia a pasta monitorada a cada 10 segundos
- Detecta pastas com `setup.exe`, `install.exe`, `installer.exe`, etc.
- Banner na sidebar com opção de "Instalar" ou "Ignorar"
- Ignora repacks já vistos

## Funcionalidades Secundárias

### Propriedades por Jogo
Janela de configuração individual com:
- Nome editável
- Executável (com seletor de arquivo)
- WINEPREFIX isolado
- Runtime (Wine / Proton / Proton-GE)
- Argumentos extras (ex: `-fullscreen -dx11`)
- Tags/categorias

### Tempo Jogado
- Registra duração de cada sessão (ignora < 10 segundos)
- Formata em minutos ou horas
- Exibe última sessão jogada

### Limpeza de Repacks
- Botão "Deletar instalador" pós-instalação
- Opção de auto-delete nas configurações
- Mostra tamanho antes de confirmar

### WINEPREFIX Isolado
- Cria automaticamente prefix em `~/.local/share/achilles/prefixes/{slug-do-jogo}/`
- Lista prefixes existentes na página de configurações
- Evita conflitos entre jogos que precisam de configurações Wine diferentes

### Forçar Encerramento
- Botão para matar processo Wine/Proton travado
- Usa `kill -9` + `wineserver -k`

## Funcionalidades em Desenvolvimento
- Busca integrada de jogos (inspirado no Hydra Launcher)
- Integração com agregadores (FitGirl, skidrow, etc.)
