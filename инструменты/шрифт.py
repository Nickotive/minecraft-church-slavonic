"""Пиксельный шрифт: гнёзда (буква + знаки) → готовые знаки в частной области Юникода.

Координаты буквы: строка 0 — верх прописной, 6 — последняя над основной
линией, 7–8 — вниз; знаки могут уходить до строки -3. В картинке игры
строка r лежит в строке ячейки r + 3; ячейка 16×12, высота 12, подъём 10.
"""
import os
import unicodedata

from PIL import Image

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ПАПКА = os.path.join(КОРЕНЬ, "шрифт")

ОКСИЯ, ВАРИЯ, КАМОРА = "́", "̀", "̑"
ЗВАТЕЛЬЦЕ, ТИТЛО, ПОКРЫТИЕ, ЕРОК = "҆", "҃", "҇", "̾"
БУКВЕННЫЕ = {chr(c) for c in range(0x2DE0, 0x2E00)}
ВСЕ_ЗНАКИ = {ОКСИЯ, ВАРИЯ, КАМОРА, ЗВАТЕЛЬЦЕ, ТИТЛО, ПОКРЫТИЕ, ЕРОК, "̈", "̆", "̏"} | БУКВЕННЫЕ
ЯЧЕЙКА_Ш, ЯЧЕЙКА_В, СДВИГ = 16, 12, 3
ПУА = 0xE000


def _читать(путь):
    рисунки, имя, нач, опора, строки, знаки_от = {}, None, 0, None, [], None

    def сдать():
        if имя is not None:
            клетки = {(x, нач + y) for y, s in enumerate(строки) for x, ch in enumerate(s) if ch == "#"}
            рисунки[имя] = {"клетки": клетки, "опора": опора, "знаки_от": знаки_от,
                            "ширина": max((len(s.rstrip(".")) for s in строки), default=0)}

    for стр in open(путь, encoding="utf-8"):
        стр = стр.rstrip("\n")
        if стр.startswith("#") and not set(стр) <= {"#", "."}:
            continue
        if стр.startswith("= "):
            сдать()
            ч = стр[2:].split()
            имя, нач, опора, строки, знаки_от = ч[0], 0, None, [], None
            for x in ч[1:]:
                if x.startswith("опора="):
                    опора = int(x[6:])
                elif x.startswith("знаки="):
                    знаки_от = int(x[6:])
                else:
                    нач = int(x)
        elif стр.strip() and имя is not None:
            строки.append(стр.strip())
    сдать()
    return рисунки


БУКВЫ = _читать(os.path.join(ПАПКА, "буквы.txt"))
ЗНАКИ = _читать(os.path.join(ПАПКА, "знаки.txt"))


def гнёзда(текст):
    """Строка → список гнёзд (буква, кортеж знаков) или (символ, None) для прочего."""
    s = unicodedata.normalize("NFD", текст)
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in ВСЕ_ЗНАКИ and out and out[-1][1] is not None:
            out[-1][1].append(ch)
            i += 1
            continue
        if ch in "ᲂО" and i + 1 < len(s) and s[i + 1] == "у":
            out.append(["ᲂу" if ch == "ᲂ" else "Оу", []])
            i += 2
            continue
        if ch in БУКВЫ or ch in ("и", "И", "і", "І", "ѵ", "Ѵ"):
            out.append([ch, []])
        else:
            out.append([ch, None])
        i += 1
    # слить составные: й, ї, ѷ
    res = []
    for b, m in out:
        if m is not None:
            if b in "иИ" and "̆" in m:
                b = "й" if b == "и" else "Й"
                m.remove("̆")
            if b in "іІ" and "̈" in m:
                b = "ї" if b == "і" else "Ї"
                m.remove("̈")
            if b == "ѵ" and "̏" in m:
                b = "ѷ"
                m.remove("̏")
            m = tuple(m)
        res.append((b, m))
    return res


def _верх(клетки):
    return min(y for _, y in клетки)


