#!/usr/bin/env python3
"""
QRGen — Gerador de QR Codes com customização (cores, logo no centro).

Uso:
    qrgen "texto ou URL" [opções]

Opções:
    --color HEX         Cor do QR (ex: #FF5733)
    --bg HEX            Cor de fundo (ex: #FFFFFF)
    --logo PATH         Caminho para imagem do logo (centro)
    --logo-size PCT     Tamanho do logo em %% do QR (def: 25)
    --output PATH       Ficheiro de saída (def: qrcode.png)
    --version VER       Versão do QR (1-40, def: auto)
    --box-size N        Tamanho de cada box em px (def: 10)
    --border N          Tamanho da borda em boxes (def: 4)
    --error LOW/M/Q/H   Nível de correção de erro (def: H)
    --show              Abrir a imagem depois de gerar
    --help              Mostrar esta ajuda
"""

import argparse
import sys
import os

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    from PIL import Image, ImageColor
except ImportError:
    print("ERRO: Dependências em falta. Instala com:", file=sys.stderr)
    print("  pip install qrcode[pil] Pillow", file=sys.stderr)
    sys.exit(1)


def hex_to_rgb(hex_color: str) -> tuple:
    """Converte hex (#RRGGBB ou #RGB) para tuplo RGB."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def add_logo(qr_img: Image.Image, logo_path: str, logo_size_pct: float = 25) -> Image.Image:
    """Sobreponho o logo ao centro do QR code."""
    if not os.path.isfile(logo_path):
        print(f"AVISO: Ficheiro do logo não encontrado: {logo_path}", file=sys.stderr)
        return qr_img

    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception as e:
        print(f"AVISO: Erro ao abrir logo: {e}", file=sys.stderr)
        return qr_img

    # Redimensionar logo para percentagem do QR
    qr_w, qr_h = qr_img.size
    logo_size = int(min(qr_w, qr_h) * logo_size_pct / 100)
    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)

    # Criar máscara redonda (opcional — mais bonito)
    mask = Image.new("L", logo.size, 0)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, logo.size[0], logo.size[1]), fill=255)

    # Posição central
    pos_x = (qr_w - logo.size[0]) // 2
    pos_y = (qr_h - logo.size[1]) // 2

    # Colar com máscara
    qr_img.paste(logo, (pos_x, pos_y), mask)
    return qr_img


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
    """Gera um QR code com as opções fornecidas."""

    # Mapear nível de correção de erro
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    ec = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_H)

    # Se for usar logo com correção baixa, avisar
    if logo_path and error_correction.upper() in ("L", "M"):
        print("AVISO: Com logo no centro, recomenda-se nível H ou Q de correção de erro.", file=sys.stderr)

    # Criar QR code
    qr = qrcode.QRCode(
        version=version or None,  # None = auto
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Converter cores
    fill_rgb = hex_to_rgb(color)
    back_rgb = hex_to_rgb(bg_color)

    # Gerar imagem
    img = qr.make_image(
        fill_color=color,
        back_color=bg_color,
    ).convert("RGBA")

    # Aplicar cores manualmente (fill_color/back_color já trata no PIL básico,
    # mas garantimos com manipulação direta)
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < 128 and g < 128 and b < 128:  # módulo (preto original)
                pixels[x, y] = (*fill_rgb, a)
            elif r > 200 and g > 200 and b > 200:  # fundo (branco original)
                pixels[x, y] = (*back_rgb, a)

    # Adicionar logo ao centro
    if logo_path:
        img = add_logo(img, logo_path, logo_size_pct)

    # Guardar
    img.save(output, "PNG")
    abs_path = os.path.abspath(output)

    if show:
        try:
            img.show()
        except Exception as e:
            print(f"AVISO: Não foi possível abrir a imagem: {e}", file=sys.stderr)

    return abs_path


def main():
    parser = argparse.ArgumentParser(
        description="QRGen — Gera QR Codes customizados com cores e logo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("data", nargs="?", help="Texto ou URL para codificar")
    parser.add_argument("--color", default="#000000", help="Cor do QR (hex, ex: #FF5733)")
    parser.add_argument("--bg", default="#FFFFFF", help="Cor de fundo (hex, ex: #FFFFFF)")
    parser.add_argument("--logo", default=None, help="Caminho para imagem do logo (centro)")
    parser.add_argument("--logo-size", type=float, default=25, help="Tamanho do logo em %% do QR (def: 25)")
    parser.add_argument("--output", "-o", default="qrcode.png", help="Ficheiro de saída (def: qrcode.png)")
    parser.add_argument("--version", type=int, default=None, help="Versão do QR (1-40, def: auto)")
    parser.add_argument("--box-size", type=int, default=10, help="Tamanho de cada box em px (def: 10)")
    parser.add_argument("--border", type=int, default=4, help="Tamanho da borda (def: 4)")
    parser.add_argument("--error", default="H", choices=["L", "M", "Q", "H"],
                        help="Nível de correção de erro (def: H)")
    parser.add_argument("--show", action="store_true", help="Abrir a imagem depois de gerar")

    args = parser.parse_args()

    # Se não houver data, mostrar ajuda
    if not args.data:
        parser.print_help()
        print("\n\nExemplos:")
        print("  qrgen https://meusite.com")
        print('  qrgen "Olá mundo" --color "#FF5733" --bg "#000000"')
        print("  qrgen https://meusite.com --color #FF5733 --logo logo.png -o meuqr.png")
        sys.exit(1)

    try:
        out = generate_qr(
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
        print(f"✓ QR code gerado: {out}")
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
