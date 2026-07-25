#!/usr/bin/env python3
"""
qrbro — Gerador de QR Codes customizados com cores e logo no centro.

USO:
    qrbro                        # Modo interativo (pergunta tudo no terminal)
    qrbro "texto ou URL"         # Modo direto com argumentos opcionais

OPCOES (modo direto):
    --color HEX         Cor do QR (ex: #FF5733)
    --bg HEX            Cor de fundo (ex: #FFFFFF)
    --logo PATH         Caminho para imagem do logo (centro)
    --logo-size PCT     Tamanho do logo em %% do QR (def: 25)
    --output PATH       Ficheiro de saída (def: qrcode.png)
    --version VER       Versão do QR (1-40, def: auto)
    --box-size N        Tamanho de cada box em px (def: 10)
    --border N          Tamanho da borda (def: 4)
    --error LOW/M/Q/H   Nível de correção de erro (def: H)
    --show              Abrir a imagem depois de gerar
    -y                  Skip confirmação (modo não-interativo)
"""

import argparse
import sys
import os

try:
    import qrcode
    from PIL import Image
except ImportError:
    print(" Dependencias em falta. A instalar automaticamente...")
    import subprocess
    for cmd in [
        [sys.executable, "-m", "pip", "install", "--quiet", "qrcode[pil]", "Pillow"],
        [sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages", "qrcode[pil]", "Pillow"],
        [sys.executable, "-m", "pip", "install", "--quiet", "--user", "qrcode[pil]", "Pillow"],
    ]:
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            break
    else:
        print(" ERRO: Nao foi possivel instalar dependencias.")
        print(" Tenta manualmente: pip install qrcode[pil] Pillow")
        sys.exit(1)

    # Reimportar apos instalacao
    try:
        import qrcode
        from PIL import Image
    except ImportError:
        print(" ERRO: Falha ao importar apos instalacao.")
        print(" Tenta manualmente: pip install qrcode[pil] Pillow")
        sys.exit(1)


# ── Cores ANSI ──────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
LOGO = f"""{CYAN}{BOLD}
   ▗▄▖ ▗▄▖ ▗▄▖
   ▐█ ▐█ ▐█ ▐█
   ▐█ ▐█ ▐█ ▐█
   ▐▙▄▟▌▐▙▄▟▌▐▙▄▟▌
   {DIM}qrbro — QR Code Builder{RESET}"""


# ── Helpers ─────────────────────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def prompt(default: str = "", label: str = "> ") -> str:
    val = input(f"  {DIM}{label}{RESET}")
    return val.strip() or default


# ── QR Generation ────────────────────────────────────────
def generate_qr(
    data: str,
    color: str = "#000000",
    bg_color: str = "#FFFFFF",
    logo_path: str | None = None,
    logo_size_pct: float = 25,
    output: str = "qrcode.png",
    version: int | None = None,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "H",
    show: bool = False,
) -> str:

    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    ec = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_H)

    if logo_path and error_correction.upper() in ("L", "M"):
        print(f" {YELLOW}aviso{RESET} Com logo no centro, recomenda-se nivel H ou Q de correcao de erro.")

    qr = qrcode.QRCode(
        version=version or None,
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color=bg_color).convert("RGBA")

    # Pintar pixéis manualmente (garantir cores exatas)
    pixels = img.load()
    w, h = img.size
    fill_rgb = hex_to_rgb(color)
    back_rgb = hex_to_rgb(bg_color)

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < 128 and g < 128 and b < 128:
                pixels[x, y] = (*fill_rgb, a)
            elif r > 200 and g > 200 and b > 200:
                pixels[x, y] = (*back_rgb, a)

    # Logo ao centro
    if logo_path and os.path.isfile(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            qr_w, qr_h = img.size
            logo_sz = int(min(qr_w, qr_h) * logo_size_pct / 100)
            logo.thumbnail((logo_sz, logo_sz), Image.LANCZOS)

            from PIL import ImageDraw
            mask = Image.new("L", logo.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo.size[0], logo.size[1]), fill=255)

            px = (qr_w - logo.size[0]) // 2
            py = (qr_h - logo.size[1]) // 2
            img.paste(logo, (px, py), mask)
        except Exception as e:
            print(f" {YELLOW}aviso{RESET} Erro ao processar logo: {e}")

    img.save(output, "PNG")
    return os.path.abspath(output)