def нарисовать(буква, знаки):
    """Гнездо → множество клеток (x, строка)."""
    if буква not in БУКВЫ:
        raise KeyError(f"нет буквы «{буква}»")
    б = БУКВЫ[буква]
    клетки = set(б["клетки"])
    ширина = max(x for x, _ in клетки) + 1
    прописная = буква[:1].isupper()
    опора = б["опора"] if б["опора"] is not None else (ширина - 1) // 2
    знаки = list(знаки)
    сверху = []  # слои снизу вверх: (рисунок, выравнивание)
    з = ЗВАТЕЛЬЦЕ in знаки
    уд = [x for x in знаки if x in (ОКСИЯ, ВАРИЯ, КАМОРА)]
    if з and уд:
        имя = {ОКСИЯ: "исо", ВАРИЯ: "апостроф", КАМОРА: "звательце+камора"}[уд[0]]
        сверху.append(ЗНАКИ[имя])
    elif з:
        сверху.append(ЗНАКИ["звательце"])
    elif уд:
        сверху.append(ЗНАКИ[{ОКСИЯ: "оксия", ВАРИЯ: "вария", КАМОРА: "камора"}[уд[0]]])
    for x in знаки:
        if x in БУКВЕННЫЕ:
            if x not in ЗНАКИ:
                raise KeyError(f"нет буквенного титла U+{ord(x):04X}")
            сверху.append(ЗНАКИ[x])
    if ПОКРЫТИЕ in знаки:
        сверху.append(ЗНАКИ["покрытие"])
    if ТИТЛО in знаки:
        сверху.append(ЗНАКИ["титло"])
    # между буквой и знаком одна пустая строка; буквенное титло встаёт вплотную
    верх = б["знаки_от"] if б["знаки_от"] is not None else _верх(клетки)
    дно = верх - (1 if any(x in БУКВЕННЫЕ for x in знаки) else 2)
    сдвиг = 0
    слои = []
    for р in сверху:
        кл = р["клетки"]
        h = max(y for _, y in кл) + 1
        w = max(x for x, _ in кл) + 1
        x0 = опора - (w - 1) // 2
        слои.append({(x + x0, y + дно - h + 1) for x, y in кл})
        дно -= h
    for сл in слои:
        сдвиг = max(сдвиг, -min(x for x, _ in сл))
    итог = {(x + сдвиг, y) for x, y in клетки}
    for сл in слои:
        итог |= {(x + сдвиг, y) for x, y in сл}
    if ЕРОК in знаки:
        ш = max(x for x, _ in итог) + 1
        в = _верх(клетки)
        итог |= {(ш, в - 2), (ш, в - 1)}
    for x, y in итог:
        if not (-СДВИГ <= y < ЯЧЕЙКА_В - СДВИГ) or not (0 <= x < ЯЧЕЙКА_Ш):
            raise ValueError(f"гнездо «{буква}{''.join(знаки)}» не помещается в ячейку")
    return итог


def ключ(буква, знаки):
    return буква + "".join(sorted(знаки))


class Набор:
    """Собирает гнёзда, раздаёт номера частной области, пишет картинки."""

    def __init__(self):
        self.номер = {}
        self.рисунок = {}

    def перевести(self, текст):
        out = []
        for б, з in гнёзда(текст):
            if з is None:
                out.append(б)
                continue
            к = ключ(б, з)
            if к not in self.номер:
                self.рисунок[к] = нарисовать(б, з)
                self.номер[к] = chr(ПУА + len(self.номер))
            out.append(self.номер[к])
        # латинские буквы со знаками (имена: Cotán, Åhman) — собрать обратно
        return unicodedata.normalize("NFC", "".join(out))

    def записать(self, папка_текстур, имя="cu"):
        os.makedirs(папка_текстур, exist_ok=True)
        пары = sorted(self.номер.items(), key=lambda kv: kv[1])
        поставщики = []
        for стр in range(0, len(пары), 256):
            кусок = пары[стр:стр + 256]
            img = Image.new("RGBA", (16 * ЯЧЕЙКА_Ш, 16 * ЯЧЕЙКА_В), (0, 0, 0, 0))
            знаки = []
            for n, (к, сим) in enumerate(кусок):
                cx, cy = (n % 16) * ЯЧЕЙКА_Ш, (n // 16) * ЯЧЕЙКА_В
                for x, y in self.рисунок[к]:
                    img.putpixel((cx + x, cy + y + СДВИГ), (255, 255, 255, 255))
                знаки.append(сим)
            знаки += ["\u0000"] * (256 - len(знаки))
            файл = f"{имя}_{стр // 256}.png"
            img.save(os.path.join(папка_текстур, файл))
            поставщики.append({
                "type": "bitmap", "file": f"minecraft:font/{файл}", "height": ЯЧЕЙКА_В, "ascent": 10,
                "chars": ["".join(знаки[r * 16:(r + 1) * 16]) for r in range(16)],
            })
        return поставщики


def образец(строки, набор=None, масштаб=4, путь=None):
    """Нарисовать строки так, как их нарисует игра (шаг = ширина + 1, пробел 4)."""
    набор = набор or Набор()
    линии = []
    for текст in строки:
        x, клетки = 0, []
        for б, з in гнёзда(текст):
            if з is None:
                x += 4 if б == " " else 6
                continue
            кл = нарисовать(б, з)
            клетки += [(x + cx, y) for cx, y in кл]
            x += max(cx for cx, _ in кл) + 2
        линии.append((x, клетки))
    W = max(w for w, _ in линии) + 4
    H = len(линии) * 14 + 4
    img = Image.new("RGB", (W * масштаб, H * масштаб), (255, 255, 255))
    for n, (_, клетки) in enumerate(линии):
        for x, y in клетки:
            X, Y = (x + 2) * масштаб, (n * 14 + 5 + y) * масштаб
            img.paste((20, 20, 20), (X, Y, X + масштаб, Y + масштаб))
        # основная линия бледно
        Y = (n * 14 + 5 + 7) * масштаб
        img.paste((215, 225, 245), (0, Y, W * масштаб, Y + 1))
    if путь:
        img.save(путь)
    return img
