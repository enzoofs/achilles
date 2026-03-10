# Carta do Projeto — Achilles

## Visão
Ser o gerenciador de jogos definitivo para Linux, focado em repacks e jogos que não estão na Steam. Combina instalação via Wine/Proton com uma biblioteca organizada, monitoramento inteligente e interface moderna.

## Problema Resolvido
Instalar repacks (FitGirl, etc.) no Linux é um processo manual e propenso a erros:
- Requer variáveis de ambiente específicas (`DISPLAY`, `WINEPREFIX`, `WINEDEBUG`)
- Instalações podem travar sem indicação visual
- Não há forma fácil de saber se Wine ou Proton é melhor
- Gerenciar múltiplos jogos com WINEPREFIXes diferentes é confuso

## Critérios de Sucesso
1. Instalar qualquer repack com 3 cliques (selecionar pasta → instalar → adicionar à biblioteca)
2. Detectar automaticamente se uma instalação travou
3. Recomendar o melhor runtime (Wine vs Proton-GE) sem que o usuário precise pesquisar
4. Organizar jogos em uma interface visual com tempo jogado

## Escopo

### Dentro do Escopo
- Instalação de jogos via Wine/Proton a partir de repacks
- Biblioteca de jogos com launch, tempo jogado, tags
- Monitoramento de instalação (CPU, I/O, chunks)
- Detecção automática de instaladores na pasta de downloads
- Debug automático de instalações com log persistente
- Detecção e recomendação de runtimes
- Configuração por jogo (WINEPREFIX, runtime, argumentos)

### Fora do Escopo (por enquanto)
- Download de jogos (inspirado no Hydra, mas não implementado ainda)
- Integração com Steam para jogos Steam
- Cloud save / sincronização
- Suporte a outras distros além de Arch Linux

## Stakeholders
- **Usuário principal**: Enzo (gamer no Arch Linux com Hyprland + NVIDIA GTX 1650)
- **Público alvo**: Gamers Linux que usam repacks e querem uma experiência integrada

## Restrições Técnicas
- Arch Linux com Hyprland (Wayland) — requer XWayland para Wine
- NVIDIA com drivers proprietários
- Python 3 com venv (PEP 668 do Arch bloqueia pip global)
- Sem dependências pesadas (sem Qt, sem Electron)
