"""Сборка ресурспака.

    python сборка.py             — полная сборка: нужны все ключи и чистая проверка
    python сборка.py --черновик  — собрать из того, что переведено (для испытаний)

Выход: сборка/Церковнославѧнскїй ѧзыкъ.zip
"""
import glob
import json
import os
import shutil
import sys
import zipfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import проверка  # noqa: E402
import шрифт  # noqa: E402

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВЫХОД = os.path.join(КОРЕНЬ, "сборка")
ПАК = os.path.join(ВЫХОД, "Церковнославѧнскїй ѧзыкъ.zip")
КОД = "ru_cu"  # сортировка списка языков по коду: ставит язык рядом с русским (rpr < ru_cu < ru_ru)
ИМЯ = "Церковнославѧ́нскїй"
ОБЛАСТЬ = "Рѡссі́йскїй и҆зво́дъ"
ОПИСАНИЕ = "Преложенїе игры и писмена"  # без надстрочных знаков: список пакетов рисуется шрифтом игры
ФОРМАТ = 97


def собрать_перевод(черновик):
    en = json.load(open(os.path.join(КОРЕНЬ, "source", "en_us.json"), encoding="utf-8"))
    cu = {}
    for ф in sorted(glob.glob(os.path.join(КОРЕНЬ, "перевод", "*.json"))):
        for k, v in json.load(open(ф, encoding="utf-8")).items():
            if k in cu and cu[k] != v:
                raise SystemExit(f"ключ {k} переведён дважды по-разному ({os.path.basename(ф)})")
            cu[k] = v
    нет = [k for k in en if k not in cu]
    ошибок = 0
    for k, v in cu.items():
        if k not in en:
            raise SystemExit(f"лишний ключ {k}")
        ош, _ = проверка.проверить_строку(en[k], v)
        ошибок += len(ош)
    if not черновик and (нет or ошибок):
        raise SystemExit(f"сборка остановлена: не переведено {len(нет)}, ошибок проверки {ошибок}")
    print(f"переведено {len(cu)} из {len(en)}; ошибок проверки {ошибок}")
    return {k: cu[k] for k in en if k in cu}


def иконка(набор, путь):
    img = Image.new("RGBA", (64, 64), (236, 224, 196, 255))
    кл = шрифт.нарисовать("Ѿ", ())
    w = max(x for x, _ in кл) + 1
    h0, h1 = min(y for _, y in кл), max(y for _, y in кл)
    s = 5
    ox = (64 - w * s) // 2
    oy = (64 - (h1 - h0 + 1) * s) // 2
    for x, y in кл:
        for dx in range(s):
            for dy in range(s):
                img.putpixel((ox + x * s + dx, oy + (y - h0) * s + dy), (150, 20, 20, 255))
    img.save(путь)


def main(argv):
    черновик = "--черновик" in argv
    cu = собрать_перевод(черновик)
    набор = шрифт.Набор()
    игровой = {k: набор.перевести(v) for k, v in cu.items()}
    имя, область = набор.перевести(ИМЯ), набор.перевести(ОБЛАСТЬ)

    врем = os.path.join(ВЫХОД, "пак")
    shutil.rmtree(врем, ignore_errors=True)
    шрифты = os.path.join(врем, "assets", "minecraft", "font")
    поставщики = набор.записать(os.path.join(врем, "assets", "minecraft", "textures", "font"))
    os.makedirs(шрифты, exist_ok=True)
    ванильные = [
        {"type": "reference", "id": "minecraft:include/space"},
        {"type": "reference", "id": "minecraft:include/default", "filter": {"uniform": False}},
        {"type": "reference", "id": "minecraft:include/unifont"},
    ]
    json.dump({"providers": поставщики + ванильные}, open(os.path.join(шрифты, "default.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"providers": поставщики + [{"type": "reference", "id": "minecraft:include/unifont"}]},
              open(os.path.join(шрифты, "uniform.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    язык = os.path.join(врем, "assets", "minecraft", "lang")
    os.makedirs(язык, exist_ok=True)
    json.dump(игровой, open(os.path.join(язык, f"{КОД}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    мета = {
        "pack": {"description": ОПИСАНИЕ, "min_format": ФОРМАТ, "max_format": ФОРМАТ},
        "language": {КОД: {"name": имя, "region": область, "bidirectional": False}},
    }
    json.dump(мета, open(os.path.join(врем, "pack.mcmeta"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    иконка(набор, os.path.join(врем, "pack.png"))

    if os.path.exists(ПАК):
        os.remove(ПАК)
    with zipfile.ZipFile(ПАК, "w", zipfile.ZIP_DEFLATED) as z:
        for корень, _, файлы in os.walk(врем):
            for f in файлы:
                п = os.path.join(корень, f)
                z.write(п, os.path.relpath(п, врем).replace(os.sep, "/"))
    print(f"гнёзд в шрифте: {len(набор.номер)}; страниц: {len(поставщики)}; пак: {ПАК}")


if __name__ == "__main__":
    main(sys.argv[1:])
