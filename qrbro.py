#!/usr/bin/env python3
"""
qrbro — Custom QR code generator with colors and center logo.

USAGE:
    qrbro                        # Interactive mode (arrow keys + live ASCII preview)
    qrbro "text or URL"          # Direct mode (optional flags)
    qrbro --help                 # Show help

OPTIONS (direct mode):
    --color HEX         QR color (default: #000000)
    --bg HEX            Background color (default: #FFFFFF)
    --logo PATH         Logo image path (centered)
    --logo-size PCT     Logo size as %% of QR (default: 25)
    --output PATH       Output file (default: ~/Downloads/qrcode.png)
    --version VER       QR version 1-40 (default: auto)
    --box-size N        Box size in px (default: 10)
    --border N          Border thickness (default: 4)
    --error L/M/Q/H     Error correction level (default: H)
    --show              Open image after generation
    -y                  Skip confirmation (non-interactive)
"""

import argparse
import signal
import sys
import os

try:
    import qrcode
    from PIL import Image
except ImportError:
    print(" Missing dependencies. Installing automatically...")
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
        print(" ERROR: Could not install dependencies.")
        print(" Try manually: pip install qrcode[pil] Pillow")
        sys.exit(1)

    try:
        import qrcode
        from PIL import Image
    except ImportError:
        print(" ERROR: Failed to import after installation.")
        print(" Try manually: pip install qrcode[pil] Pillow")
        sys.exit(1)


# ── ANSI Colors ──────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
LOGO = f"""{CYAN}
 ________  ________                 ________  ________  ________     
|\\   __  \\|\\   __  \\               |\\   __  \\|\\   __  \\|\\   __  \\    
\\ \\  \\|\\  \\ \\  \\|\\  \\  ____________\\ \\  \\|\\ /\\ \\  \\|\\  \\ \\  \\|\\  \\   
 \\ \\  \\\\  \\ \\   _  _\\|\\____________\\ \\   __  \\ \\   _  _\\ \\  \\\\  \\  
  \\ \\  \\\\  \\ \\  \\\\  \\\\|____________|\\ \\  \\|\\  \\ \\  \\\\  \\\\ \\  \\\\  \\ 
   \\ \\_____  \\ \\__\\\\ _\\               \\ \\_______\\ \\__\\\\ _\\\\ \\_______\\
    \\|___| \\__\\|__|\\|__|               \\|_______|\\|__|\\|__|\\|_______|
          \\|__|                                                      {RESET}
   {DIM}qrbro — QR Code Builder{RESET}"""


