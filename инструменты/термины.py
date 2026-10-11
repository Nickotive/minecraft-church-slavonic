"""Собрать ТЕРМИНЫ.md — таблицу названий прямо из перевода.

    python термины.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import словарь  # noqa: E402

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

РАЗДЕЛЫ = [
    ("Существа", "entity.minecraft."),
    ("Действия зелий", "effect.minecraft."),
    ("Чары", "enchantment.minecraft."),
    ("Местности (биомы)", "biome.minecraft."),
    ("Блоки", "block.minecraft."),
    ("Предметы", "item.minecraft."),
]


def main():
    en = json.load(open(os.path.join(КОРЕНЬ, "source", "en_us.json"), encoding="utf-8"))
    ru = json.load(open(os.path.join(КОРЕНЬ, "source", "ru_ru.json"), encoding="utf-8"))
    cu = {}
    for ф in glob.glob(os.path.join(КОРЕНЬ, "перевод", "*.json")):
        cu.update(json.load(open(ф, encoding="utf-8")))
    out = ["# Термины", "",
           "Как названы вещи игры. Таблица собирается из перевода командой",
           "`python инструменты/термины.py`, поэтому всегда совпадает с ним.", "",
           "## Миры", "",
           "| Церковнославянский | Русский | English |", "|---|---|---|",
           "| Поднебе́снаѧ | Верхний мир | Overworld |",
           "| А҆́дъ | Незер | The Nether |",
           "| Кра́й | Энд | The End |", ""]
    for заглавие, начало in РАЗДЕЛЫ:
        ключи = [k for k in en if k.startswith(начало) and k.count(".") == 2
                 and not k.startswith("block.minecraft.banner") and k in cu]
        ключи.sort(key=lambda k: словарь.остов(cu[k]))
        out += [f"## {заглавие}", "", "| Церковнославянский | Русский | English |", "|---|---|---|"]
        out += [f"| {cu[k]} | {ru.get(k, '')} | {en[k]} |" for k in ключи]
        out.append("")
    open(os.path.join(КОРЕНЬ, "ТЕРМИНЫ.md"), "w", encoding="utf-8").write("\n".join(out))
    print("ТЕРМИНЫ.md готов")


if __name__ == "__main__":
    main()
