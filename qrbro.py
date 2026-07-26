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

PREVIEW_DATA = "https://qr.bro"
BACK_SENTINEL = "<BACK>"
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


# ── Arrow-key picker with live preview ───────────────────
def arrow_picker(title: str, options: list[tuple[str, str]], default: int = 0,
                 preview_fn=None) -> str:
    """Arrow-key navigable picker. ↑↓ move, Enter select, Esc back.
    If preview_fn(selected_val) returns a list of lines, renders them live."""
    idx = default - 1 if 0 <= default - 1 < len(options) else 0

    def render(draw_preview=True):
        out = [f"\n {BOLD}?{RESET} {title}"]
        out.append(f"  {DIM}↑↓  Enter select  Esc back{RESET}")
        for i, (label, _) in enumerate(options):
            indicator = f" {GREEN}▸{RESET}" if i == idx else "  "
            out.append(f"{indicator} {label}")
        out.append("")
        if draw_preview and preview_fn:
            try:
                plines = preview_fn(options[idx][1])
                out.append(f"  {DIM}Preview:{RESET}")
                for l in plines[:15]:
                    out.append(f"    {l}")
            except Exception:
                pass
        return out

    lines = render(draw_preview=False)
    for l in lines:
        print(l)
    total = len(lines) + (min(len(preview_fn(options[0][1])[:15]) if preview_fn else 0, 15) + 1 if preview_fn else 0)

    while True:
        # Draw preview
        preview_extra = 0
        if preview_fn:
            idx_bk = idx
            try:
                plines = preview_fn(options[idx][1])
                preview_extra = min(len(plines), 15) + 1
                print(f"  {DIM}Preview:{RESET}")
                for l in plines[:15]:
                    print(f"    {l}")
            except Exception:
                pass

        key = getch()

        if key == "\x1b[A":  # Up
            if idx > 0:
                idx -= 1
                clear_lines(len(lines) + preview_extra)
                lines = render(draw_preview=False)
                for l in lines:
                    print(l)
            else:
                clear_lines(preview_extra) if preview_extra else None

        elif key == "\x1b[B":  # Down
            if idx < len(options) - 1:
                idx += 1
                clear_lines(len(lines) + preview_extra)
                lines = render(draw_preview=False)
                for l in lines:
                    print(l)
            else:
                clear_lines(preview_extra) if preview_extra else None

        elif key in ("\r", "\n"):  # Enter
            clear_lines(len(lines) + preview_extra)
            print(f" {BOLD}?{RESET} {title} {GREEN}{options[idx][0]}{RESET}")
            return options[idx][1]

        elif key in ("\x1b", "\x7f"):  # Esc or Backspace → go back
            clear_lines(len(lines) + preview_extra)
            return BACK_SENTINEL

        else:
            clear_lines(preview_extra)


def arrow_confirm(label: str, default: bool = True) -> bool:
    """Yes/No picker with arrow keys."""
    opts = [("Yes", "y"), ("No", "n")]
    idx = 0 if default else 1
    lines = [
        f"\n {BOLD}?{RESET} {label}",
        f"  {DIM}← →  Enter confirm  Esc back{RESET}",
        f" {GREEN}▸{RESET}" + " Yes" if idx == 0 else "  Yes",
        f" {GREEN}▸{RESET}" + " No" if idx == 1 else "  No",
        "",
    ]
    for l in lines:
        print(l)

    while True:
        key = getch()
        if key == "\x1b[C":  # Right
            idx = 1
            clear_lines(5)
            lines[2] = f" {GREEN}▸{RESET} Yes" if idx == 0 else "  Yes"
            lines[3] = f" {GREEN}▸{RESET} No" if idx == 1 else "  No"
            for l in lines:
                print(l)
        elif key == "\x1b[D":  # Left
            idx = 0
            clear_lines(5)
            lines[2] = f" {GREEN}▸{RESET} Yes" if idx == 0 else "  Yes"
            lines[3] = f" {GREEN}▸{RESET} No" if idx == 1 else "  No"
            for l in lines:
                print(l)
        elif key in ("\r", "\n"):
            clear_lines(5)
            print(f" {BOLD}?{RESET} {label} {GREEN}{opts[idx][0]}{RESET}")
            return idx == 0
        elif key in ("\x1b", "\x7f"):
            clear_lines(5)
            return BACK_SENTINEL


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


# ── Interactive Mode (state machine with back support) ──
def interactive_mode():
    print(LOGO)
    data = ""
    color = "#000000"
    bg = "#FFFFFF"
    logo = ""
    logo_size = 25
    error = "H"
    step = 0  # current step index

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
            # ── Color scheme (with live preview) ──
            def color_preview(val):
                if val == "8":
                    return []
                pr = COLOR_PRESETS[val]
                return ascii_preview(PREVIEW_DATA, ec=error, color=pr[1])

            presets_list = [(v[0], k) for k, v in COLOR_PRESETS.items()]
            result = arrow_picker("Color scheme", presets_list, default=4,
                                  preview_fn=color_preview)
            if result == BACK_SENTINEL:
                step = 0
                continue
            if result == "8":
                color = prompt_hex("QR color", "#000000")
                bg = prompt_hex("Background color", "#FFFFFF")
            else:
                preset = COLOR_PRESETS[result]
                color, bg = preset[1], preset[2]
            step = 2

        elif step == 2:
            # ── Logo ──
            logo = prompt_str("Logo path (leave empty to skip)")
            if logo:
                sz = prompt_str("Logo size as % of QR", "25")
                try:
                    logo_size = int(sz)
                except ValueError:
                    print(f"  {YELLOW}warning{RESET} Invalid size, using 25%.")
            step = 3

        elif step == 3:
            # ── Error correction (with live preview) ──
            def ec_preview(val):
                return ascii_preview(PREVIEW_DATA, ec=val)

            ec_opts = [("Low (L)", "L"), ("Medium (M)", "M"),
                       ("Quartile (Q)", "Q"), ("High (H)", "H")]
            result = arrow_picker("Error correction level", ec_opts, default=4,
                                  preview_fn=ec_preview)
            if result == BACK_SENTINEL:
                step = 2
                continue
            error = result
            step = 4

        elif step == 4:
            # ── Output ──
            default_out = os.path.expanduser("~/Downloads/qrcode.png")
            out = prompt_str("Output filename", default_out)
            if not out.endswith(".png"):
                out += ".png"
            step = 5

        elif step == 5:
            # ── Show image? ──
            result = arrow_confirm("Open image after generation?", default=False)
            if result == BACK_SENTINEL:
                step = 4
                continue
            show = result
            step = 6

        elif step == 6:
            # ── Summary & Confirm ──
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
            show_preview(data, ec=error)
            print(f" {DIM}{'─'*44}{RESET}")

            result = arrow_confirm("Generate QR code?", default=True)
            if result == BACK_SENTINEL:
                step = 5
                continue

            if result is False:
                print(f"\n {YELLOW}Cancelled.{RESET}")
                sys.exit(0)

            # ── Generate ──
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
            break


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
