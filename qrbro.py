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

COLOR_PRESETS = {
    "1": ("Classic black", "#000000", "#FFFFFF"),
    "2": ("Night mode", "#00FF88", "#0D1117"),
    "3": ("Royal", "#FFD700", "#1a1a2e"),
    "4": ("Fire", "#FF5733", "#1a0a00"),
    "5": ("Ocean", "#00BFFF", "#001830"),
    "6": ("Neon pink", "#FF1493", "#000000"),
    "7": ("Minimal", "#333333", "#FFFFFF"),
    "8": ("Custom", None, None),
}
EC_OPTIONS = [("Low (L)", "L"), ("Medium (M)", "M"), ("Quartile (Q)", "Q"), ("High (H)", "H")]


# ── Terminal helpers ─────────────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def getch() -> str:
    """Read a single keypress. Returns escape sequences for arrow keys."""
    import termios, tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            nxt = sys.stdin.read(2)
            return ch + nxt
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear_lines(n: int):
    """Move cursor up n lines and clear them."""
    for _ in range(n):
        sys.stdout.write("\033[F\033[K")
    sys.stdout.flush()


# ── Arrow-key picker ─────────────────────────────────────
def arrow_picker(title: str, options: list[tuple[str, str]], default: int = 0) -> str:
    """Arrow-key navigable picker. ↑↓ to move, Enter to select."""
    idx = default - 1 if 0 <= default - 1 < len(options) else 0
    total = len(options) + 4  # title + header + options + blank line

    print(f"\n {BOLD}?{RESET} {title}")
    print(f"  {DIM}↑↓ navigate  Enter select{RESET}")
    for i, (label, _) in enumerate(options):
        indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
        print(f"{indicator} {label}")
    print()

    while True:
        key = getch()
        if key == "\x1b[A":  # Up
            if idx > 0:
                idx -= 1
                # redraw indicators
                lines_to_redraw = total - 1
                clear_lines(lines_to_redraw)
                print(f" {BOLD}?{RESET} {title}")
                print(f"  {DIM}↑↓ navigate  Enter select{RESET}")
                for i, (label, _) in enumerate(options):
                    indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
                    print(f"{indicator} {label}")
                print()
        elif key == "\x1b[B":  # Down
            if idx < len(options) - 1:
                idx += 1
                lines_to_redraw = total - 1
                clear_lines(lines_to_redraw)
                print(f" {BOLD}?{RESET} {title}")
                print(f"  {DIM}↑↓ navigate  Enter select{RESET}")
                for i, (label, _) in enumerate(options):
                    indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
                    print(f"{indicator} {label}")
                print()
        elif key in ("\r", "\n"):  # Enter
            break

    # Clear the picker lines
    clear_lines(total)
    print(f" {BOLD}?{RESET} {title} {GREEN}{options[idx][0]}{RESET}")
    return options[idx][1]


def arrow_confirm(label: str, default: bool = True) -> bool:
    """Yes/No picker with arrow keys."""
    opts = [("Yes", "y"), ("No", "n")]
    idx = 0 if default else 1
    total = 4

    print(f"\n {BOLD}?{RESET} {label}")
    print(f"  {DIM}← → navigate  Enter confirm{RESET}")
    for i, (lbl, _) in enumerate(opts):
        indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
        print(f"{indicator} {lbl}")
    print()

    while True:
        key = getch()
        if key == "\x1b[C":  # Right
            idx = 1
            clear_lines(total)
            print(f" {BOLD}?{RESET} {label}")
            print(f"  {DIM}← → navigate  Enter confirm{RESET}")
            for i, (lbl, _) in enumerate(opts):
                indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
                print(f"{indicator} {lbl}")
            print()
        elif key == "\x1b[D":  # Left
            idx = 0
            clear_lines(total)
            print(f" {BOLD}?{RESET} {label}")
            print(f"  {DIM}← → navigate  Enter confirm{RESET}")
            for i, (lbl, _) in enumerate(opts):
                indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
                print(f"{indicator} {lbl}")
            print()
        elif key in ("\r", "\n"):
            break

    clear_lines(total)
    print(f" {BOLD}?{RESET} {label} {GREEN}{opts[idx][0]}{RESET}")
    return idx == 0


