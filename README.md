
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
  <p><strong>QR-Bro</strong> — QR code generator for the terminal.<br>
  Interactive arrow-key pickers, live ASCII preview, colors, center logo.</p>
</p>

---

## Installation

### With curl (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/thdreams0/QR-Bro/main/install.sh | bash
```

Downloads `qrbro` to `~/.local/bin/` and installs dependencies (`qrcode[pil]`, `Pillow`).

If `~/.local/bin/` is not in your `PATH`, add it:

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

Or copy the files to `~/.local/bin/`.

---

## Usage

### Interactive mode (recommended)

```bash
qrbro
```

Navigate with ↑↓ arrows, Enter to confirm, Esc to go back, Ctrl+C to quit. The live ASCII preview updates as you pick error correction levels. Output goes to `~/Downloads/qrcode.png` by default — no extra prompts.

### Direct mode

```bash
qrbro "https://example.com"
qrbro "text or URL" --color "#FF5733" --bg "#1a1a2e"
qrbro "https://example.com" --logo logo.png -o output.png
qrbro --help
```

---

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--color HEX` | QR color (hex) | `#000000` |
| `--bg HEX` | Background color (hex) | `#FFFFFF` |
| `--logo PATH` | Center logo image path | — |
| `--logo-size PCT` | Logo size as % of QR | `25` |
| `--output PATH` / `-o` | Output file | `~/Downloads/qrcode.png` |
| `--version VER` | QR version 1–40 | auto |
| `--box-size N` | Module size in px | `10` |
| `--border N` | Border thickness | `4` |
| `--error L/M/Q/H` | Error correction level | `H` |
| `--show` | Open image after generation | — |
| `-y` | Skip confirmation | — |

---

## Examples

```bash
# Interactive (arrows, live preview)
qrbro

# Simple QR
qrbro "https://github.com/thdreams0"

# With colors
qrbro "Hello world" --color "#FF5733" --bg "#1a1a2e"

# With center logo
qrbro "https://example.com" --logo logo.png --logo-size 30

# Custom output
qrbro "https://example.com" -o ~/Desktop/myqr.png

# Open automatically
qrbro "https://example.com" --show

# All together
qrbro "https://example.com" \
  --color "#00FF88" --bg "#0D1117" \
  --logo icon.png --logo-size 25 \
  -o ~/Desktop/qr.png --show
```

---

## Requirements

- Python 3.8+
- `qrcode[pil]` and `Pillow` (installed automatically)

---

<p align="center">
  <sub>Made by <a href="https://github.com/thdreams0">thdreams0</a></sub>
</p>
