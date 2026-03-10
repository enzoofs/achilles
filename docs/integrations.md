# Integrações

## Sistema Operacional

### Wine / Wine-staging
**Tipo**: Binário do sistema (subprocess)
**Propósito**: Executar instaladores e jogos Windows (.exe) no Linux
**Protocolo**: `subprocess.Popen(["wine", "caminho.exe"], env={...})`
**Dados Trocados**: stdin/stdout/stderr do processo
**Dependência**: Crítica — sem Wine, nenhum jogo funciona
**Tratamento de Falhas**: `FileNotFoundError` capturado, mensagem informando para instalar

### Proton / Proton-GE
**Tipo**: Binário local (Steam compatibilitytools)
**Propósito**: Runtime otimizado para jogos com patches extras
**Protocolo**: `subprocess.Popen(["proton", "run", "caminho.exe"], env={STEAM_COMPAT_DATA_PATH, STEAM_COMPAT_CLIENT_INSTALL_PATH})`
**Dados Trocados**: stdin/stdout/stderr do processo
**Dependência**: Opcional — fallback para Wine se não disponível
**Detecção**: Escaneia diretórios do Steam buscando executável `proton`

### Filesystem /proc
**Tipo**: Virtual filesystem do Linux
**Propósito**: Monitoramento de processos sem dependências externas
**Dados Lidos**:
- `/proc/[pid]/stat` — Tempo de CPU (utime + stime)
- `/proc/[pid]/io` — Bytes escritos em disco
- `/proc/[pid]/fd` — File descriptors abertos (detecção de chunks)
- `/proc/[pid]/task/[pid]/children` — Processos filhos (árvore)
**Dependência**: Crítica para monitoramento, não para funcionalidade core

### XWayland (DISPLAY=:0)
**Tipo**: Display server
**Propósito**: Wine precisa de um X11 display para renderizar janelas
**Protocolo**: Variável de ambiente `DISPLAY=:0`
**Dependência**: Crítica — sem XWayland, Wine não abre janelas no Hyprland
**Tratamento de Falhas**: Erro mapeado: `no driver could be loaded` → mensagem sobre XWayland

### wineserver
**Tipo**: Daemon do Wine
**Propósito**: Gerencia processos Wine em um WINEPREFIX
**Uso no Achilles**: `wineserver -k` para forçar encerramento de processos travados
**Dependência**: Vem junto com Wine

### xdg-open
**Tipo**: Utilitário desktop
**Propósito**: Abrir arquivos de log com o editor padrão do sistema
**Uso**: Botão "Ver log" na pós-instalação

## Desktop Environment

### Rofi / Launcher
**Tipo**: Integração via .desktop entry
**Propósito**: Achilles aparece no launcher do sistema (SUPER + Espaço)
**Arquivo**: `~/.local/share/applications/achilles.desktop`
**Configuração**:
```ini
[Desktop Entry]
Name=Achilles
Comment=FitGirl Installer + Biblioteca de Jogos para Linux
Exec=/home/enzof/projetos/achilles/.venv/bin/python /home/enzof/projetos/achilles/main.py
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Utility;
```

## Armazenamento Local

### biblioteca.json
**Caminho**: `~/.config/achilles/biblioteca.json`
**Formato**: JSON array de objetos
**Campos por jogo**:
```json
{
  "nome": "string",
  "exe": "caminho/absoluto.exe",
  "pasta": "caminho/da/instalacao",
  "data": "YYYY-MM-DD HH:MM",
  "runtime": "wine|proton|proton-ge",
  "wineprefix": "caminho/do/prefix",
  "tempo_jogado": 0,
  "ultima_sessao": "YYYY-MM-DD HH:MM",
  "tags": ["FPS", "RPG"],
  "args": "-fullscreen"
}
```

### config.json
**Caminho**: `~/.config/achilles/config.json`
**Formato**: JSON objeto
**Campos**:
```json
{
  "pasta_monitorada": "~/Downloads",
  "auto_delete": true,
  "repacks_ja_vistos": ["/caminho/do/repack"]
}
```

### Logs de Instalação
**Caminho**: `~/.config/achilles/logs/{exe}_{timestamp}.log`
**Formato**: Texto plano com cabeçalho (data, comando, wineprefix, winedebug) e output completo do Wine
