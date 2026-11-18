"""A deterministic, entirely drawn newspaper. Python standard library only."""
import binascii
import os
import struct
import zlib
from pathlib import Path

# Each slash separates one row of a hand-defined 5 by 7 bitmap.
FONT_DATA = {
 'A':'01110/10001/10001/11111/10001/10001/10001',
 'B':'11110/10001/10001/11110/10001/10001/11110',
 'C':'01111/10000/10000/10000/10000/10000/01111',
 'D':'11110/10001/10001/10001/10001/10001/11110',
 'E':'11111/10000/10000/11110/10000/10000/11111',
 'F':'11111/10000/10000/11110/10000/10000/10000',
 'G':'01111/10000/10000/10111/10001/10001/01111',
 'H':'10001/10001/10001/11111/10001/10001/10001',
 'I':'11111/00100/00100/00100/00100/00100/11111',
 'J':'00111/00010/00010/00010/10010/10010/01100',
 'K':'10001/10010/10100/11000/10100/10010/10001',
 'L':'10000/10000/10000/10000/10000/10000/11111',
 'M':'10001/11011/10101/10101/10001/10001/10001',
 'N':'10001/11001/10101/10011/10001/10001/10001',
 'O':'01110/10001/10001/10001/10001/10001/01110',
 'P':'11110/10001/10001/11110/10000/10000/10000',
 'Q':'01110/10001/10001/10001/10101/10010/01101',
 'R':'11110/10001/10001/11110/10100/10010/10001',
 'S':'01111/10000/10000/01110/00001/00001/11110',
 'T':'11111/00100/00100/00100/00100/00100/00100',
 'U':'10001/10001/10001/10001/10001/10001/01110',
 'V':'10001/10001/10001/10001/10001/01010/00100',
 'W':'10001/10001/10001/10101/10101/10101/01010',
 'X':'10001/10001/01010/00100/01010/10001/10001',
 'Y':'10001/10001/01010/00100/00100/00100/00100',
 'Z':'11111/00001/00010/00100/01000/10000/11111',
 '0':'01110/10001/10011/10101/11001/10001/01110',
 '1':'00100/01100/00100/00100/00100/00100/01110',
 '2':'01110/10001/00001/00010/00100/01000/11111',
 '3':'11110/00001/00001/01110/00001/00001/11110',
 '4':'00010/00110/01010/10010/11111/00010/00010',
 '5':'11111/10000/10000/11110/00001/00001/11110',
 '6':'01110/10000/10000/11110/10001/10001/01110',
 '7':'11111/00001/00010/00100/01000/01000/01000',
 '8':'01110/10001/10001/01110/10001/10001/01110',
 '9':'01110/10001/10001/01111/00001/00001/01110',
 '.':'00000/00000/00000/00000/00000/00110/00110',
 ',':'00000/00000/00000/00000/00110/00100/01000',
 ':':'00000/00110/00110/00000/00110/00110/00000',
 ';':'00000/00110/00110/00000/00110/00100/01000',
 "'":'00100/00100/01000/00000/00000/00000/00000',
 '-':'00000/00000/00000/11111/00000/00000/00000',
 '/':'00001/00010/00010/00100/01000/01000/10000',
 '$':'00100/01111/10100/01110/00101/11110/00100',
 '%':'11001/11010/00010/00100/01000/01011/10011',
 '&':'01100/10010/10100/01000/10101/10010/01101',
 '(':'00010/00100/01000/01000/01000/00100/00010',
 ')':'01000/00100/00010/00010/00010/00100/01000',
 '!':'00100/00100/00100/00100/00100/00000/00100',
 '?':'01110/10001/00001/00010/00100/00000/00100',
 '—':'00000/00000/00000/11111/00000/00000/00000',
 ' ':'00000/00000/00000/00000/00000/00000/00000',
}
PAPER = (248, 245, 234)
INK = (24, 39, 46)
RED = (166, 49, 39)
TEAL = (29, 102, 104)
W = H = 1024


