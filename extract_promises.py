#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TISZA vallalasok kinyerese a tisza2026.pdf szovegebol (bullet + folyoszoveg)."""
import re
import json
from collections import Counter, defaultdict

SRC = "/sessions/magical-peaceful-franklin/mnt/outputs/tisza.txt"
OUT = "/sessions/magical-peaceful-franklin/mnt/outputs/promises.json"

CHAPTER_TITLES = {
    "1": "Gazdag és sikeres ország",
    "2": "Békés és rendezett ország",
    "3": "Szabad és boldog ország",
    "4": "Tiszta és haladó ország",
}
SUBSECTIONS = {
    "1.1": ("Ganz Ábrahám Gazdaságfejlesztési Program", "Gazdaság és Adó"),
    "1.2": ("Adócsökkentés+", "Gazdaság és Adó"),
    "1.3": ("Stabil költségvetés", "Gazdaság és Adó"),
    "1.4": ("Rezsicsökkentés+", "Energia és Rezsi"),
    "1.5": ("Infrastruktúrafejlesztés", "Közlekedés"),
    "1.6": ("Wekerle Sándor Bérlakásépítési és Otthonfejlesztési Program", "Lakhatás"),
    "2.1": ("Biztonságos Magyarország, erős határok", "Biztonság és Honvédelem"),
    "2.2": ("Rend és közbiztonság", "Biztonság és Honvédelem"),
    "2.3": ("Zéró tolerancia az illegális bevándorlással szemben", "Biztonság és Honvédelem"),
    "2.4": ("Szuverén nemzet", "Külpolitika és Nemzet"),
    "2.5": ("Demográfiai fordulat, összetartó nemzet, hazatérő magyarok", "Külpolitika és Nemzet"),
    "2.6": ("Tisztességes Magyarország", "Korrupció és Jog"),
    "2.7": ("Bibó István Program", "Korrupció és Jog"),
    "2.8": ("Működő állam, erős önkormányzatok", "Államszervezet"),
    "2.9": ("Erős közösségek", "Államszervezet"),
    "3.1": ("Hugonnai Vilma Egészségügyi Program", "Egészségügy"),
    "3.2": ("Nyugdíjemelés+", "Szociális és Család"),
    "3.3": ("Brunszvik Teréz Gyermekvédelmi Program", "Szociális és Család"),
    "3.4": ("100% Család Program", "Szociális és Család"),
    "3.5": ("Okos nemzet, világszínvonalú tudás", "Oktatás"),
    "3.6": ("Akadálymentes Magyarország", "Esélyegyenlőség"),
    "3.7": ("Egyenlő esély a nőknek a munkában és a magánéletben", "Esélyegyenlőség"),
    "3.8": ("Roma esélyegyenlőség", "Esélyegyenlőség"),
    "3.9": ("Hajós Alfréd Program", "Sport és Kultúra"),
    "3.10": ("Szabad kultúra, támogatott művészet", "Sport és Kultúra"),
    "4.1": ("Zöld Magyarország", "Környezet és Energia"),
    "4.2": ("Erős hazai agrár- és élelmiszeripar", "Agrár és Vidék"),
    "4.3": ("Xantus János Állatvédelmi Program", "Agrár és Vidék"),
    "4.4": ("Szent István Vidékfejlesztési Program", "Agrár és Vidék"),
    "4.5": ("Felkészülés a jövőre", "Környezet és Energia"),
}

# Gyakori, jelentés nélküli szavak – a duplikátum-hasonlóság zajának csökkentésére
STOPWORDS = frozenset(
    "a az és hogy nem is be meg el ki fel le re ra ban ben nak nek val vel hoz hez "
    "höz tól től ról ről mint csak már még ezt azt egy minden számára érdekében "
    "valamint illetve ahol amely amelyek ami ezek azok után előtt között szerint".split()
)

subsec_re = re.compile(r'^\s*(\d)\.(\d{1,2})\.\s+\S')
PROBLEM_HEAD_RE = re.compile(r'(?:[–-]\s*)?Probl[ée]m[áa]k\s*$', re.IGNORECASE)
COMMIT_HEAD_RE = re.compile(
    r'(?:[–-]\s*)?(?:V[áa]llal[áa]s(?:aink|ok|unk)?|Megold[áa]s(?:aink|ok)?|Javaslataink)\s*$',
    re.IGNORECASE,
)
PROSE_VERB_RE = re.compile(
    r'\b(Vállaljuk|Bevezetjük|Létrehozzuk|Megduplázzuk|Megdupláz\w*|Eltöröljük|'
    r'Visszaállítjuk|Visszahozzuk|Biztosítjuk|Garantáljuk|Megteremtjük|Csökkentjük|'
    r'Emeljük|Növeljük|Megerősítjük|Megszüntetjük|Megnyitjuk|Helyreállítjuk|Megőrizzük|'
    r'Kiterjesztjük|Megemeljük|Megszervezzük|Újraindítjuk|Megkezdjük|Kidolgozzuk|'
    r'Felülvizsgáljuk|Lehetővé tesszük|Elérhetővé tesszük|Hazahozzuk|Megvédjük|Megújítjuk)\b'
)


def clean(text):
    text = text.replace('�', '')
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_break_line(s):
    return (not s or s.isdigit() or bool(re.match(r'^\d+\s', s))
            or (s.isupper() and len(s) > 12))