# ── Modo Interactivo ─────────────────────────────────────
def interactive_mode():
    print(LOGO)
    print(f"  {DIM}Introduz os dados para gerar o QR code. Enter = valor default.{RESET}\n")

    # 1. Data
    while True:
        data = input(f" {BOLD}?{RESET} URL ou texto a codificar\n  {DIM}> {RESET}")
        if data.strip():
            break
        print(f" {RED}erro{RESET} Este campo e obrigatorio.\n")

    # 2. Cor do QR
    color = input(f" {BOLD}?{RESET} Cor do QR {DIM}[#000000]{RESET}\n  {DIM}> {RESET}").strip()
    if not color:
        color = "#000000"
    elif not color.startswith("#"):
        color = f"#{color}"

    # 3. Cor de fundo
    bg = input(f" {BOLD}?{RESET} Cor de fundo {DIM}[#FFFFFF]{RESET}\n  {DIM}> {RESET}").strip()
    if not bg:
        bg = "#FFFFFF"
    elif not bg.startswith("#"):
        bg = f"#{bg}"

    # 4. Logo
    logo = input(f" {BOLD}?{RESET} Caminho do logo {DIM}[opcional, Enter para saltar]{RESET}\n  {DIM}> {RESET}").strip()

    logo_size = 25
    if logo:
        sz = input(f" {BOLD}?{RESET} Tamanho do logo em % do QR {DIM}[25]{RESET}\n  {DIM}> {RESET}").strip()
        if sz:
            try:
                logo_size = int(sz)
            except ValueError:
                print(f" {YELLOW}aviso{RESET} Valor invalido, a usar 25%.")

    # 5. Erro
    err_prompt = input(f" {BOLD}?{RESET} Nivel de correcao de erro {DIM}[H] — L/M/Q/H{RESET}\n  {DIM}> {RESET}").strip().upper()
    if err_prompt not in ("L", "M", "Q", "H", ""):
        print(f" {YELLOW}aviso{RESET} Opcao invalida, a usar H.")
        err_prompt = "H"
    error = err_prompt or "H"

    # 6. Output
    out = input(f" {BOLD}?{RESET} Nome do ficheiro {DIM}[qrcode.png]{RESET}\n  {DIM}> {RESET}").strip()
    if not out:
        out = "qrcode.png"
    if not out.endswith(".png"):
        out += ".png"

    # 7. Mostrar imagem?
    show_input = input(f" {BOLD}?{RESET} Abrir a imagem depois de gerar? {DIM}[s/N]{RESET}\n  {DIM}> {RESET}").strip().lower()
    show = show_input in ("s", "sim", "yes", "y")

    # ── Resumo ────────────────────────────────────────
    ec_label = {"L": "Low", "M": "Medium", "Q": "Quartile", "H": "High"}
    print(f"\n {DIM}{'─'*40}{RESET}")
    print(f" {BOLD}Resumo:{RESET}")
    print(f"   Dados:     {data}")
    print(f"   Cor QR:    {color}")
    print(f"   Fundo:     {bg}")
    print(f"   Logo:      {logo or '(sem logo)'}")
    print(f"   Erro:      {ec_label.get(error, error)}")
    print(f"   Output:    {out}")
    if show:
        print(f"   Abrir:     sim")
    print(f" {DIM}{'─'*40}{RESET}")

    confirm = input(f"\n {BOLD}?{RESET} Gerar QR code? {DIM}[S/n]{RESET}\n  {DIM}> {RESET}").strip().lower()
    if confirm in ("n", "nao", "no"):
        print(f"\n {YELLOW}Cancelado.{RESET}")
        sys.exit(0)

    print(f"\n {DIM}A gerar QR code...{RESET}")
    try:
        path = generate_qr(
            data=data,
            color=color,
            bg_color=bg,
            logo_path=logo or None,
            logo_size_pct=logo_size,
            output=out,
            error_correction=error,
            show=show,
        )
        print(f"\n {GREEN}{BOLD}✓ QR code gerado!{RESET}")
        print(f"   {path}\n")
    except Exception as e:
        print(f"\n {RED}erro{RESET} {e}")
        sys.exit(1)


# ── Modo Direto (argumentos) ────────────────────────────
def direct_mode(args):
    print(f" {DIM}A gerar QR code...{RESET}")
    try:
        path = generate_qr(
            data=args.data,
            color=args.color,
            bg_color=args.bg,
            logo_path=args.logo,
            logo_size_pct=args.logo_size,
            output=args.output,
            version=args.version,
            box_size=args.box_size,
            border=args.border,
            error_correction=args.error,
            show=args.show,
        )
        print(f" {GREEN}{BOLD}✓ QR code gerado!{RESET} {DIM}{path}{RESET}")
    except Exception as e:
        print(f" {RED}erro{RESET} {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="qrbro — Gerador de QR Codes customizados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("data", nargs="?", help="Texto ou URL para codificar")
    parser.add_argument("--color", default="#000000", help="Cor do QR (hex)")
    parser.add_argument("--bg", default="#FFFFFF", help="Cor de fundo (hex)")
    parser.add_argument("--logo", default=None, help="Caminho do logo (centro)")
    parser.add_argument("--logo-size", type=float, default=25, help="Tamanho do logo em %% do QR")
    parser.add_argument("--output", "-o", default="qrcode.png", help="Ficheiro de saida")
    parser.add_argument("--version", type=int, default=None, help="Versao do QR (1-40)")
    parser.add_argument("--box-size", type=int, default=10, help="Tamanho de cada box (px)")
    parser.add_argument("--border", type=int, default=4, help="Tamanho da borda")
    parser.add_argument("--error", default="H", choices=["L","M","Q","H"], help="Correcao de erro")
    parser.add_argument("--show", action="store_true", help="Abrir a imagem")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmacao")
    parser.add_argument("-h", "--help", action="store_true", help="Mostrar ajuda")

    args = parser.parse_args()

    if args.help or args.data == "help":
        print(LOGO)
        parser.print_help()
        print(f"\n{DIM}Exemplos:{RESET}")
        print(f"  qrbro")
        print(f'  qrbro "https://meusite.com"')
        print(f'  qrbro "texto" --color "#FF5733" --bg "#1a1a2e"')
        print(f'  qrbro "url" --color "#FF5733" --logo logo.png -o meuqr.png')
        return

    if args.data:
        direct_mode(args)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
