"""Справочник подтверждённых церковнославянских форм.

Источники: корпус/hunspell-cu/cu.dic (словарь форм с ударениями)
и корпус/ponomar/.../elis/*.text (Елизаветинская Библия).

Слово сводится к «остову» — русскими буквами, без знаков: ѻ ѡ → о, є ѣ → е,
і ї ѵ → и, ꙋ ѹ → у, ꙗ ѧ → я, ѳ → ф, ѯ → кс, ѱ → пс, ѕ → з, ѿ → от,
конечный ъ отбрасывается. По остову находятся все подтверждённые написания.

Командная строка:
    python словарь.py камень дерево*      — формы по остову (* — по началу)
    python словарь.py --стих велбꙋ́дъ     — стихи Библии, где форма встречается
"""
import glob
import os
import pickle
import re
import sys
import unicodedata
from collections import Counter, defaultdict

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
КОРПУС = os.path.join(КОРЕНЬ, "корпус")
КЭШ = os.path.join(КОРЕНЬ, "сборка", "словарь.pickle")

ЗАМЕНЫ = {
    "ѻ": "о", "ѡ": "о", "ᲂ": "о", "ꙍ": "о", "ѽ": "о",
    "є": "е", "ѣ": "е", "э": "е", "ё": "е",
    "і": "и", "ї": "и", "ѵ": "и", "ѷ": "и",
    "ꙋ": "у", "ѹ": "у",
    "ꙗ": "я", "ѧ": "я",
    "ѳ": "ф", "ѯ": "кс", "ѱ": "пс", "ѕ": "з", "ꙁ": "з", "ѿ": "от",
}
БУКВА = re.compile(r"[^\W\d_]", re.UNICODE)


def знаки_прочь(слово: str) -> str:
    """Убрать все надстрочные знаки, сохранив й."""
    s = unicodedata.normalize("NFD", слово)
    s = s.replace("й", "й").replace("Й", "Й")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def остов(слово: str) -> str:
    s = знаки_прочь(слово).lower().replace("ᲂу", "у").replace("оу", "у")
    s = "".join(ЗАМЕНЫ.get(ch, ch) for ch in s)
    if s.endswith("ъ"):
        s = s[:-1]
    return s


def строчное(слово: str) -> str:
    """Первая буква в строчную; прописное Оу в начале слова — это ᲂу."""
    if слово.startswith("Оу"):
        return "ᲂу" + слово[2:]
    return слово[:1].lower() + слово[1:]


def слова_строки(текст: str):
    """Слова строки вместе с надстрочными знаками (в NFC)."""
    текст = unicodedata.normalize("NFC", текст)
    return re.findall(r"[^\W\d_](?:[^\W\d_]|[̀-ͯ҃-҉ⷠ-ⷿ꙯-ꙿ])*", текст)


def _собрать():
    формы = Counter()
    стихи = defaultdict(list)
    for стр in open(os.path.join(КОРПУС, "hunspell-cu", "cu.dic"), encoding="utf-8").read().split("\n")[1:]:
        стр = стр.split("/")[0].strip()
        if стр:
            формы[unicodedata.normalize("NFC", стр)] += 1
    for путь in sorted(glob.glob(os.path.join(КОРПУС, "ponomar", "Ponomar", "languages", "cu", "bible", "elis", "*.text"))):
        книга = os.path.splitext(os.path.basename(путь))[0]
        глава = "?"
        for стр in open(путь, encoding="utf-8"):
            стр = стр.rstrip("\n")
            if стр.startswith("#"):
                глава = стр[1:].strip()
                continue
            стих, _, текст = стр.partition("|")
            текст = re.sub(r"\*\*\(.*?\)\*\*", "", текст)
            for с in слова_строки(текст):
                ф = строчное(с)
                формы[ф] += 1
                if len(стихи[ф]) < 5:
                    стихи[ф].append(f"{книга} {глава}:{стих.strip()}")
    указатель = defaultdict(Counter)
    for ф, n in формы.items():
        указатель[остов(ф)][ф] += n
    return dict(указатель), dict(стихи), формы


def загрузить():
    if os.path.exists(КЭШ):
        with open(КЭШ, "rb") as f:
            return pickle.load(f)
    данные = _собрать()
    os.makedirs(os.path.dirname(КЭШ), exist_ok=True)
    with open(КЭШ, "wb") as f:
        pickle.dump(данные, f)
    return данные


def найти(запрос: str, указатель):
    if запрос.endswith("*"):
        о = остов(запрос[:-1])
        res = Counter()
        for k, v in указатель.items():
            if k.startswith(о):
                res.update(v)
        return res
    return указатель.get(остов(запрос), Counter())


def main(argv):
    указатель, стихи, формы = загрузить()
    out = []
    if argv and argv[0] == "--стих":
        for w in argv[1:]:
            w = unicodedata.normalize("NFC", w)
            out.append(f"{w}: {', '.join(стихи.get(w, [])) or 'нет в Библии'}")
    else:
        for w in argv:
            res = найти(w, указатель)
            if not res:
                out.append(f"{w}: —")
            else:
                лучшие = ", ".join(f"{ф}({n})" for ф, n in res.most_common(25))
                out.append(f"{w}: {лучшие}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