def main():
    lines = open(SRC, encoding='utf-8').read().split('\n')
    cur_sub = None
    in_problem = False
    promises = []
    pending = None
    prose_buf = []

    def add_promise(text, src):
        text = clean(text)
        if len(text) < 8:
            return
        title, category = SUBSECTIONS.get(cur_sub, ("", "Egyéb"))
        chap = cur_sub.split('.')[0] if cur_sub else ""
        promises.append({
            "text": text,
            "subsection": cur_sub or "",
            "subsectionTitle": title,
            "chapter": CHAPTER_TITLES.get(chap, ""),
            "category": category,
            "source": src,
        })

    def flush_bullet():
        nonlocal pending
        if pending is None:
            return
        text, pending = pending, None
        add_promise(text, "bullet")

    def flush_prose():
        nonlocal prose_buf
        if not prose_buf:
            return
        txt = clean(' '.join(prose_buf))
        prose_buf = []
        for sent in re.split(r'(?<=[.!?])\s+', txt):
            sent = sent.strip()
            if 25 <= len(sent) <= 320 and PROSE_VERB_RE.search(sent):
                add_promise(sent, "próza")

    for line in lines:
        s = line.strip()

        m = subsec_re.match(line)
        if m and f"{m.group(1)}.{m.group(2)}" in SUBSECTIONS:
            flush_bullet(); flush_prose()
            cur_sub = f"{m.group(1)}.{m.group(2)}"
            in_problem = False
            continue

        is_heading = len(s) <= 60
        if is_heading and PROBLEM_HEAD_RE.search(s):
            flush_bullet(); flush_prose(); in_problem = True
            continue
        if is_heading and (COMMIT_HEAD_RE.search(s) or s == 'Bevezető'):
            flush_bullet(); flush_prose(); in_problem = False
            continue

        if '»' in line:
            flush_bullet(); flush_prose()
            after = line.split('»', 1)[1].strip()
            pending = None if in_problem else after
            continue

        if pending is not None:
            if is_break_line(s):
                flush_bullet()
            else:
                pending += ' ' + s
            continue

        if is_break_line(s):
            flush_prose()
        elif not in_problem:
            prose_buf.append(s)

    flush_bullet(); flush_prose()

    # ============ DUPLIKÁTUMSZŰRÉS ============
    # 0) Az "Egyéb" (alfejezethez nem köthető) összefoglaló vállalások eldobása –
    #    ezek a program eleji kivonatok, amelyek a fejezeti tételeket ismétlik.
    promises = [p for p in promises if p["subsection"]]

    def content_words(t):
        return [w for w in re.sub(r'[^a-záéíóöőúüű0-9 ]', ' ', t.lower()).split()
                if w not in STOPWORDS]

    def tokenset(t):
        return frozenset(content_words(t))

    for p in promises:
        p["_tok"] = tokenset(p["text"])
        p["_head"] = tuple(content_words(p["text"])[:3])

    # 1) Token-hasonlóság: két vállalás duplikátum, ha
    #    - Jaccard >= 0.50 (átfogalmazott, de lényegében azonos), VAGY
    #    - a rövidebb >= 70%-a benne a hosszabban ÉS azonos a nyitó akció (első 3 szó).
    JACCARD_T = 0.50
    CONTAIN_T = 0.70

    def is_dup(a, b):
        sa, sb = a["_tok"], b["_tok"]
        if not sa or not sb:
            return False
        inter = len(sa & sb)
        if not inter:
            return False
        jac = inter / len(sa | sb)
        if jac >= JACCARD_T:
            return True
        cont = inter / min(len(sa), len(sb))
        same_head = a["_head"] == b["_head"] and len(a["_head"]) >= 3
        return cont >= CONTAIN_T and same_head

    # A hosszabb (részletesebb) változat marad meg.
    order = sorted(range(len(promises)), key=lambda i: -len(promises[i]["text"]))
    kept_idx = []
    for i in order:
        if any(is_dup(promises[i], promises[k]) for k in kept_idx):
            continue
        kept_idx.append(i)
    promises = [promises[i] for i in sorted(kept_idx)]

    # 2) Szemantikus klaszterek: ugyanaz az intézkedés több fejezetben, eltérő
    #    megfogalmazással (a tokenek alig fednek át, ezért a fenti lépés nem fogja).
    #    Minden klaszterből a leghosszabb (legrészletesebb) vállalás marad.
    SEMANTIC_CLUSTERS = [
        ("egészségügyi minisztérium",),
        ("20 ezer új férőhely",),
        ("nemzetközi büntetőbíróság",),
        ("vendégmunkások behozatalát",),
        ("nyugdíjas szép-kártyát",),
        ("kekva-modell", "kekva-modellt"),
        ("európai ügyészséghez",),
        ("ügynökakták", "ügynökaktákat"),
        ("szuverenitásvédelmi hivatal",),
        ("svájci indexálás", "bérek alakulását fogják követni", "nyugdíjak újra követni"),
    ]
    drop_ids = set()
    for keys in SEMANTIC_CLUSTERS:
        grp = [p for p in promises if any(k in p["text"].lower() for k in keys)]
        if len(grp) <= 1:
            continue
        grp.sort(key=lambda p: -len(p["text"]))
        for p in grp[1:]:
            drop_ids.add(id(p))
    promises = [p for p in promises if id(p) not in drop_ids]

    uniq = promises
    for p in uniq:
        p.pop("_tok", None)
        p.pop("_head", None)

    for i, p in enumerate(uniq, 1):
        p["id"] = i

    json.dump(uniq, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print("Osszes vallalas:", len(uniq))
    print("  bullet:", sum(1 for p in uniq if p["source"] == "bullet"),
          "| proza:", sum(1 for p in uniq if p["source"] == "próza"))
    for k, v in Counter(p["category"] for p in uniq).most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
