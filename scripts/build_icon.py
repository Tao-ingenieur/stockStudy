"""Generate the project's original candlestick icon using only the standard library."""

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "resources"
CANDLES = [(62, 98, 214, 134, 184, "#ff657a"), (124, 68, 192, 104, 151, "#45d6b0"),
           (186, 35, 158, 64, 122, "#ff657a")]


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def png(size):
    def pixel(x, y):
        # Rounded dark background with transparent corners.
        dx, dy = max(30 - x, x - 226, 0), max(30 - y, y - 226, 0)
        if dx * dx + dy * dy > 30 * 30:
            return (0, 0, 0, 0)
        color = (23, 37, 66, 255)
        if 30 < x < 225 and any(abs(y - line) < 1 for line in (84, 140, 196)):
            color = (49, 67, 99, 255)
        for cx, top, bottom, body_top, body_bottom, fill in CANDLES:
            if (abs(x - cx) < 3 and top <= y <= bottom) or (abs(x - cx) < 15 and body_top <= y <= body_bottom):
                color = tuple(bytes.fromhex(fill[1:])) + (255,)
        return color
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            samples = [pixel((x + (a + .5) / 3) * 256 / size, (y + (b + .5) / 3) * 256 / size)
                       for a in range(3) for b in range(3)]
            raw.extend(round(sum(p[c] for p in samples) / 9) for c in range(4))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">',
           '<rect width="256" height="256" rx="30" fill="#172542"/>']
    for y in (84, 140, 196):
        svg.append(f'<path d="M30 {y}H225" stroke="#314363" stroke-width="2"/>')
    for x, top, bottom, body_top, body_bottom, fill in CANDLES:
        svg.append(f'<path d="M{x} {top}V{bottom}" stroke="{fill}" stroke-width="6"/>')
        svg.append(f'<rect x="{x-15}" y="{body_top}" width="30" height="{body_bottom-body_top}" fill="{fill}"/>')
    (ROOT / "candlestick.svg").write_text("\n".join(svg + ["</svg>"]) + "\n", encoding="utf-8")
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = [png(size) for size in sizes]
    (ROOT / "candlestick.png").write_bytes(images[-1])
    offset = 6 + 16 * len(sizes)
    entries = []
    for size, data in zip(sizes, images):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    (ROOT / "candlestick.ico").write_bytes(struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries) + b"".join(images))


if __name__ == "__main__":
    main()