class Canvas:
    def __init__(self):
        self.rows = [bytearray(bytes(PAPER) * W) for _ in range(H)]

    def rect(self, x, y, w, h, color=INK):
        for yy in range(max(0, y), min(H, y + h)):
            a, b = max(0, x), min(W, x + w)
            if b > a:
                self.rows[yy][a*3:b*3] = bytes(color) * (b-a)

    def border(self, x, y, w, h, color=INK, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y+h-t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x+w-t, y, t, h, color)

    def line(self, x, y, xx, yy, color=INK, t=3):
        dx, dy = abs(xx-x), -abs(yy-y)
        sx, sy = (1 if x < xx else -1), (1 if y < yy else -1)
        err = dx + dy
        while True:
            self.rect(x-t//2, y-t//2, t, t, color)
            if (x, y) == (xx, yy):
                break
            e = 2*err
            if e >= dy:
                err += dy
                x += sx
            if e <= dx:
                err += dx
                y += sy

    def circle(self, x, y, r, color=INK, t=3):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if (r-t)**2 <= dx*dx+dy*dy <= r*r:
                    self.rect(x+dx, y+dy, 1, 1, color)

    def glyph(self, x, y, ch, s, color):
        for yy, row in enumerate(FONT_DATA[ch].split('/')):
            for xx, bit in enumerate(row):
                if bit == '1':
                    self.rect(x+xx*s, y+yy*s, s, s, color)

    def text(self, x, y, words, s=2, color=INK):
        for ch in words.upper():
            self.glyph(x, y, ch, s, color)
            x += 6*s

    def wrap(self, x, y, words, width, s=2, color=INK, gap=5):
        line = ''
        for word in words.upper().split():
            trial = (line+' '+word).strip()
            if len(trial)*6*s-s > width:
                self.text(x, y, line, s, color)
                y += 7*s+gap
                line = word
            else:
                line = trial
        self.text(x, y, line, s, color)
        return y+7*s

    def png(self):
        def chunk(tag, data):
            return (struct.pack('>I', len(data)) + tag + data +
                    struct.pack('>I', binascii.crc32(tag+data) & 0xffffffff))
        raw = b''.join(b'\0'+bytes(row) for row in self.rows)
        return (b'\x89PNG\r\n\x1a\n' +
                chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def icon(c, kind, x, y, color):
    if kind == 'strike':
        for dx, dy in [(0,-30),(22,-22),(30,0),(22,22),(0,30),(-22,22),(-30,0),(-22,-22)]:
            c.line(x+dx//2, y+dy//2, x+dx, y+dy, color, 5)
        c.circle(x, y, 10, color, 5)
    elif kind == 'bridge':
        c.line(x-32,y-9,x+32,y-9,color,5)
        for dx in [-26,26]:
            c.line(x+dx,y-9,x+dx,y+17,color,5)
        c.line(x-24,y-10,x-10,y-27,color,4)
        c.line(x-10,y-27,x+10,y-27,color,4)
        c.line(x+10,y-27,x+24,y-10,color,4)
        c.rect(x+2,y-14,10,12,PAPER)
        for dx in [-30,-10,10]:
            c.line(x+dx,y+27,x+dx+10,y+22,color,3)
            c.line(x+dx+10,y+22,x+dx+20,y+27,color,3)
    elif kind == 'climate':
        c.circle(x,y,29,color)
        c.circle(x,y,15,color)
        c.line(x-27,y,x+27,y,color)
        c.line(x,y-27,x,y+27,color)
        c.line(x-21,y-16,x+21,y-16,color)
        c.line(x-21,y+16,x+21,y+16,color)
    elif kind == 'summit':
        for dx in [-24,0,24]:
            c.circle(x+dx,y-15,8,color,5)
            c.line(x+dx,y-1,x+dx,y+16,color,7)
        c.line(x-31,y+24,x+31,y+24,color,4)
    elif kind == 'health':
        for a,b,aa,bb in [(-27,-27,27,-27),(27,-27,25,10),(25,10,0,31),(0,31,-25,10),(-25,10,-27,-27)]:
            c.line(x+a,y+b,x+aa,y+bb,color,4)
        c.rect(x-5,y-17,10,31,color)
        c.rect(x-15,y-7,30,10,color)
    else:
        c.border(x-22,y-22,44,44,color,4)
        c.border(x-11,y-11,22,22,color,3)
        for d in [-14,0,14]:
            c.line(x+d,y-31,x+d,y-23,color)
            c.line(x+d,y+23,x+d,y+31,color)
            c.line(x-31,y+d,x-23,y+d,color)
            c.line(x+23,y+d,x+31,y+d,color)


def panel(c, x, y, w, h, label, kind, headline, body, color=TEAL):
    c.rect(x,y,w,3,INK)
    icon_y = y+44 if h < 150 else y+54
    icon(c,kind,x+40,icon_y,color)
    c.text(x+88,y+17,label,2,color)
    end = c.wrap(x+88,y+44,headline,w-100,4)
    body_offset = 78 if h < 150 else 112
    headline_gap = 10 if h < 150 else 14
    bottom = c.wrap(x+12,max(y+body_offset,end+headline_gap),body,w-24,2,gap=6)
    assert bottom <= y+h-8, (label, bottom, y+h)


def render():
    c = Canvas()
    c.rect(24,24,976,10,INK)
    c.text(38,49,'THE WORLD LEDGER',7)
    c.text(40,116,'TUESDAY 17 NOVEMBER 2026',4,RED)
    c.rect(24,160,976,3,INK)
    c.text(40,174,'ONE DAY / SIX STORIES / A DRAWN FRONT PAGE',2)
    panel(c,28,207,968,177,'01 / MIDDLE EAST','strike',
          'U.S. STRIKES IRAN',
          'U.S. jets strike an Iranian missile site on Qeshm Island. Iran fired drones at a U.S. radar base in Bahrain; a fourth tanker hit a mine in the Strait of Hormuz.',RED)
    panel(c,28,397,472,205,'02 / UKRAINE','bridge',
          'KERCH BRIDGE HIT',
          'Ukraine strikes the bridge to Crimea; a road span falls into the strait. Russia closes it to traffic and hits Kyiv bridges in reply.')
    panel(c,524,397,472,205,'03 / CLIMATE','climate',
          'COP31 DRAFT DEAL',
          'Antalya draft urges faster fossil-fuel phase-out. Climate finance for developing nations rises to $120bn a year by 2035.')
    panel(c,28,619,472,205,'04 / DIPLOMACY','summit',
          'SHENZHEN SUMMIT',
          'Trump, Xi and Putin to hold their first three-way summit on Thursday, on the sidelines of the APEC summit in Shenzhen.')
    panel(c,524,619,472,205,'05 / HEALTH','health',
          'MEASLES STATUS LOST',
          'U.S. loses measles-free status after 26 years: over 5,400 cases, 10 deaths. Mexico and Bolivia also lose the status.',RED)
    panel(c,28,839,968,127,'06 / TECHNOLOGY','chip',
          'NVIDIA: STRONG RESULTS',
          "Nvidia posts strong results after Jensen Huang's exit and will not reinstate him. U.S. tightens AI chip controls on China.")
    c.rect(28,978,968,2,INK)
    c.text(50,988,'TUESDAY 17 NOVEMBER 2026 — THE WORLD IN ONE IMAGE',2)
    c.text(278,1007,'DRAWN BY A PROGRAM. NO PHOTOGRAPHS.',2)
    return c.png()


if __name__ == '__main__':
    target = Path(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output'))
    target.mkdir(parents=True, exist_ok=True)
    (target / 'entry.png').write_bytes(render())
