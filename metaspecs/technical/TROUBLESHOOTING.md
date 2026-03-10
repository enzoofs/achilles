# Solução de Problemas — Achilles

## Erros na Inicialização

### ImportError: libtk8.6.so not found
**Causa**: Pacote `tk` não instalado no Arch Linux
**Solução**:
```bash
sudo pacman -S tk
```

### ModuleNotFoundError: customtkinter
**Causa**: Venv não existe ou customtkinter não instalado
**Solução**:
```bash
cd /home/enzof/projetos/achilles
python -m venv .venv
.venv/bin/pip install customtkinter
```

### error: externally-managed-environment (PEP 668)
**Causa**: Tentando instalar pip package globalmente no Arch
**Solução**: Usar venv (já configurado em `.venv/`)

## Erros durante Instalação de Jogos

### "Erro de display. Verifique se o XWayland está ativo."
**Causa**: Wine não encontra display X11. XWayland pode não estar rodando.
**Solução**:
1. Verificar se XWayland está ativo: `pgrep Xwayland`
2. Se não: reiniciar Hyprland ou verificar config do Hyprland
3. Testar manualmente: `DISPLAY=:0 wine --version`

### "FreeType não encontrado"
**Causa**: Bibliotecas de fontes faltando
**Solução**:
```bash
sudo pacman -S freetype2 lib32-freetype2
```

### "Arquivo não encontrado ou caminho inválido" (c0000135)
**Causa**: DLL faltando ou caminho com caracteres especiais
**Solução**:
1. Verificar se o caminho não tem acentos ou espaços problemáticos
2. Tentar rodar `winetricks` no prefix: `WINEPREFIX=~/.local/share/achilles/prefixes/slug winetricks`

### Instalação travou (SEM ATIVIDADE)
**Causa**: Unpacking de chunks pode demorar muito (especialmente `re_chunk_000.pak` em jogos grandes)
**Diagnóstico**:
1. Verificar o indicador de status no Achilles
2. Se "SEM ATIVIDADE" por mais de 5 minutos, pode estar travado
3. Abrir o log completo (botão "Ver log") e verificar última linha
4. Verificar CPU com `htop` — processo wine deve usar CPU
**Solução**:
1. Usar botão "Forçar parada" no Achilles
2. Deletar o WINEPREFIX e tentar novamente
3. Verificar se tem espaço em disco suficiente

### Log mostra "fixme:ntdll:..." repetidamente
**Causa**: Normal. São avisos de funcionalidades Wine não implementadas.
**Ação**: Ignorar. O filtro do Achilles já esconde a maioria dessas linhas na UI.

## Erros na Biblioteca

### "Executável não encontrado" (nome em vermelho)
**Causa**: O .exe do jogo foi movido ou deletado
**Solução**: Clicar em "Config" no card do jogo e atualizar o caminho do executável

### Jogo não abre (fecha imediatamente)
**Causa**: Prefix corrompido, DLLs faltando, ou runtime errado
**Solução**:
1. Tentar trocar runtime nas propriedades (Wine → Proton-GE ou vice-versa)
2. Deletar o WINEPREFIX do jogo e criar novo (jogo instalado persiste)
3. Verificar se precisa de winetricks: `WINEPREFIX=... winetricks`
4. Verificar log da sessão anterior

## Problemas de Interface

### TclError: invalid command name
**Causa**: Widget foi destruído mas um binding ainda aponta pra ele
**Solução**: Já corrigido — usar `widget.bind()` ao invés de `widget.bind_all()`

### Achilles não aparece no rofi
**Causa**: Desktop entry faltando ou com caminho errado
**Solução**: Verificar se `~/.local/share/applications/achilles.desktop` existe com o Exec correto

## Debug Geral

### Ver logs de instalação
```bash
ls ~/.config/achilles/logs/
cat ~/.config/achilles/logs/setup_YYYYMMDD_HHMMSS.log
```

### Testar Wine manualmente
```bash
DISPLAY=:0 WINEPREFIX=~/.local/share/achilles/prefixes/meu-jogo WINEDEBUG=+file,+loaddll,+seh wine "/caminho/setup.exe" 2>&1 | tee ~/debug.log
```

### Resetar configuração do Achilles
```bash
rm ~/.config/achilles/config.json
rm ~/.config/achilles/biblioteca.json
```

### Limpar prefix de um jogo
```bash
rm -rf ~/.local/share/achilles/prefixes/nome-do-jogo/
```
