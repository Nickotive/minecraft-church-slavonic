"""Сверка слов с корпусом.

    python сверка.py ТАБЛИЦА.md     — проверить предпоследний столбец таблиц Markdown
    python сверка.py --json файл.json — проверить значения JSON

Для каждого слова: подтверждено точно / есть другие написания того же остова
(почти всегда ошибка в букве или ударении) / остова нет в корпусе (новое слово).
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import словарь  # noqa: E402


def сверить(тексты):
    указатель, _, формы = словарь.загрузить()
    точно, иначе, новые = set(), {}, set()
    for т in тексты:
        т = re.sub(r"%(?:\d+\$)?[sdf%]|§.|https?://\S+", " ", т)
        for с in словарь.слова_строки(т):
            с = unicodedata.normalize("NFC", с)
            ф = словарь.строчное(с)
            if ф in формы or с in формы:
                точно.add(ф)
                continue
            варианты = указатель.get(словарь.остов(с))
            if варианты:
                иначе[ф] = [v for v, _ in варианты.most_common(6)]
            else:
                новые.add(ф)
    return точно, иначе, новые


def main(argv):
    if argv[0] == "--json":
        тексты = list(json.load(open(argv[1], encoding="utf-8")).values())
    else:
        тексты = []
        for стр in open(argv[0], encoding="utf-8"):
            ч = [x.strip() for x in стр.split("|")]
            if len(ч) >= 4 and стр.startswith("|"):
                тексты.append(ч[-2])
    точно, иначе, новые = сверить(тексты)
    out = [f"подтверждено: {len(точно)}", f"иное написание в корпусе: {len(иначе)}"]
    out += [f"  {w} → {', '.join(v)}" for w, v in sorted(иначе.items())]
    out += [f"нет в корпусе: {len(новые)}", "  " + " ".join(sorted(новые))]
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