# ── ASCII QR Preview ─────────────────────────────────────
def ascii_preview(data: str, color: str, bg: str, ec: str = "H",
                  logo_path: str | None = None, logo_size: int = 25,
                  max_size: int = 21) -> list[str]:
    """Generate a small ASCII QR preview using the module matrix directly."""
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

    fr, fg, fb = hex_to_rgb(color)
    br, bg_c, bb = hex_to_rgb(bg)

    fc = f"\033[38;2;{fr};{fg};{fb}m"
    bc_s = f"\033[48;2;{br};{bg_c};{bb}m"
    reset_c = "\033[0m"

    modules = qr.modules  # True = dark module
    lines = []
    for row in modules:
        line = ""
        for cell in row:
            if cell:
                line += f"{bc_s}{fc}██{reset_c}"
            else:
                line += f"{bc_s}  {reset_c}"
        lines.append(line)

    return lines


def show_preview(data: str, color: str, bg: str, ec: str = "H",
                 logo_path: str | None = None, logo_size: int = 25):
    """Render ASCII QR preview to terminal."""
    try:
        lines = ascii_preview(data, color, bg, ec, logo_path, logo_size)
        print(f"  {DIM}Preview ({len(data)} chars, ec={ec}):{RESET}")
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


# ── QR Generation ────────────────────────────────────────
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

    img = qr.make_image(fill_color=color, back_color=bg_color).convert("RGBA")

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
def interactive_mode():
    print(LOGO)
    data = ""
    color = "#000000"
    bg = "#FFFFFF"
    logo = ""
    logo_size = 25
    error = "H"

    # 1. Data
    print()
    while True:
        data = prompt_str("URL or text to encode", required=True)
        if data:
            break

    show_preview(data, color, bg, error)

    # 2. Color scheme picker (arrow keys)
    presets_list = [(v[0], k) for k, v in COLOR_PRESETS.items()]
    color_choice = arrow_picker("Color scheme", presets_list, default=4)

    if color_choice == "8":
        color = prompt_hex("QR color", "#000000")
        bg = prompt_hex("Background color", "#FFFFFF")
    else:
        preset = COLOR_PRESETS[color_choice]
        color, bg = preset[1], preset[2]

    show_preview(data, color, bg, error)

    # 3. Logo
    logo = prompt_str("Logo path (leave empty to skip)")
    if logo:
        sz = prompt_str("Logo size as % of QR", "25")
        try:
            logo_size = int(sz)
        except ValueError:
            print(f"  {YELLOW}warning{RESET} Invalid size, using 25%.")

    # 4. Error correction picker
    error = arrow_picker("Error correction level", EC_OPTIONS, default=4)
    show_preview(data, color, bg, error, logo if logo else None, logo_size)

    # 5. Output
    default_out = os.path.expanduser("~/Downloads/qrcode.png")
    out = prompt_str("Output filename", default_out)
    if not out.endswith(".png"):
        out += ".png"

    # 6. Show image?
    show = arrow_confirm("Open image after generation?", default=False)

    # ── Summary ────────────────────────────────────────
    ec_label = {"L": "Low", "M": "Medium", "Q": "Quartile", "H": "High"}
    print(f"\n {DIM}{'─'*44}{RESET}")
    print(f" {BOLD}Summary:{RESET}")
    print(f"   Data:     {data}")
    print(f"   QR color: {color}")
    print(f"   BG color: {bg}")
    print(f"   Logo:     {logo or '(none)'}")
    print(f"   Error:    {ec_label.get(error, error)}")
    print(f"   Output:   {out}")
    print(f"   Open:     {'yes' if show else 'no'}")
    show_preview(data, color, bg, error, logo if logo else None, logo_size)
    print(f" {DIM}{'─'*44}{RESET}")

    if not arrow_confirm("Generate QR code?", default=True):
        print(f"\n {YELLOW}Cancelled.{RESET}")
        sys.exit(0)

    print(f"\n {DIM}Generating QR code...{RESET}")
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
        print(f"\n {GREEN}{BOLD}✓ QR code generated!{RESET}")
        print(f"   {path}\n")
    except Exception as e:
        print(f"\n {RED}error{RESET} {e}")
        sys.exit(1)


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
