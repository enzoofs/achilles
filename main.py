#!/usr/bin/env python3
"""
Achilles — Game Manager para Arch Linux
Instala, organiza e lanca jogos via Wine/Proton.
"""

import customtkinter as ctk
from tkinter import filedialog
import subprocess
import threading
import queue
import shutil
import os
import re
import json
import time
import glob as globmod
from datetime import datetime

# ============================================================
# Tema — Catppuccin Mocha
# ============================================================
CORES = {
    "base":       "#1e1e2e",
    "mantle":     "#181825",
    "crust":      "#11111b",
    "surface0":   "#313244",
    "surface1":   "#45475a",
    "surface2":   "#585b70",
    "overlay0":   "#6c7086",
    "text":       "#cdd6f4",
    "subtext0":   "#a6adc8",
    "subtext1":   "#bac2de",
    "lavender":   "#b4befe",
    "blue":       "#89b4fa",
    "sapphire":   "#74c7ec",
    "green":      "#a6e3a1",
    "yellow":     "#f9e2af",
    "peach":      "#fab387",
    "red":        "#f38ba8",
    "pink":       "#f5c2e7",
    "mauve":      "#cba6f7",
}

# Caminhos
PASTA_CONFIG = os.path.expanduser("~/.config/achilles")
PASTA_PREFIXES = os.path.expanduser("~/.local/share/achilles/prefixes")
ARQUIVO_BIBLIOTECA = os.path.join(PASTA_CONFIG, "biblioteca.json")
ARQUIVO_CONFIG = os.path.join(PASTA_CONFIG, "config.json")

CONFIG_PADRAO = {
    "pasta_monitorada": os.path.expanduser("~/Downloads"),
    "auto_delete": True,
    "repacks_ja_vistos": [],
}

ERROS_CONHECIDOS = {
    r"no driver could be loaded": "Erro de display. Verifique se o XWayland esta ativo.",
    r"FreeType font library": "FreeType nao encontrado. Rode: sudo pacman -S freetype2 lib32-freetype2",
    r"c0000135": "Arquivo nao encontrado ou caminho invalido.",
}

# Nomes comuns de instaladores (case insensitive)
NOMES_INSTALADOR = [
    "setup.exe", "install.exe", "installer.exe", "setup-*.exe",
    "autorun.exe", "start.exe",
]


# ============================================================
# Backend: Detector de runtime (Wine vs Proton)
# ============================================================
class DetectorRuntime:
    """Detecta Wine e Proton instalados e recomenda o melhor pro usuario."""

    @staticmethod
    def detectar_wine():
        """Retorna info sobre o Wine instalado."""
        caminho = shutil.which("wine")
        if not caminho:
            return None
        try:
            r = subprocess.run(["wine", "--version"], capture_output=True, text=True, timeout=5)
            versao = r.stdout.strip()
        except Exception:
            versao = "desconhecida"
        return {"tipo": "wine", "caminho": caminho, "versao": versao}

    @staticmethod
    def detectar_proton():
        """Procura Proton instalado via Steam ou standalone."""
        resultados = []

        # Proton do Steam (compatibilitytools.d)
        locais_steam = [
            os.path.expanduser("~/.steam/root/compatibilitytools.d"),
            os.path.expanduser("~/.local/share/Steam/compatibilitytools.d"),
            os.path.expanduser("~/.steam/steam/compatibilitytools.d"),
        ]
        for local in locais_steam:
            if os.path.isdir(local):
                for item in os.listdir(local):
                    proton_exe = os.path.join(local, item, "proton")
                    if os.path.isfile(proton_exe):
                        resultados.append({
                            "tipo": "proton",
                            "nome": item,
                            "caminho": proton_exe,
                            "origem": "Steam (custom)",
                        })

        # Proton oficial do Steam
        locais_proton_oficial = [
            os.path.expanduser("~/.steam/root/steamapps/common"),
            os.path.expanduser("~/.local/share/Steam/steamapps/common"),
        ]
        for local in locais_proton_oficial:
            if os.path.isdir(local):
                for item in os.listdir(local):
                    if "proton" in item.lower():
                        proton_exe = os.path.join(local, item, "proton")
                        if os.path.isfile(proton_exe):
                            resultados.append({
                                "tipo": "proton",
                                "nome": item,
                                "caminho": proton_exe,
                                "origem": "Steam (oficial)",
                            })

        # Proton-GE standalone
        ge_path = os.path.expanduser("~/.local/share/Steam/compatibilitytools.d")
        if os.path.isdir(ge_path):
            for item in os.listdir(ge_path):
                if "ge" in item.lower() or "GE" in item:
                    proton_exe = os.path.join(ge_path, item, "proton")
                    if os.path.isfile(proton_exe):
                        # Evita duplicatas
                        if not any(r["caminho"] == proton_exe for r in resultados):
                            resultados.append({
                                "tipo": "proton-ge",
                                "nome": item,
                                "caminho": proton_exe,
                                "origem": "Proton-GE",
                            })

        return resultados

    @staticmethod
    def recomendar():
        """Retorna recomendação de qual runtime usar e por quê."""
        wine = DetectorRuntime.detectar_wine()
        protons = DetectorRuntime.detectar_proton()

        recomendacao = {
            "wine": wine,
            "protons": protons,
            "recomendado": None,
            "motivo": "",
        }

        # Proton-GE é geralmente a melhor opcao pra jogos
        ge = [p for p in protons if p["tipo"] == "proton-ge"]
        oficial = [p for p in protons if p["tipo"] == "proton"]

        if ge:
            recomendacao["recomendado"] = ge[0]
            recomendacao["motivo"] = (
                "Proton-GE tem patches extras para jogos que o Wine nao tem: "
                "melhor compatibilidade com anti-cheat, codecs de video (cutscenes), "
                "e correcoes especificas de jogos. Recomendado para a maioria dos jogos."
            )
        elif oficial:
            recomendacao["recomendado"] = oficial[0]
            recomendacao["motivo"] = (
                "Proton oficial da Valve. Boa compatibilidade geral, "
                "mas Proton-GE costuma ter suporte melhor para jogos fora da Steam."
            )
        elif wine:
            recomendacao["recomendado"] = wine
            recomendacao["motivo"] = (
                "Wine puro. Funciona para instalacao de repacks, "
                "mas para jogar, Proton-GE geralmente tem melhor desempenho. "
                "Instale com: yay -S proton-ge-custom-bin"
            )
        else:
            recomendacao["motivo"] = (
                "Nenhum runtime encontrado. Instale Wine ou Proton:\n"
                "sudo pacman -S wine-staging winetricks\n"
                "ou: yay -S proton-ge-custom-bin"
            )

        return recomendacao


