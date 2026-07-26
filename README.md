
<p align="center">
  <pre>
  ________  ________                 ________  ________  ________
 |\   __  \|\   __  \               |\   __  \|\   __  \|\   __  \
 \ \  \|\ /\ \  \|\  \  ____________\ \  \|\  \ \  \|\  \ \  \|\  \
  \ \   __  \ \   _  _\|\____________\ \   __  \ \   _  _\ \  \\\  \
   \ \  \|\  \ \  \\\  \|____________|\ \  \ \  \ \  \\\  \\ \  \\\  \
    \ \_______\ \__\\\\ _\               \ \_______\ \__\\\\ _\\ \_______\
     \|_______|\|__|\|__|                \|_______|\|__|\|__|\|_______|
  </pre>
  <p><strong>QR-Bro</strong> — gerador de QR codes no terminal.<br>
  Interativo com setas, preview ASCII ao vivo, cores, logo central.</p>
</p>

---

## Instalação

### Com curl (recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/thdreams0/QR-Bro/main/install.sh | bash
```

Isto descarrega o `qrbro` para `~/.local/bin/` e instala as dependências (`qrcode[pil]`, `Pillow`).

Se `~/.local/bin/` não estiver no teu `PATH`, adiciona ao teu shell config:

```bash
# ~/.bashrc / ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# fish
fish_add_path ~/.local/bin
```

### Manual

```bash
git clone https://github.com/thdreams0/QR-Bro.git
cd QR-Bro
pip install qrcode[pil] Pillow
chmod +x qrbro
./qrbro
```

Ou copia os ficheiros para `~/.local/bin/`.

---

## Uso

### Modo interativo (recomendado)

```bash
qrbro
```

Navega com setas ↑↓, Enter para confirmar, Esc para voltar. O preview ASCII do QR aparece ao vivo enquanto escolhes cores e nível de erro.

### Modo direto

```bash
qrbro "https://example.com"
qrbro "texto ou URL" --color "#FF5733" --bg "#1a1a2e"
qrbro "https://example.com" --logo logo.png -o output.png
qrbro --help
```

---

## Opções

| Opção | Descrição | Default |
|-------|-----------|---------|
| `--color HEX` | Cor do QR (hex) | `#000000` |
| `--bg HEX` | Cor de fundo (hex) | `#FFFFFF` |
| `--logo PATH` | Caminho para logo central | — |
| `--logo-size PCT` | Tamanho do logo em % do QR | `25` |
| `--output PATH` / `-o` | Ficheiro de saída | `~/Downloads/qrcode.png` |
| `--version VER` | Versão QR 1–40 | auto |
| `--box-size N` | Tamanho de cada módulo (px) | `10` |
| `--border N` | Espessura da borda | `4` |
| `--error L/M/Q/H` | Nível de correção de erros | `H` |
| `--show` | Abrir imagem após gerar | — |
| `-y` | Saltar confirmação | — |

---

## Presets de cor (modo interativo)

| # | Nome | QR | Fundo |
|---|------|----|-------|
| 1 | Classic black | `#000000` | `#FFFFFF` |
| 2 | Night mode | `#00FF88` | `#0D1117` |
| 3 | Royal | `#FFD700` | `#1a1a2e` |
| 4 | Fire | `#FF5733` | `#1a0a00` |
| 5 | Ocean | `#00BFFF` | `#001830` |
| 6 | Neon pink | `#FF1493` | `#000000` |
| 7 | Minimal | `#333333` | `#FFFFFF` |
| 8 | Custom | escolhes | escolhes |

---

## Exemplos

```bash
# Interativo (setas, preview ao vivo)
qrbro

# QR simples
qrbro "https://github.com/thdreams0"

# Com cores
qrbro "Olá mundo" --color "#FF5733" --bg "#1a1a2e"

# Com logo central
qrbro "https://example.com" --logo logo.png --logo-size 30

# Output personalizado
qrbro "https://example.com" -o ~/Desktop/meuqr.png

# Abrir automaticamente
qrbro "https://example.com" --show

# Tudo junto
qrbro "https://example.com" \
  --color "#00FF88" --bg "#0D1117" \
  --logo icon.png --logo-size 25 \
  -o ~/Desktop/qr.png --show
```

---

## Requisitos

- Python 3.8+
- `qrcode[pil]` e `Pillow` (instalados automaticamente)

---

<p align="center">
  <sub>Feito por <a href="https://github.com/thdreams0">thdreams0</a></sub>
</p>