# ── Terminal helpers ─────────────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ── ASCII QR Preview ─────────────────────────────────────
def ascii_preview(data: str, ec: str = "H", stride: int = 2, max_rows: int = 15,
                  color: str = None, **kwargs) -> list[str]:
    """ASCII QR preview. @@ for dark, spaces for light.
    If color is given, dark modules render in that color (ANSI fg).
    stride > 1 shrinks the preview (every Nth row/col)."""
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    qr = qrcode.QRCode(
        error_correction=ec_map.get(ec, qrcode.constants.ERROR_CORRECT_H),
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    fc = ""
    rc = ""
    if color:
        r, g, b = hex_to_rgb(color)
        fc = f"\033[38;2;{r};{g};{b}m"
        rc = "\033[0m"

    modules = qr.modules
    out = []
    for ri in range(0, len(modules), stride):
        row = ""
        for ci in range(0, len(modules[ri]), stride):
            if modules[ri][ci]:
                row += f"{fc}@@{rc}" if fc else "@@"
            else:
                row += "  "
        out.append(row)
        if len(out) >= max_rows:
            break
    return out


def show_preview(data: str, **kwargs):
    """Draw ASCII QR preview."""
    try:
        lines = ascii_preview(data, **kwargs)
        print(f"  {DIM}Preview ({len(data)} chars):{RESET}")
        for line in lines:
            print(f"  {line}")
    except Exception:
        print(f"  {DIM}Preview unavailable{RESET}")


def prompt_str(label: str, default: str = "", required: bool = False) -> str:
    while True:
        val = input(f"  {BOLD}?{RESET} {label} {DIM}[{default}]:{RESET} ").strip()
        if not val:
            if required:
                print(f"  {RED}This field is required.{RESET}")
                continue
            return default
        return val


def prompt_hex(label: str, default: str) -> str:
    val = input(f"  {BOLD}?{RESET} {label} {DIM}[{default}]:{RESET} ").strip()
    if not val:
        return default
    return f"#{val.lstrip('#')}"


def prompt_yesno(label: str, default: bool = True) -> bool:
    """Simple [Y/n] or [y/N] prompt."""
    hint = "Y/n" if default else "y/N"
    while True:
        val = input(f"  {BOLD}?{RESET} {label} {DIM}[{hint}]:{RESET} ").strip().lower()
        if not val:
            return default
        if val in ("y", "yes", "s", "sim"):
            return True
        if val in ("n", "no"):
            return False
        print(f"  {YELLOW}Please answer Y or N.{RESET}")


# ── QR Generation ────────────────────────────────────────
def _round_corners(img: Image.Image, radius: int = None) -> Image.Image:
    """Apply rounded corners to an RGBA image."""
    if radius is None:
        radius = max(8, min(img.size) // 20)
    from PIL import ImageDraw
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    w, h = img.size
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def generate_qr(
    data: str,
    color: str = "#000000",
    bg_color: str = "#FFFFFF",
    logo_path: str | None = None,
    logo_size_pct: float = 25,
    output: str = "",
    version: int | None = None,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "H",
    show: bool = False,
    style: str = "rounded",
) -> str:

    if not output:
        output = os.path.expanduser("~/Downloads/qrcode.png")

    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    ec = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_H)

    if logo_path and error_correction.upper() in ("L", "M"):
        print(f" {YELLOW}warning{RESET} With center logo, use H or Q error correction.")

    qr = qrcode.QRCode(
        version=version or None,
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Styled generation with rounded modules
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    from qrcode.image.styles.colormasks import SolidFillColorMask

    fc_rgb = hex_to_rgb(color)
    bc_rgb = hex_to_rgb(bg_color)
    drawer = RoundedModuleDrawer()

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        color_mask=SolidFillColorMask(
            back_color=(*bc_rgb, 255),
            front_color=(*fc_rgb, 255),
        ),
    ).convert("RGBA")

    # Apply rounded outer corners
    img = _round_corners(img)

    # Center logo
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
            print(f" {YELLOW}warning{RESET} Logo error: {e}")

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    img.save(output, "PNG")
    return os.path.abspath(output)


# ── Interactive Mode ─────────────────────────────────────
def _confirm_quit() -> bool:
    """Ask user if they want to quit. Returns True if quitting."""
    return prompt_yesno("Quit QR-Bro?", default=False)


def interactive_mode():
    print(LOGO)
    data = ""
    color = "#000000"
    bg = "#FFFFFF"
    error = "H"
    step = 0

    signal.signal(signal.SIGINT, signal.default_int_handler)
    show = False

    try:
        while True:
            if step == 0:
                # ── Data ──
                while True:
                    data = prompt_str("URL or text to encode", required=True)
                    if data:
                        break
                show_preview(data, ec=error)
                step = 1

            elif step == 1:
                # ── QR color & background ──
                color = prompt_hex("QR color (hex)", "#000000")
                bg = prompt_hex("Background color (hex)", "#FFFFFF")
                step = 2

            elif step == 2:
                # ── Show image? ──
                show = prompt_yesno("Open image after generation?", default=False)
                step = 3

            elif step == 3:
                # ── Summary & Generate ──
                default_out = os.path.expanduser("~/Downloads/qrcode.png")
                out = default_out
                print(f"\n {DIM}{'─'*44}{RESET}")
                print(f" {BOLD}Summary:{RESET}")
                print(f"   Data:     {data}")
                print(f"   QR color: {color}")
                print(f"   BG color: {bg}")
                print(f"   Output:   {out}")
                print(f"   Open:     {'yes' if show else 'no'}")
                show_preview(data, ec=error)
                print(f" {DIM}{'─'*44}{RESET}")

                print(f"\n {DIM}Generating QR code...{RESET}")
                try:
                    path = generate_qr(
                        data=data,
                        color=color,
                        bg_color=bg,
                        output=out,
                        error_correction=error,
                        show=show,
                    )
                    print(f"\n {GREEN}{BOLD}✓ QR code generated!{RESET}")
                    print(f"   {path}\n")
                except Exception as e:
                    print(f"\n {RED}error{RESET} {e}")
                    sys.exit(1)
                break
    except KeyboardInterrupt:
        if _confirm_quit():
            print(f" {YELLOW}Bye.{RESET}")
        else:
            interactive_mode()


# ── Direct Mode ──────────────────────────────────────────
def direct_mode(args):
    print(f" {DIM}Generating QR code...{RESET}")
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
        print(f" {GREEN}{BOLD}✓ QR code generated!{RESET} {DIM}{path}{RESET}")
    except Exception as e:
        print(f" {RED}error{RESET} {e}")
        sys.exit(1)


# ── Entrypoint ───────────────────────────────────────────
def main():
    default_out = os.path.expanduser("~/Downloads/qrcode.png")

    parser = argparse.ArgumentParser(
        description="qrbro — Custom QR code generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("data", nargs="?", help="Text or URL to encode")
    parser.add_argument("--color", default="#000000", help="QR color (hex)")
    parser.add_argument("--bg", default="#FFFFFF", help="Background color (hex)")
    parser.add_argument("--logo", default=None, help="Logo image path (center)")
    parser.add_argument("--logo-size", type=float, default=25, help="Logo size as %% of QR")
    parser.add_argument("--output", "-o", default=default_out, help="Output file")
    parser.add_argument("--version", type=int, default=None, help="QR version (1-40)")
    parser.add_argument("--box-size", type=int, default=10, help="Box size in px")
    parser.add_argument("--border", type=int, default=4, help="Border thickness")
    parser.add_argument("--error", default="H", choices=["L","M","Q","H"], help="Error correction")
    parser.add_argument("--show", action="store_true", help="Open image after generation")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")

    args = parser.parse_args()

    if args.help or args.data == "help":
        print(LOGO)
        parser.print_help()
        print(f"\n{DIM}Examples:{RESET}")
        print(f"  qrbro")
        print(f'  qrbro "https://example.com"')
        print(f'  qrbro "hello" --color "#FF5733" --bg "#1a1a2e"')
        print(f'  qrbro "url" --color "#FF5733" --logo logo.png -o output.png')
        return

    if args.data:
        direct_mode(args)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