# ============================================================
# Backend: Biblioteca
# ============================================================
class Biblioteca:
    def __init__(self):
        self.jogos = []
        self._carregar()

    def _carregar(self):
        if os.path.exists(ARQUIVO_BIBLIOTECA):
            try:
                with open(ARQUIVO_BIBLIOTECA, "r", encoding="utf-8") as f:
                    self.jogos = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.jogos = []
        # Garante campos novos em jogos antigos
        for jogo in self.jogos:
            jogo.setdefault("runtime", "wine")
            jogo.setdefault("wineprefix", "")
            jogo.setdefault("tempo_jogado", 0)
            jogo.setdefault("ultima_sessao", "")
            jogo.setdefault("tags", [])
            jogo.setdefault("args", "")

    def _salvar(self):
        os.makedirs(PASTA_CONFIG, exist_ok=True)
        with open(ARQUIVO_BIBLIOTECA, "w", encoding="utf-8") as f:
            json.dump(self.jogos, f, indent=2, ensure_ascii=False)

    def adicionar(self, nome, exe_path, pasta_instalacao="", runtime="wine",
                  wineprefix="", tags=None):
        # Cria prefix isolado se nao especificado
        if not wineprefix:
            slug = re.sub(r"[^a-zA-Z0-9]", "-", nome.lower()).strip("-")
            wineprefix = os.path.join(PASTA_PREFIXES, slug)

        jogo = {
            "nome": nome,
            "exe": exe_path,
            "pasta": pasta_instalacao or os.path.dirname(exe_path),
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "runtime": runtime,
            "wineprefix": wineprefix,
            "tempo_jogado": 0,
            "ultima_sessao": "",
            "tags": tags or [],
            "args": "",
        }
        self.jogos.append(jogo)
        self._salvar()
        return jogo

    def remover(self, indice):
        if 0 <= indice < len(self.jogos):
            self.jogos.pop(indice)
            self._salvar()

    def editar(self, indice, **campos):
        if 0 <= indice < len(self.jogos):
            for k, v in campos.items():
                if v is not None:
                    self.jogos[indice][k] = v
            self._salvar()

    def registrar_sessao(self, indice, duracao_seg):
        """Registra tempo jogado e data da ultima sessao."""
        if 0 <= indice < len(self.jogos):
            self.jogos[indice]["tempo_jogado"] += duracao_seg
            self.jogos[indice]["ultima_sessao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._salvar()

    @staticmethod
    def formatar_tempo_jogado(segundos):
        if segundos < 60:
            return "< 1 min"
        horas = segundos / 3600
        if horas < 1:
            return f"{int(segundos / 60)} min"
        return f"{horas:.1f}h"


# ============================================================
# Backend: Configuração
# ============================================================
class Configuracao:
    def __init__(self):
        self.dados = dict(CONFIG_PADRAO)
        self._carregar()

    def _carregar(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
                    self.dados.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass

    def salvar(self):
        os.makedirs(PASTA_CONFIG, exist_ok=True)
        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=2, ensure_ascii=False)

    def get(self, chave):
        return self.dados.get(chave, CONFIG_PADRAO.get(chave))

    def set(self, chave, valor):
        self.dados[chave] = valor
        self.salvar()


# ============================================================
# Backend: Detector de instaladores
# ============================================================
class DetectorInstaladores:
    """Monitora pasta e detecta instaladores (nao so FitGirl)."""

    def __init__(self, config):
        self.config = config

    def escanear(self):
        pasta = self.config.get("pasta_monitorada")
        if not pasta or not os.path.isdir(pasta):
            return []
        ja_vistos = set(self.config.get("repacks_ja_vistos") or [])
        encontrados = []
        try:
            for item in os.listdir(pasta):
                caminho = os.path.join(pasta, item)
                if not os.path.isdir(caminho):
                    continue
                instalador = self._encontrar_instalador(caminho)
                if instalador and caminho not in ja_vistos:
                    encontrados.append({
                        "nome": item,
                        "caminho": caminho,
                        "instalador": instalador,
                    })
        except PermissionError:
            pass
        return encontrados

    def _encontrar_instalador(self, pasta):
        """Procura executáveis de instalação dentro da pasta."""
        try:
            arquivos = os.listdir(pasta)
        except PermissionError:
            return None

        arquivos_lower = {f.lower(): f for f in arquivos if os.path.isfile(os.path.join(pasta, f))}

        # Checa patterns conhecidos
        for pattern in NOMES_INSTALADOR:
            if "*" in pattern:
                # Glob pattern
                matches = globmod.glob(os.path.join(pasta, pattern))
                if matches:
                    return matches[0]
            else:
                if pattern in arquivos_lower:
                    return os.path.join(pasta, arquivos_lower[pattern])

        # Fallback: qualquer .exe na raiz da pasta
        exes = [f for f in arquivos if f.lower().endswith(".exe")
                and os.path.isfile(os.path.join(pasta, f))]
        if len(exes) == 1:
            return os.path.join(pasta, exes[0])

        return None

    def marcar_como_visto(self, caminho):
        vistos = self.config.get("repacks_ja_vistos") or []
        if caminho not in vistos:
            vistos.append(caminho)
            self.config.set("repacks_ja_vistos", vistos)

    @staticmethod
    def calcular_tamanho(pasta):
        total = 0
        try:
            for dp, _, fns in os.walk(pasta):
                for f in fns:
                    try:
                        total += os.path.getsize(os.path.join(dp, f))
                    except OSError:
                        pass
        except PermissionError:
            pass
        return total

    @staticmethod
    def formatar_tamanho(n):
        if n < 1024 ** 2: return f"{n / 1024:.1f} KB"
        if n < 1024 ** 3: return f"{n / (1024 ** 2):.1f} MB"
        return f"{n / (1024 ** 3):.1f} GB"


# ============================================================
# Backend: Verificador de dependências
# ============================================================
class VerificadorDependencias:
    DEPS = ["wine", "winetricks"]

    @staticmethod
    def faltando():
        return [d for d in VerificadorDependencias.DEPS if shutil.which(d) is None]


# ============================================================
# Backend: Executor Wine/Proton
# ============================================================
class ExecutorWine:
    # Modo debug: mostra operacoes de arquivo e DLLs carregadas
    # Modo silencioso: suprime tudo (pra jogar sem poluir log)
    WINEDEBUG_INSTALL = "+file,+loaddll,+seh"
    WINEDEBUG_PLAY = "-all"

    def __init__(self, caminho_exe, fila_log, callback_fim=None,
                 wineprefix=None, runtime="wine", proton_path=None,
                 args="", modo="install"):
        self.caminho_exe = caminho_exe
        self.fila_log = fila_log
        self.callback_fim = callback_fim
        self.wineprefix = wineprefix or os.path.expanduser("~/.wine")
        self.runtime = runtime
        self.proton_path = proton_path
        self.args = args
        self.modo = modo  # "install" ou "play"
        self.processo = None
        self.inicio = None
        self.arquivo_log = None
        self.log_path = None

    def iniciar(self):
        self.inicio = time.time()
        threading.Thread(target=self._executar, daemon=True).start()

    def tempo_decorrido(self):
        if self.inicio:
            return time.time() - self.inicio
        return 0

    def _executar(self):
        env = os.environ.copy()
        env["DISPLAY"] = ":0"

        # Debug durante instalacao, silencioso ao jogar
        if self.modo == "install":
            env["WINEDEBUG"] = self.WINEDEBUG_INSTALL
            self.fila_log.put(("info", "Modo: INSTALACAO (debug Wine ativo)"))
        else:
            env["WINEDEBUG"] = self.WINEDEBUG_PLAY
            self.fila_log.put(("info", "Modo: JOGO (debug Wine desativado)"))

        # Cria o prefix se nao existir
        os.makedirs(self.wineprefix, exist_ok=True)
        env["WINEPREFIX"] = self.wineprefix

        if self.runtime in ("proton", "proton-ge") and self.proton_path:
            cmd = [self.proton_path, "run", self.caminho_exe]
            env["STEAM_COMPAT_DATA_PATH"] = self.wineprefix
            env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = os.path.expanduser("~/.steam/steam")
            self.fila_log.put(("info", f"Runtime: Proton ({os.path.basename(os.path.dirname(self.proton_path))})"))
        else:
            cmd = ["wine", self.caminho_exe]
            self.fila_log.put(("info", "Runtime: Wine"))

        if self.args:
            cmd.extend(self.args.split())

        self.fila_log.put(("info", f"Executando: {' '.join(cmd)}"))
        self.fila_log.put(("info", f"WINEPREFIX: {self.wineprefix}"))

        # Abre arquivo de log pra instalacoes
        if self.modo == "install":
            os.makedirs(os.path.join(PASTA_CONFIG, "logs"), exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_exe = os.path.basename(self.caminho_exe).replace(".exe", "")
            log_path = os.path.join(PASTA_CONFIG, "logs", f"{nome_exe}_{timestamp}.log")
            self.log_path = log_path
            self.arquivo_log = open(log_path, "w", encoding="utf-8")
            self.fila_log.put(("info", f"Log salvo em: {log_path}"))
            self.arquivo_log.write(f"Achilles — Log de instalacao\n")
            self.arquivo_log.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.arquivo_log.write(f"Comando: {' '.join(cmd)}\n")
            self.arquivo_log.write(f"WINEPREFIX: {self.wineprefix}\n")
            self.arquivo_log.write(f"WINEDEBUG: {env['WINEDEBUG']}\n")
            self.arquivo_log.write("=" * 60 + "\n\n")

        self.fila_log.put(("info", ""))

        codigo = -1
        try:
            self.processo = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, text=True, bufsize=1,
            )

            def ler(stream, tipo):
                for linha in stream:
                    linha = linha.rstrip("\n")
                    if not linha:
                        continue

                    # Salva no arquivo de log
                    if self.arquivo_log:
                        try:
                            self.arquivo_log.write(linha + "\n")
                            self.arquivo_log.flush()
                        except Exception:
                            pass

                    # Classifica a linha pra exibicao
                    t = tipo
                    for padrao, msg in ERROS_CONHECIDOS.items():
                        if re.search(padrao, linha, re.IGNORECASE):
                            self.fila_log.put(("erro_conhecido", msg))
                            t = "erro"
                            break

                    # No modo debug, filtra linhas muito verbosas pro log visual
                    # mas salva tudo no arquivo
                    if self.modo == "install" and tipo == "aviso":
                        ll = linha.lower()
                        # Mostra apenas linhas relevantes na UI
                        if any(k in ll for k in [
                            "err:", "error", "warn:", "fixme:",
                            "critical", "fail", "exception",
                            "chunk", ".pak", "extract", "decompress",
                            "unpack", "write", "create", "open",
                            "loaddll", "loading", "loaded",
                        ]):
                            self.fila_log.put((t, linha))
                        # Linhas de debug puras vao so pro arquivo
                    else:
                        self.fila_log.put((t, linha))

            t1 = threading.Thread(target=ler, args=(self.processo.stdout, "info"), daemon=True)
            t2 = threading.Thread(target=ler, args=(self.processo.stderr, "aviso"), daemon=True)
            t1.start(); t2.start()
            self.processo.wait()
            t1.join(timeout=5); t2.join(timeout=5)
            codigo = self.processo.returncode

        except FileNotFoundError:
            self.fila_log.put(("erro", "Runtime nao encontrado. Verifique a instalacao."))
        except Exception as e:
            self.fila_log.put(("erro", f"Erro inesperado: {e}"))

        # Fecha arquivo de log
        if self.arquivo_log:
            try:
                self.arquivo_log.write(f"\n{'=' * 60}\n")
                self.arquivo_log.write(f"Codigo de saida: {codigo}\n")
                self.arquivo_log.write(f"Duracao: {int(self.tempo_decorrido())}s\n")
                self.arquivo_log.close()
            except Exception:
                pass
            self.arquivo_log = None

        self.fila_log.put(("fim", codigo))
        if self.callback_fim:
            self.callback_fim(codigo)


# ============================================================
# Backend: Monitor de processo
# ============================================================
class MonitorProcesso:
    TEMPO_AVISO = 120

    def __init__(self, executor, pasta_repack=None):
        self.executor = executor
        self.pasta_repack = pasta_repack
        self.inicio = time.time()
        self.ativo = True
        self._cpu_ant = 0
        self._io_ant = 0
        self._ultima_atividade = time.time()
        self._avisou = False
        self.total_chunks = 0
        self.chunk_atual = -1
        self._mapear_chunks()

    def _mapear_chunks(self):
        if not self.pasta_repack or not os.path.isdir(self.pasta_repack):
            return
        self.total_chunks = len([
            f for f in os.listdir(self.pasta_repack)
            if re.match(r"re_chunk_\d+\.pak", f, re.IGNORECASE)
        ])

    def _ler_cpu(self, pid):
        try:
            with open(f"/proc/{pid}/stat") as f:
                c = f.read().split(")")[-1].split()
                return int(c[11]) + int(c[12])
        except Exception:
            return None

    def _ler_io(self, pid):
        try:
            with open(f"/proc/{pid}/io") as f:
                for l in f:
                    if l.startswith("write_bytes:"):
                        return int(l.split()[1])
        except Exception:
            return None

    def _arvore(self, pid):
        cpu = self._ler_cpu(pid) or 0
        io = self._ler_io(pid) or 0
        try:
            with open(f"/proc/{pid}/task/{pid}/children") as f:
                for fp in f.read().split():
                    c, i = self._arvore(int(fp))
                    cpu += c; io += i
        except Exception:
            pass
        return cpu, io

    def _chunk_aberto(self, pid):
        melhor = -1
        pids = [pid]
        try:
            with open(f"/proc/{pid}/task/{pid}/children") as f:
                pids.extend(int(p) for p in f.read().split())
        except Exception:
            pass
        for p in pids:
            try:
                for fd in os.listdir(f"/proc/{p}/fd"):
                    try:
                        link = os.readlink(f"/proc/{p}/fd/{fd}")
                        m = re.search(r"re_chunk_(\d+)\.pak", link, re.IGNORECASE)
                        if m:
                            melhor = max(melhor, int(m.group(1)))
                    except OSError:
                        pass
            except Exception:
                pass
        return melhor

    def formatar_tempo(self, s):
        s = int(s)
        h, r = divmod(s, 3600)
        m, seg = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{seg:02d}" if h else f"{m:02d}:{seg:02d}"

    def formatar_bytes(self, n):
        if n < 1024: return f"{n} B"
        if n < 1024**2: return f"{n/1024:.1f} KB"
        if n < 1024**3: return f"{n/1024**2:.1f} MB"
        return f"{n/1024**3:.2f} GB"

    def atualizar(self):
        if not self.ativo:
            return None
        pid = self.executor.processo.pid if self.executor and self.executor.processo else None
        if not pid:
            return None

        tempo = time.time() - self.inicio
        cpu, io = self._arvore(pid)
        dc = cpu - self._cpu_ant
        di = io - self._io_ant

        if dc > 0 or di > 0:
            self._ultima_atividade = time.time()
            self._avisou = False

        inativo = time.time() - self._ultima_atividade
        self._cpu_ant = cpu
        self._io_ant = io

        if inativo > self.TEMPO_AVISO:
            status = "travado"
            if not self._avisou:
                self._avisou = True
        elif dc > 0 or di > 0:
            status = "ativo"
        else:
            status = "aguardando"

        progresso = None
        if self.total_chunks > 0:
            c = self._chunk_aberto(pid)
            if c >= 0:
                self.chunk_atual = c
                progresso = ((self.chunk_atual + 1) / self.total_chunks) * 100

        return {
            "tempo": self.formatar_tempo(tempo),
            "io_total": self.formatar_bytes(io),
            "io_delta": self.formatar_bytes(di),
            "inativo": int(inativo),
            "status": status,
            "progresso": progresso,
            "chunk": self.chunk_atual + 1 if self.chunk_atual >= 0 else 0,
            "total_chunks": self.total_chunks,
        }

    def parar(self):
        self.ativo = False


# ============================================================
# GUI — App principal
# ============================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Achilles")
        self.geometry("920x640")
        self.minsize(780, 540)
        self.configure(fg_color=CORES["base"])
        ctk.set_appearance_mode("dark")

        # Estado
        self.config = Configuracao()
        self.biblioteca = Biblioteca()
        self.detector = DetectorInstaladores(self.config)
        self.runtime_info = DetectorRuntime.recomendar()
        self.caminho_pasta = None
        self.caminho_setup = None
        self.fila_log = queue.Queue()
        self.executor = None
        self.instalando = False
        self.monitor = None
        self.repacks_pendentes = []
        self.jogo_jogando_idx = None  # indice do jogo sendo jogado (pra tempo)

        # Layout
        self._criar_sidebar()
        self._criar_area_conteudo()
        self._mostrar_pagina("biblioteca")

        self.after(100, self._processar_fila)
        self.after(3000, self._escanear_downloads)

    # ============================================================
    # Sidebar
    # ============================================================
    def _criar_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=CORES["mantle"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        frame_logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame_logo.pack(fill="x", padx=20, pady=(24, 8))

        ctk.CTkLabel(
            frame_logo, text="ACHILLES",
            font=ctk.CTkFont(family="sans-serif", size=22, weight="bold"),
            text_color=CORES["lavender"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame_logo, text="Game Manager",
            font=ctk.CTkFont(size=11), text_color=CORES["overlay0"],
        ).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=CORES["surface0"]).pack(fill="x", padx=16, pady=16)

        self.nav_botoes = {}
        for pid, label in [("biblioteca", "Biblioteca"), ("instalar", "Instalar"),
                           ("runtime", "Wine / Proton"), ("config", "Configuracoes")]:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent", text_color=CORES["subtext0"],
                hover_color=CORES["surface0"], height=38, corner_radius=8,
                command=lambda p=pid: self._mostrar_pagina(p),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_botoes[pid] = btn

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Banner de detecção
        self.frame_banner = ctk.CTkFrame(self.sidebar, fg_color=CORES["surface0"], corner_radius=8)
        self.label_banner = ctk.CTkLabel(
            self.frame_banner, text="", font=ctk.CTkFont(size=11),
            text_color=CORES["blue"], wraplength=160,
        )
        self.label_banner.pack(padx=10, pady=(10, 4))
        ctk.CTkButton(
            self.frame_banner, text="Instalar",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=CORES["blue"], text_color=CORES["crust"],
            hover_color=CORES["sapphire"], height=28, corner_radius=6,
            command=self._instalar_detectado,
        ).pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(
            self.frame_banner, text="Ignorar", font=ctk.CTkFont(size=10),
            fg_color="transparent", text_color=CORES["overlay0"],
            hover_color=CORES["surface1"], height=24, corner_radius=6,
            command=self._ignorar_detectado,
        ).pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(
            self.sidebar, text="v2.0 — Arch Linux",
            font=ctk.CTkFont(size=9), text_color=CORES["surface2"],
        ).pack(pady=(8, 16))

    # ============================================================
    # Conteúdo
    # ============================================================
    def _criar_area_conteudo(self):
        self.conteudo = ctk.CTkFrame(self, fg_color=CORES["base"], corner_radius=0)
        self.conteudo.pack(side="right", fill="both", expand=True)

    def _mostrar_pagina(self, nome):
        for pid, btn in self.nav_botoes.items():
            if pid == nome:
                btn.configure(fg_color=CORES["surface0"], text_color=CORES["lavender"],
                              font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=CORES["subtext0"],
                              font=ctk.CTkFont(size=13))

        for w in self.conteudo.winfo_children():
            w.destroy()

        {"biblioteca": self._pag_biblioteca, "instalar": self._pag_instalar,
         "runtime": self._pag_runtime, "config": self._pag_config}.get(nome, lambda: None)()

    # ============================================================
    # Página: Biblioteca
    # ============================================================
    def _pag_biblioteca(self):
        header = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))

        ctk.CTkLabel(header, text="Meus Jogos",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=CORES["text"]).pack(side="left")
        ctk.CTkButton(
            header, text="+ Adicionar jogo", width=130,
            font=ctk.CTkFont(size=12), fg_color=CORES["surface0"],
            text_color=CORES["subtext1"], hover_color=CORES["surface1"],
            height=32, corner_radius=8, command=self._adicionar_jogo_manual,
        ).pack(side="right")

        jogos = self.biblioteca.jogos

        if not jogos:
            vazio = ctk.CTkFrame(self.conteudo, fg_color="transparent")
            vazio.pack(expand=True)
            ctk.CTkLabel(vazio, text="Nenhum jogo na biblioteca",
                         font=ctk.CTkFont(size=16), text_color=CORES["overlay0"]).pack()
            ctk.CTkLabel(vazio, text="Instale um jogo ou adicione manualmente",
                         font=ctk.CTkFont(size=12), text_color=CORES["surface2"]).pack(pady=(4, 0))
            return

        lista = ctk.CTkScrollableFrame(
            self.conteudo, fg_color="transparent",
            scrollbar_button_color=CORES["surface1"],
            scrollbar_button_hover_color=CORES["surface2"],
        )
        lista.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        for i, jogo in enumerate(jogos):
            self._card_jogo(lista, jogo, i)

    def _card_jogo(self, parent, jogo, indice):
        # Cor do accent baseada no runtime
        cor_accent = CORES["mauve"]
        if jogo.get("runtime") in ("proton", "proton-ge"):
            cor_accent = CORES["sapphire"]

        # Status do exe
        exe_existe = os.path.exists(jogo["exe"])

        card = ctk.CTkFrame(parent, fg_color=CORES["surface0"], corner_radius=12, height=90)
        card.pack(fill="x", pady=(0, 8))
        card.pack_propagate(False)

        # Accent bar
        ctk.CTkFrame(card, width=4, corner_radius=2, fg_color=cor_accent).pack(
            side="left", fill="y", padx=(12, 0), pady=12)

        # Info
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(12, 8), pady=10)

        # Linha do titulo com status
        titulo_row = ctk.CTkFrame(info, fg_color="transparent")
        titulo_row.pack(fill="x")

        ctk.CTkLabel(
            titulo_row, text=jogo["nome"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["text"] if exe_existe else CORES["red"],
            anchor="w",
        ).pack(side="left")

        # Badge de runtime
        rt = jogo.get("runtime", "wine")
        rt_label = "Wine" if rt == "wine" else "Proton"
        ctk.CTkLabel(
            titulo_row, text=rt_label,
            font=ctk.CTkFont(size=9),
            text_color=CORES["overlay0"],
            fg_color=CORES["surface1"],
            corner_radius=4, padx=6,
        ).pack(side="left", padx=(8, 0))

        # Tags
        for tag in jogo.get("tags", []):
            ctk.CTkLabel(
                titulo_row, text=tag,
                font=ctk.CTkFont(size=9),
                text_color=CORES["mauve"],
                fg_color=CORES["base"],
                corner_radius=4, padx=6,
            ).pack(side="left", padx=(4, 0))

        # Info secundaria
        tempo = Biblioteca.formatar_tempo_jogado(jogo.get("tempo_jogado", 0))
        ultima = jogo.get("ultima_sessao", "")
        sub_texto = f"{tempo} jogado"
        if ultima:
            sub_texto += f"  |  Ultimo: {ultima}"
        if not exe_existe:
            sub_texto = "Executavel nao encontrado"

        ctk.CTkLabel(
            info, text=sub_texto,
            font=ctk.CTkFont(size=10), text_color=CORES["overlay0"], anchor="w",
        ).pack(fill="x")

        # Botoes
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=16, pady=10)

        ctk.CTkButton(
            btns, text="Jogar", width=80,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CORES["green"] if exe_existe else CORES["surface1"],
            text_color=CORES["crust"], hover_color="#8bd18b",
            height=34, corner_radius=8,
            state="normal" if exe_existe else "disabled",
            command=lambda j=jogo, i=indice: self._jogar(j, i),
        ).pack(pady=(0, 4))

        frame_sub = ctk.CTkFrame(btns, fg_color="transparent")
        frame_sub.pack()

        ctk.CTkButton(
            frame_sub, text="Config", width=40,
            font=ctk.CTkFont(size=10), fg_color="transparent",
            text_color=CORES["overlay0"], hover_color=CORES["surface1"], height=22,
            command=lambda idx=indice: self._config_jogo(idx),
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            frame_sub, text="Remover", width=46,
            font=ctk.CTkFont(size=10), fg_color="transparent",
            text_color=CORES["red"], hover_color=CORES["surface1"], height=22,
            command=lambda idx=indice: self._remover_jogo(idx),
        ).pack(side="left")

    # ---------- Acoes da biblioteca ----------
    def _jogar(self, jogo, indice):
        exe = jogo["exe"]
        if not os.path.exists(exe):
            return

        self.jogo_jogando_idx = indice
        self._mostrar_pagina("instalar")
        self._log("info", f"Iniciando {jogo['nome']}...")

        # Seleciona runtime
        proton_path = None
        rt = jogo.get("runtime", "wine")
        if rt in ("proton", "proton-ge"):
            protons = DetectorRuntime.detectar_proton()
            if protons:
                proton_path = protons[0]["caminho"]
                self._log("info", f"Usando Proton: {protons[0]['nome']}")
            else:
                self._log("aviso", "Proton nao encontrado, usando Wine")
                rt = "wine"

        executor = ExecutorWine(
            caminho_exe=exe, fila_log=self.fila_log,
            wineprefix=jogo.get("wineprefix", ""),
            runtime=rt, proton_path=proton_path,
            args=jogo.get("args", ""),
            modo="play",
            callback_fim=lambda rc: self.after(0, lambda: self._jogo_fim(jogo["nome"], indice, rc)),
        )
        executor.iniciar()
        self.executor = executor

    def _jogo_fim(self, nome, indice, rc):
        # Registra tempo jogado
        if self.executor and self.executor.inicio:
            duracao = int(self.executor.tempo_decorrido())
            if duracao > 10:  # ignora sessoes < 10s
                self.biblioteca.registrar_sessao(indice, duracao)
                tempo_fmt = Biblioteca.formatar_tempo_jogado(duracao)
                self._log("info", f"Sessao: {tempo_fmt}")

        self.jogo_jogando_idx = None
        if rc == 0:
            self._log("sucesso", f"{nome} encerrado normalmente.")
        else:
            self._log("aviso", f"{nome} encerrado com codigo {rc}")

    def _adicionar_jogo_manual(self):
        exe = filedialog.askopenfilename(
            title="Selecione o executavel do jogo (.exe)",
            filetypes=[("Executaveis", "*.exe *.EXE"), ("Todos", "*.*")],
            initialdir=os.path.expanduser("~/.wine/drive_c/"),
        )
        if not exe:
            return
        nome_sug = os.path.basename(os.path.dirname(exe))
        dialog = ctk.CTkInputDialog(text="Nome do jogo:", title="Adicionar jogo")
        dialog.geometry("350x180")
        nome = dialog.get_input()
        if not nome:
            nome = nome_sug
        if not nome:
            return

        # Runtime recomendado
        rt = "wine"
        if self.runtime_info["recomendado"] and self.runtime_info["recomendado"]["tipo"] != "wine":
            rt = self.runtime_info["recomendado"]["tipo"]

        self.biblioteca.adicionar(nome, exe, runtime=rt)
        self._mostrar_pagina("biblioteca")

    def _config_jogo(self, indice):
        """Abre janela de propriedades do jogo."""
        jogo = self.biblioteca.jogos[indice]

        win = ctk.CTkToplevel(self)
        win.title(f"Propriedades — {jogo['nome']}")
        win.geometry("480x500")
        win.configure(fg_color=CORES["base"])
        win.transient(self)
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text=jogo["nome"],
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=CORES["text"]).pack(anchor="w", pady=(0, 16))

        # Nome
        ctk.CTkLabel(scroll, text="Nome", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")
        entry_nome = ctk.CTkEntry(scroll, fg_color=CORES["surface0"],
                                  text_color=CORES["text"], border_color=CORES["surface1"])
        entry_nome.pack(fill="x", pady=(2, 12))
        entry_nome.insert(0, jogo["nome"])

        # Executável
        ctk.CTkLabel(scroll, text="Executavel", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")
        row_exe = ctk.CTkFrame(scroll, fg_color="transparent")
        row_exe.pack(fill="x", pady=(2, 12))
        entry_exe = ctk.CTkEntry(row_exe, fg_color=CORES["surface0"],
                                 text_color=CORES["text"], border_color=CORES["surface1"])
        entry_exe.pack(side="left", fill="x", expand=True)
        entry_exe.insert(0, jogo["exe"])

        def trocar_exe():
            e = filedialog.askopenfilename(filetypes=[("Executaveis", "*.exe *.EXE")])
            if e:
                entry_exe.delete(0, "end")
                entry_exe.insert(0, e)

        ctk.CTkButton(row_exe, text="...", width=36,
                      fg_color=CORES["surface0"], text_color=CORES["text"],
                      hover_color=CORES["surface1"], command=trocar_exe).pack(side="left", padx=(4, 0))

        # WINEPREFIX
        ctk.CTkLabel(scroll, text="WINEPREFIX (pasta isolada)", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")
        entry_prefix = ctk.CTkEntry(scroll, fg_color=CORES["surface0"],
                                    text_color=CORES["text"], border_color=CORES["surface1"])
        entry_prefix.pack(fill="x", pady=(2, 12))
        entry_prefix.insert(0, jogo.get("wineprefix", ""))

        # Runtime
        ctk.CTkLabel(scroll, text="Runtime", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")

        var_runtime = ctk.StringVar(value=jogo.get("runtime", "wine"))
        rt_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        rt_frame.pack(fill="x", pady=(2, 12))

        ctk.CTkRadioButton(rt_frame, text="Wine", variable=var_runtime, value="wine",
                           text_color=CORES["text"], fg_color=CORES["mauve"],
                           hover_color=CORES["lavender"]).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(rt_frame, text="Proton", variable=var_runtime, value="proton",
                           text_color=CORES["text"], fg_color=CORES["sapphire"],
                           hover_color=CORES["blue"]).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(rt_frame, text="Proton-GE", variable=var_runtime, value="proton-ge",
                           text_color=CORES["text"], fg_color=CORES["green"],
                           hover_color=CORES["sapphire"]).pack(side="left")

        # Argumentos
        ctk.CTkLabel(scroll, text="Argumentos extras", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")
        entry_args = ctk.CTkEntry(scroll, fg_color=CORES["surface0"],
                                  text_color=CORES["text"], border_color=CORES["surface1"],
                                  placeholder_text="ex: -fullscreen -dx11")
        entry_args.pack(fill="x", pady=(2, 12))
        entry_args.insert(0, jogo.get("args", ""))

        # Tags
        ctk.CTkLabel(scroll, text="Tags (separadas por virgula)", font=ctk.CTkFont(size=11),
                     text_color=CORES["overlay0"]).pack(anchor="w")
        entry_tags = ctk.CTkEntry(scroll, fg_color=CORES["surface0"],
                                  text_color=CORES["text"], border_color=CORES["surface1"],
                                  placeholder_text="ex: FPS, RPG, Favorito")
        entry_tags.pack(fill="x", pady=(2, 12))
        entry_tags.insert(0, ", ".join(jogo.get("tags", [])))

        # Info
        ctk.CTkFrame(scroll, height=1, fg_color=CORES["surface0"]).pack(fill="x", pady=8)
        tempo_fmt = Biblioteca.formatar_tempo_jogado(jogo.get("tempo_jogado", 0))
        ctk.CTkLabel(scroll, text=f"Tempo jogado: {tempo_fmt}",
                     font=ctk.CTkFont(size=11), text_color=CORES["overlay0"]).pack(anchor="w")

        # Botão salvar
        def salvar():
            tags_str = entry_tags.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

            self.biblioteca.editar(
                indice,
                nome=entry_nome.get().strip() or None,
                exe=entry_exe.get().strip() or None,
                wineprefix=entry_prefix.get().strip(),
                runtime=var_runtime.get(),
                args=entry_args.get().strip(),
                tags=tags,
            )
            win.destroy()
            self._mostrar_pagina("biblioteca")

        ctk.CTkButton(
            scroll, text="Salvar", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=CORES["blue"], text_color=CORES["crust"],
            hover_color=CORES["sapphire"], height=38, corner_radius=8,
            command=salvar,
        ).pack(fill="x", pady=(16, 0))

    def _remover_jogo(self, indice):
        jogo = self.biblioteca.jogos[indice]
        confirm = ctk.CTkToplevel(self)
        confirm.title("Remover jogo")
        confirm.geometry("380x160")
        confirm.configure(fg_color=CORES["base"])
        confirm.transient(self)
        confirm.grab_set()

        ctk.CTkLabel(confirm, text=f"Remover \"{jogo['nome']}\"?",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=CORES["text"]).pack(pady=(20, 4))
        ctk.CTkLabel(confirm, text="(Nao apaga os arquivos, so remove da lista)",
                     font=ctk.CTkFont(size=11), text_color=CORES["overlay0"]).pack()

        btns = ctk.CTkFrame(confirm, fg_color="transparent")
        btns.pack(pady=16)
        ctk.CTkButton(btns, text="Cancelar", width=100, fg_color=CORES["surface0"],
                      text_color=CORES["text"], hover_color=CORES["surface1"],
                      command=confirm.destroy).pack(side="left", padx=4)

        def confirmar():
            self.biblioteca.remover(indice)
            confirm.destroy()
            self._mostrar_pagina("biblioteca")

        ctk.CTkButton(btns, text="Remover", width=100, fg_color=CORES["red"],
                      text_color=CORES["crust"], hover_color="#e06080",
                      command=confirmar).pack(side="left", padx=4)

    # ============================================================
    # Página: Instalar
    # ============================================================
    def _pag_instalar(self):
        frame = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(frame, text="Instalar Jogo",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=CORES["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text="Selecione a pasta contendo o instalador",
                     font=ctk.CTkFont(size=12), text_color=CORES["overlay0"]).pack(anchor="w", pady=(2, 16))

        self.btn_selecionar = ctk.CTkButton(
            frame, text="Clique para selecionar a pasta",
            font=ctk.CTkFont(size=13), fg_color=CORES["surface0"],
            text_color=CORES["overlay0"], hover_color=CORES["surface1"],
            height=64, corner_radius=12, command=self._abrir_seletor,
        )
        self.btn_selecionar.pack(fill="x")

        self.label_status = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11),
                                         text_color=CORES["overlay0"], anchor="w")
        self.label_status.pack(fill="x", pady=(8, 0))

        self.label_deps = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11),
                                       text_color=CORES["yellow"], anchor="w")
        self.label_deps.pack(fill="x", pady=(2, 8))
        self._checar_deps()

        self.log_text = ctk.CTkTextbox(
            frame, font=ctk.CTkFont(family="monospace", size=11),
            fg_color=CORES["crust"], text_color=CORES["text"],
            corner_radius=10, height=200, state="disabled",
            scrollbar_button_color=CORES["surface1"],
        )
        self.log_text.pack(fill="both", expand=True, pady=(0, 8))
        self.log_text.tag_config("info", foreground=CORES["text"])
        self.log_text.tag_config("aviso", foreground=CORES["yellow"])
        self.log_text.tag_config("erro", foreground=CORES["red"])
        self.log_text.tag_config("erro_conhecido", foreground=CORES["red"])
        self.log_text.tag_config("sucesso", foreground=CORES["green"])

        # Monitor
        self.frame_monitor = ctk.CTkFrame(frame, fg_color=CORES["mantle"], corner_radius=8, height=36)
        self.label_mon_tempo = ctk.CTkLabel(self.frame_monitor, text="",
            font=ctk.CTkFont(family="monospace", size=11), text_color=CORES["text"])
        self.label_mon_tempo.pack(side="left", padx=10)
        self.label_mon_io = ctk.CTkLabel(self.frame_monitor, text="",
            font=ctk.CTkFont(family="monospace", size=11), text_color=CORES["blue"])
        self.label_mon_io.pack(side="left", padx=8)
        self.label_mon_status = ctk.CTkLabel(self.frame_monitor, text="",
            font=ctk.CTkFont(family="monospace", size=11, weight="bold"), text_color=CORES["green"])
        self.label_mon_status.pack(side="left", padx=8)
        self.label_mon_prog = ctk.CTkLabel(self.frame_monitor, text="",
            font=ctk.CTkFont(family="monospace", size=11, weight="bold"), text_color=CORES["pink"])
        self.label_mon_prog.pack(side="left", padx=8)
        self.barra_progresso = ctk.CTkProgressBar(self.frame_monitor, width=120, height=12,
            fg_color=CORES["surface0"], progress_color=CORES["mauve"], corner_radius=6)
        self.barra_progresso.set(0)
        self.barra_progresso.pack(side="left", padx=8)
        ctk.CTkButton(self.frame_monitor, text="Forcar parada", width=100,
            font=ctk.CTkFont(size=10), fg_color=CORES["red"], text_color=CORES["crust"],
            hover_color="#e06080", height=26, corner_radius=6,
            command=self._forcar_encerramento).pack(side="right", padx=8)

        self.frame_botoes = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_botoes.pack(fill="x")

        self.btn_instalar = ctk.CTkButton(
            self.frame_botoes, text="Instalar", width=140,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=CORES["blue"], text_color=CORES["crust"],
            hover_color=CORES["sapphire"], height=40, corner_radius=10,
            state="disabled", command=self._iniciar_instalacao,
        )
        self.btn_instalar.pack(side="left")

    def _checar_deps(self):
        faltando = VerificadorDependencias.faltando()
        if faltando:
            self.label_deps.configure(
                text=f"Faltando: {', '.join(faltando)}  |  sudo pacman -S wine-staging winetricks",
                text_color=CORES["yellow"])
        else:
            self.label_deps.configure(text="Dependencias OK", text_color=CORES["green"])

    def _log(self, tipo, texto):
        if not hasattr(self, "log_text") or not self.log_text.winfo_exists():
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", texto + "\n", tipo)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _abrir_seletor(self):
        if self.instalando:
            return
        pasta = filedialog.askdirectory(title="Selecione a pasta do jogo")
        if pasta:
            self._selecionar_pasta(pasta)

    def _selecionar_pasta(self, pasta):
        self.caminho_pasta = pasta
        self.caminho_setup = None

        # Procura instalador (generico, nao so setup.exe)
        det = DetectorInstaladores(self.config)
        instalador = det._encontrar_instalador(pasta)

        if instalador:
            self.caminho_setup = instalador
            nome = os.path.basename(pasta)
            exe_nome = os.path.basename(instalador)
            self.btn_selecionar.configure(text=nome, text_color=CORES["green"])
            self.label_status.configure(
                text=f"Instalador encontrado: {exe_nome}", text_color=CORES["green"])
            if not VerificadorDependencias.faltando():
                self.btn_instalar.configure(state="normal")
        else:
            self.btn_selecionar.configure(text="Nenhum instalador encontrado",
                                          text_color=CORES["red"])
            self.label_status.configure(text=f"Pasta: {pasta}", text_color=CORES["red"])
            self.btn_instalar.configure(state="disabled")

    def _iniciar_instalacao(self):
        if not self.caminho_setup or self.instalando:
            return
        self.instalando = True
        self.btn_instalar.configure(state="disabled", text="Instalando...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        # Usa Wine pra instalacao (setup sempre roda via Wine)
        self.executor = ExecutorWine(
            caminho_exe=self.caminho_setup, fila_log=self.fila_log,
            callback_fim=self._instalacao_fim,
        )
        self.executor.iniciar()
        self.monitor = MonitorProcesso(self.executor, pasta_repack=self.caminho_pasta)
        self.frame_monitor.pack(fill="x", pady=(0, 8), before=self.frame_botoes)
        self.barra_progresso.set(0)
        self._loop_monitor()

    def _loop_monitor(self):
        if not self.monitor or not self.monitor.ativo:
            return
        info = self.monitor.atualizar()
        if info is None:
            self.after(2000, self._loop_monitor)
            return

        self.label_mon_tempo.configure(text=f"Tempo: {info['tempo']}")
        self.label_mon_io.configure(text=f"Escrito: {info['io_total']}  (+{info['io_delta']})")

        if info["status"] == "ativo":
            self.label_mon_status.configure(text="ATIVO", text_color=CORES["green"])
        elif info["status"] == "travado":
            m = info["inativo"] // 60
            self.label_mon_status.configure(text=f"SEM ATIVIDADE ({m}min)", text_color=CORES["red"])
            if m == 2:
                self._log("aviso", f"Sem atividade ha {m} min. Pode estar travado.")
        else:
            self.label_mon_status.configure(text=f"aguardando ({info['inativo']}s)",
                                            text_color=CORES["yellow"])

        if info["progresso"] is not None:
            pct = info["progresso"]
            self.label_mon_prog.configure(text=f"{pct:.0f}%  (chunk {info['chunk']}/{info['total_chunks']})")
            self.barra_progresso.set(pct / 100)
        else:
            self.label_mon_prog.configure(text="")

        self.after(2000, self._loop_monitor)

    def _forcar_encerramento(self):
        if not self.executor or not self.executor.processo:
            return
        pid = self.executor.processo.pid
        self._log("aviso", f"Forcando encerramento do processo {pid}...")
        try:
            subprocess.run(["kill", "-9", str(pid)], capture_output=True)
            subprocess.run(["wineserver", "-k"], capture_output=True)
            self._log("info", "Processo encerrado.")
        except Exception as e:
            self._log("erro", f"Erro: {e}")

    def _instalacao_fim(self, codigo):
        self.after(0, lambda: self._pos_instalacao(codigo))

    def _pos_instalacao(self, codigo):
        self.instalando = False
        if self.monitor:
            self.monitor.parar()
            self.monitor = None

        if codigo == 0:
            self._log("sucesso", "")
            self._log("sucesso", "Instalacao concluida!")
            self.btn_instalar.configure(text="Concluido", state="disabled")
        else:
            self._log("erro", "")
            self._log("erro", f"Processo encerrado com codigo {codigo}")
            self.btn_instalar.configure(text="Falhou", state="disabled")

        ctk.CTkButton(
            self.frame_botoes, text="Adicionar a biblioteca", width=160,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=CORES["green"], text_color=CORES["crust"],
            hover_color="#8bd18b", height=34, corner_radius=8,
            command=self._adicionar_pos_instalacao,
        ).pack(side="left", padx=(8, 0))

        if codigo == 0:
            ctk.CTkButton(
                self.frame_botoes, text="Deletar instalador", width=120,
                font=ctk.CTkFont(size=11), fg_color=CORES["red"], text_color=CORES["crust"],
                hover_color="#e06080", height=34, corner_radius=8,
                command=self._limpar_repack,
            ).pack(side="left", padx=(8, 0))

        # Botao pra abrir o log completo da instalacao
        if self.executor and self.executor.log_path and os.path.exists(self.executor.log_path):
            log_caminho = self.executor.log_path
            ctk.CTkButton(
                self.frame_botoes, text="Ver log", width=90,
                font=ctk.CTkFont(size=11), fg_color=CORES["surface0"],
                text_color=CORES["subtext1"], hover_color=CORES["surface1"],
                height=34, corner_radius=8,
                command=lambda: subprocess.Popen(["xdg-open", log_caminho]),
            ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            self.frame_botoes, text="Nova instalacao", width=120,
            font=ctk.CTkFont(size=11), fg_color=CORES["surface0"],
            text_color=CORES["subtext1"], hover_color=CORES["surface1"],
            height=34, corner_radius=8,
            command=lambda: self._mostrar_pagina("instalar"),
        ).pack(side="left", padx=(8, 0))

        if codigo == 0 and self.config.get("auto_delete"):
            self.after(500, self._limpar_repack)

    def _adicionar_pos_instalacao(self):
        nome_sug = os.path.basename(self.caminho_pasta or "")
        nome_limpo = re.sub(r"\s*\[.*?\]\s*", " ", nome_sug).strip()

        dialog = ctk.CTkInputDialog(text="Nome do jogo:", title="Adicionar a biblioteca")
        dialog.geometry("350x180")
        nome = dialog.get_input()
        if not nome:
            nome = nome_limpo
        if not nome:
            return

        exe = filedialog.askopenfilename(
            title=f"Selecione o executavel de {nome}",
            filetypes=[("Executaveis", "*.exe *.EXE"), ("Todos", "*.*")],
            initialdir=os.path.expanduser("~/.wine/drive_c/"),
        )
        if not exe:
            return

        rt = "wine"
        if self.runtime_info["recomendado"] and self.runtime_info["recomendado"]["tipo"] != "wine":
            rt = self.runtime_info["recomendado"]["tipo"]

        self.biblioteca.adicionar(nome, exe, runtime=rt)
        self._log("sucesso", f"\"{nome}\" adicionado a biblioteca!")

    def _limpar_repack(self):
        if not self.caminho_pasta or not os.path.isdir(self.caminho_pasta):
            return
        tamanho = DetectorInstaladores.calcular_tamanho(self.caminho_pasta)
        tamanho_fmt = DetectorInstaladores.formatar_tamanho(tamanho)
        nome = os.path.basename(self.caminho_pasta)

        confirm = ctk.CTkToplevel(self)
        confirm.title("Deletar instalador")
        confirm.geometry("420x180")
        confirm.configure(fg_color=CORES["base"])
        confirm.transient(self)
        confirm.grab_set()

        ctk.CTkLabel(confirm, text="Deletar pasta do instalador?",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=CORES["text"]).pack(pady=(16, 4))
        ctk.CTkLabel(confirm, text=f"{nome}\nTamanho: {tamanho_fmt}",
                     font=ctk.CTkFont(size=11), text_color=CORES["overlay0"]).pack()

        btns = ctk.CTkFrame(confirm, fg_color="transparent")
        btns.pack(pady=16)
        ctk.CTkButton(btns, text="Cancelar", width=100, fg_color=CORES["surface0"],
                      text_color=CORES["text"], hover_color=CORES["surface1"],
                      command=confirm.destroy).pack(side="left", padx=4)

        def deletar():
            confirm.destroy()
            try:
                shutil.rmtree(self.caminho_pasta)
                self._log("sucesso", f"Deletado: {nome} ({tamanho_fmt} liberados)")
                vistos = self.config.get("repacks_ja_vistos") or []
                if self.caminho_pasta in vistos:
                    vistos.remove(self.caminho_pasta)
                    self.config.set("repacks_ja_vistos", vistos)
            except Exception as e:
                self._log("erro", f"Erro ao deletar: {e}")

        ctk.CTkButton(btns, text="Deletar", width=100, fg_color=CORES["red"],
                      text_color=CORES["crust"], hover_color="#e06080",
                      command=deletar).pack(side="left", padx=4)

    # ============================================================
    # Página: Wine / Proton
    # ============================================================
    def _pag_runtime(self):
        frame = ctk.CTkScrollableFrame(self.conteudo, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(frame, text="Wine / Proton",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=CORES["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text="Runtimes detectados no sistema",
                     font=ctk.CTkFont(size=12), text_color=CORES["overlay0"]).pack(anchor="w", pady=(2, 16))

        # Atualiza detecção
        self.runtime_info = DetectorRuntime.recomendar()

        # --- Recomendação ---
        rec = self.runtime_info
        rec_frame = ctk.CTkFrame(frame, fg_color=CORES["surface0"], corner_radius=12)
        rec_frame.pack(fill="x", pady=(0, 16))

        rec_inner = ctk.CTkFrame(rec_frame, fg_color="transparent")
        rec_inner.pack(fill="x", padx=16, pady=12)

        if rec["recomendado"]:
            nome_rec = rec["recomendado"].get("nome", rec["recomendado"].get("versao", ""))
            tipo_rec = rec["recomendado"]["tipo"]
            cor_rec = CORES["green"] if "ge" in tipo_rec else CORES["sapphire"] if "proton" in tipo_rec else CORES["mauve"]

            ctk.CTkLabel(rec_inner, text="RECOMENDADO",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=cor_rec).pack(anchor="w")
            ctk.CTkLabel(rec_inner, text=nome_rec,
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=CORES["text"]).pack(anchor="w")
        else:
            ctk.CTkLabel(rec_inner, text="NENHUM RUNTIME ENCONTRADO",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=CORES["red"]).pack(anchor="w")

        ctk.CTkLabel(rec_inner, text=rec["motivo"],
                     font=ctk.CTkFont(size=11), text_color=CORES["subtext0"],
                     wraplength=550, justify="left").pack(anchor="w", pady=(8, 0))

        # --- Wine ---
        ctk.CTkFrame(frame, height=1, fg_color=CORES["surface0"]).pack(fill="x", pady=8)
        ctk.CTkLabel(frame, text="Wine", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=CORES["mauve"]).pack(anchor="w", pady=(8, 4))

        wine = rec["wine"]
        if wine:
            card_w = ctk.CTkFrame(frame, fg_color=CORES["surface0"], corner_radius=10)
            card_w.pack(fill="x", pady=(0, 8))
            inner_w = ctk.CTkFrame(card_w, fg_color="transparent")
            inner_w.pack(fill="x", padx=12, pady=10)
            ctk.CTkLabel(inner_w, text=wine["versao"],
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=CORES["text"]).pack(anchor="w")
            ctk.CTkLabel(inner_w, text=wine["caminho"],
                         font=ctk.CTkFont(family="monospace", size=10),
                         text_color=CORES["overlay0"]).pack(anchor="w")
            ctk.CTkLabel(inner_w,
                         text="Bom para: instalacao de repacks, jogos mais antigos",
                         font=ctk.CTkFont(size=10), text_color=CORES["subtext0"]).pack(anchor="w", pady=(4, 0))
        else:
            ctk.CTkLabel(frame, text="  Nao instalado. Instale: sudo pacman -S wine-staging",
                         font=ctk.CTkFont(size=11), text_color=CORES["red"]).pack(anchor="w")

        # --- Proton ---
        ctk.CTkFrame(frame, height=1, fg_color=CORES["surface0"]).pack(fill="x", pady=8)
        ctk.CTkLabel(frame, text="Proton", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=CORES["sapphire"]).pack(anchor="w", pady=(8, 4))

        protons = rec["protons"]
        if protons:
            for p in protons:
                card_p = ctk.CTkFrame(frame, fg_color=CORES["surface0"], corner_radius=10)
                card_p.pack(fill="x", pady=(0, 6))
                inner_p = ctk.CTkFrame(card_p, fg_color="transparent")
                inner_p.pack(fill="x", padx=12, pady=10)

                titulo_p = ctk.CTkFrame(inner_p, fg_color="transparent")
                titulo_p.pack(fill="x")

                ctk.CTkLabel(titulo_p, text=p["nome"],
                             font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=CORES["text"]).pack(side="left")

                cor_badge = CORES["green"] if p["tipo"] == "proton-ge" else CORES["blue"]
                ctk.CTkLabel(titulo_p, text=p["origem"],
                             font=ctk.CTkFont(size=9), text_color=cor_badge,
                             fg_color=CORES["base"], corner_radius=4, padx=6).pack(side="left", padx=(8, 0))

                ctk.CTkLabel(inner_p, text=p["caminho"],
                             font=ctk.CTkFont(family="monospace", size=10),
                             text_color=CORES["overlay0"]).pack(anchor="w")

                if p["tipo"] == "proton-ge":
                    ctk.CTkLabel(inner_p,
                        text="Melhor para: jogos modernos, anti-cheat, cutscenes com codec",
                        font=ctk.CTkFont(size=10), text_color=CORES["subtext0"]).pack(anchor="w", pady=(4, 0))
                else:
                    ctk.CTkLabel(inner_p,
                        text="Bom para: jogos da Steam, compatibilidade geral",
                        font=ctk.CTkFont(size=10), text_color=CORES["subtext0"]).pack(anchor="w", pady=(4, 0))
        else:
            ctk.CTkLabel(frame,
                text="  Nenhum Proton encontrado.\n  Instale Proton-GE: yay -S proton-ge-custom-bin",
                font=ctk.CTkFont(size=11), text_color=CORES["yellow"], justify="left").pack(anchor="w")

        # Botão atualizar
        ctk.CTkButton(
            frame, text="Atualizar deteccao", width=150,
            font=ctk.CTkFont(size=11), fg_color=CORES["surface0"],
            text_color=CORES["subtext1"], hover_color=CORES["surface1"],
            height=32, corner_radius=8,
            command=lambda: self._mostrar_pagina("runtime"),
        ).pack(anchor="w", pady=(16, 0))

    # ============================================================
    # Página: Configurações
    # ============================================================
    def _pag_config(self):
        frame = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(frame, text="Configuracoes",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=CORES["text"]).pack(anchor="w", pady=(0, 20))

        # Pasta monitorada
        ctk.CTkLabel(frame, text="Pasta monitorada",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CORES["subtext1"]).pack(anchor="w")
        ctk.CTkLabel(frame, text="Detecta instaladores automaticamente",
                     font=ctk.CTkFont(size=11), text_color=CORES["overlay0"]).pack(anchor="w", pady=(0, 8))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 20))
        self.entry_pasta = ctk.CTkEntry(row, font=ctk.CTkFont(family="monospace", size=11),
                                        fg_color=CORES["surface0"], text_color=CORES["text"],
                                        border_color=CORES["surface1"], height=36, corner_radius=8)
        self.entry_pasta.pack(side="left", fill="x", expand=True)
        self.entry_pasta.insert(0, self.config.get("pasta_monitorada"))
        ctk.CTkButton(row, text="Alterar", width=80, font=ctk.CTkFont(size=11),
                      fg_color=CORES["surface0"], text_color=CORES["subtext1"],
                      hover_color=CORES["surface1"], height=36, corner_radius=8,
                      command=self._alterar_pasta).pack(side="left", padx=(8, 0))

        # Auto-delete
        self.var_auto_del = ctk.BooleanVar(value=self.config.get("auto_delete"))
        ctk.CTkSwitch(
            frame, text="Oferecer para deletar instalador apos concluir",
            font=ctk.CTkFont(size=12), text_color=CORES["text"],
            fg_color=CORES["surface1"], progress_color=CORES["mauve"],
            button_color=CORES["lavender"], button_hover_color=CORES["blue"],
            variable=self.var_auto_del,
            command=lambda: self.config.set("auto_delete", self.var_auto_del.get()),
        ).pack(anchor="w", pady=(0, 20))

        # Prefixes
        ctk.CTkFrame(frame, height=1, fg_color=CORES["surface0"]).pack(fill="x", pady=8)
        ctk.CTkLabel(frame, text="WINEPREFIX isolados",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CORES["subtext1"]).pack(anchor="w", pady=(8, 4))

        if os.path.isdir(PASTA_PREFIXES):
            prefixes = os.listdir(PASTA_PREFIXES)
            if prefixes:
                for p in sorted(prefixes):
                    ctk.CTkLabel(frame, text=f"  {p}",
                                 font=ctk.CTkFont(family="monospace", size=10),
                                 text_color=CORES["overlay0"]).pack(anchor="w")
            else:
                ctk.CTkLabel(frame, text="  Nenhum prefix criado ainda",
                             font=ctk.CTkFont(size=11), text_color=CORES["surface2"]).pack(anchor="w")
        else:
            ctk.CTkLabel(frame, text="  Nenhum prefix criado ainda",
                         font=ctk.CTkFont(size=11), text_color=CORES["surface2"]).pack(anchor="w")

        ctk.CTkLabel(frame, text=f"  Local: {PASTA_PREFIXES}",
                     font=ctk.CTkFont(family="monospace", size=9),
                     text_color=CORES["surface2"]).pack(anchor="w", pady=(4, 0))

        # Ignorados
        ctk.CTkFrame(frame, height=1, fg_color=CORES["surface0"]).pack(fill="x", pady=(16, 8))
        ctk.CTkLabel(frame, text="Instaladores ignorados",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CORES["subtext1"]).pack(anchor="w", pady=(8, 4))

        vistos = self.config.get("repacks_ja_vistos") or []
        if vistos:
            for v in vistos:
                ctk.CTkLabel(frame, text=f"  {os.path.basename(v)}",
                             font=ctk.CTkFont(family="monospace", size=10),
                             text_color=CORES["overlay0"]).pack(anchor="w")
            ctk.CTkButton(frame, text="Limpar lista", width=100,
                          font=ctk.CTkFont(size=11), fg_color=CORES["surface0"],
                          text_color=CORES["subtext1"], hover_color=CORES["surface1"],
                          height=28, corner_radius=6,
                          command=self._limpar_ignorados).pack(anchor="w", pady=(8, 0))
        else:
            ctk.CTkLabel(frame, text="  Nenhum",
                         font=ctk.CTkFont(size=11), text_color=CORES["surface2"]).pack(anchor="w")

    def _alterar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta para monitorar",
                                        initialdir=self.config.get("pasta_monitorada"))
        if pasta:
            self.config.set("pasta_monitorada", pasta)
            self.entry_pasta.delete(0, "end")
            self.entry_pasta.insert(0, pasta)

    def _limpar_ignorados(self):
        self.config.set("repacks_ja_vistos", [])
        self._mostrar_pagina("config")

    # ============================================================
    # Detector de downloads
    # ============================================================
    def _escanear_downloads(self):
        if not self.instalando:
            novos = self.detector.escanear()
            if novos and novos != self.repacks_pendentes:
                self.repacks_pendentes = novos
                self._atualizar_banner()
            elif not novos and self.repacks_pendentes:
                self.repacks_pendentes = []
                self.frame_banner.pack_forget()
        self.after(10000, self._escanear_downloads)

    def _atualizar_banner(self):
        if not self.repacks_pendentes:
            self.frame_banner.pack_forget()
            return
        repack = self.repacks_pendentes[0]
        nome = re.sub(r"\s*\[.*?\]\s*", " ", repack["nome"]).strip()
        qtd = len(self.repacks_pendentes)
        texto = f"Jogo detectado:\n{nome}"
        if qtd > 1:
            texto += f"\n(+{qtd - 1} outros)"
        self.label_banner.configure(text=texto)
        self.frame_banner.pack(fill="x", padx=12, pady=(0, 8))

    def _instalar_detectado(self):
        if not self.repacks_pendentes:
            return
        repack = self.repacks_pendentes[0]
        self.detector.marcar_como_visto(repack["caminho"])
        self.frame_banner.pack_forget()
        self._mostrar_pagina("instalar")
        self._selecionar_pasta(repack["caminho"])

    def _ignorar_detectado(self):
        if not self.repacks_pendentes:
            return
        repack = self.repacks_pendentes.pop(0)
        self.detector.marcar_como_visto(repack["caminho"])
        if self.repacks_pendentes:
            self._atualizar_banner()
        else:
            self.frame_banner.pack_forget()

    # ============================================================
    # Fila de log
    # ============================================================
    def _processar_fila(self):
        while True:
            try:
                tipo, conteudo = self.fila_log.get_nowait()
            except queue.Empty:
                break
            if tipo == "fim":
                continue
            if tipo in ("info", "aviso"):
                cl = conteudo.lower()
                if "err:" in cl or "error" in cl:
                    tipo = "erro"
                elif "warn:" in cl or "warning" in cl:
                    tipo = "aviso"
            self._log(tipo, conteudo)
        self.after(100, self._processar_fila)


if __name__ == "__main__":
    app = App()
    app.mainloop()
