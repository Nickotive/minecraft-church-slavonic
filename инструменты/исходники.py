"""Достать исходные строки игры из установленного Minecraft.

    python исходники.py [версия]      — по умолчанию 26.3

Кладёт en_us.json и ru_ru.json в папку source/. Строки принадлежат Mojang,
поэтому в репозитории их нет.
"""
import json
import os
import sys
import zipfile

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(os.environ.get("APPDATA", ""), ".minecraft")


def main(версия="26.3"):
    папка = os.path.join(MC, "versions", версия)
    описание = json.load(open(os.path.join(папка, версия + ".json"), encoding="utf-8"))
    jar = zipfile.ZipFile(os.path.join(папка, версия + ".jar"))
    индекс = json.load(open(os.path.join(MC, "assets", "indexes", описание["assetIndex"]["id"] + ".json"), encoding="utf-8"))
    os.makedirs(os.path.join(КОРЕНЬ, "source"), exist_ok=True)
    en = json.loads(jar.read("assets/minecraft/lang/en_us.json"))
    h = индекс["objects"]["minecraft/lang/ru_ru.json"]["hash"]
    ru = json.load(open(os.path.join(MC, "assets", "objects", h[:2], h), encoding="utf-8"))
    for имя, данные in (("en_us", en), ("ru_ru", ru)):
        json.dump(данные, open(os.path.join(КОРЕНЬ, "source", имя + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"строк: {len(en)}; файлы в source/")


if __name__ == "__main__":
    main(*sys.argv[1:])
