"""Generates yrgo_mystery.sql — a Swedish SQL mystery set at Yrgo, Göteborg (MySQL 8.4)."""
import datetime as dt
import hashlib
import math
import random
import re
import sys

OUT = sys.argv[1]
rng = random.Random(20251114)
D = dt.date
CRIME_DATE = D(2025, 11, 14)

# ---------------------------------------------------------------- name data
MALE = """Erik Lars Karl Anders Johan Per Nils Mikael Jan Hans Lennart Peter Olof Gunnar Sven Fredrik
Bengt Daniel Alexander Gustav Magnus Göran Stefan Marcus Andreas Mattias Oscar Jonas Henrik Viktor David
Emil Simon Anton Filip Johannes Kristoffer Rasmus Oliver William Lucas Hugo Elias Liam Axel Ludvig Adam
Isak Theo Ali Mohammed Ahmed Kevin Robin Sebastian Tobias Joakim Patrik Ulf Leif Kent Rolf Björn Åke
Tommy Thomas Christer Roger Sixten Melvin Albin Edvin Vilgot""".split()
FEMALE = """Anna Eva Maria Karin Kristina Lena Sara Emma Kerstin Ingrid Marie Malin Jenny Annika Hanna Linda
Susanne Elin Johanna Sofia Carina Elisabeth Ida Ulla Monica Julia Linnéa Ebba Alice Maja Elsa Astrid Wilma
Freja Saga Klara Agnes Alva Selma Moa Lisa Matilda Frida Amanda Emelie Therese Camilla Helena Åsa Birgitta
Gunilla Margareta Ingela Petra Jessica Josefin Fatima Leila Yasmin Cecilia Ronja Tove Siri Stina""".split()
LAST = """Andersson Johansson Karlsson Nilsson Eriksson Larsson Olsson Persson Svensson Gustafsson Pettersson
Jonsson Jansson Hansson Bengtsson Jönsson Lindberg Jakobsson Magnusson Lindström Olofsson Lindqvist Lindgren
Berg Axelsson Bergström Lundberg Lundgren Lind Lundqvist Mattsson Berglund Fredriksson Sandberg Henriksson
Forsberg Sjöberg Wallin Ali Engström Mohammed Eklund Danielsson Lundin Håkansson Björk Bergman Gunnarsson
Holm Wikström Samuelsson Isaksson Fransson Bergqvist Nyström Holmberg Arvidsson Löfgren Söderberg Nyberg
Blomqvist Claesson Nordström Mårtensson Lundström Ström Viklund Hassan Abrahamsson Öberg Hedlund Holmgren
Dahlberg Hellström Sundberg Ekström Strand Falk Åberg Nordin Sundqvist Ekberg Hermansson Kaya Yilmaz""".split()

STREETS = """Kungsportsavenyn|Linnégatan|Vasagatan|Hisingsgatan|Lindholmsallén|Forskningsgången|Järntorgsgatan|
Övre Husargatan|Första Långgatan|Andra Långgatan|Tredje Långgatan|Majorsgatan|Karl Johansgatan|Eriksbergsgatan|
Sannegårdsgatan|Vågmästaregatan|Kvillegatan|Hjalmar Brantingsgatan|Wieselgrensgatan|Masthuggstorget|Stigbergsliden|
Allmänna vägen|Kaponjärgatan|Haga Nygata|Sprängkullsgatan|Aschebergsgatan|Föreningsgatan|Södra vägen|
Engelbrektsgatan|Götabergsgatan|Storgatan|Postgatan|Ekelundsgatan|Bergsgatan|Danska vägen|Redbergsvägen|
Kvibergsvägen|Delsjövägen|Mölndalsvägen|Guldhedsgatan|Doktor Allards gata|Gibraltargatan|Olofshöjdsgatan|
Doktor Sydows gata|Frölundagatan|Tynnereds gata|Långedragsvägen|Saltholmsgatan|Slottsskogsgatan|Plantagegatan|
Smaragdgatan|Brämaregatan|Vågbrytaregatan|Säterigatan|Godhemsgatan|Gamlestadsvägen|Friggagatan""".replace("\n", "").split("|")

EYES = ["blå", "blå", "blå", "brun", "brun", "grön", "grå"]
HAIR = ["blond", "blond", "brun", "brun", "brun", "svart", "svart", "röd", "grå", "vit", "skallig"]
CARS = {
    "Volvo": ["XC40", "XC60", "XC90", "V60", "V70", "V90", "S60", "EX30"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "ID.4", "Polo"],
    "Toyota": ["Corolla", "RAV4", "Yaris", "C-HR"],
    "Tesla": ["Model 3", "Model Y"],
    "Kia": ["Niro", "Ceed", "EV6"],
    "BMW": ["3-serie", "5-serie", "X3", "i4"],
    "Audi": ["A4", "A6", "Q5", "e-tron"],
    "Skoda": ["Octavia", "Superb", "Enyaq"],
    "Saab": ["9-3", "9-5", "900"],
    "Polestar": ["2", "3"],
    "Ford": ["Focus", "Kuga", "Mustang Mach-E"],
    "Renault": ["Clio", "Captur", "Zoe"],
    "Mercedes-Benz": ["A-klass", "C-klass", "E-klass"],
    "Hyundai": ["i30", "Kona", "Ioniq 5"],
}
CAR_WEIGHTS = {"Volvo": 6, "Volkswagen": 4, "Toyota": 3, "Tesla": 2, "Kia": 2, "BMW": 2, "Audi": 2,
               "Skoda": 2, "Saab": 1, "Polestar": 1, "Ford": 1, "Renault": 1, "Mercedes-Benz": 2, "Hyundai": 1}
PLATE_LETTERS = "ABCDEFGHJKLMNOPRSTUWXYZ"   # Swedish plates skip I, Q, V, Å, Ä, Ö
PLATE_LAST = "0123456789ABCDEFGHJKLMNPRSTUWXYZ"


def sql(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dt.datetime):
        return f"'{v.isoformat(sep=' ')}'"
    if isinstance(v, (dt.date, dt.time)):
        return f"'{v.isoformat()}'"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def luhn(digits):
    total = 0
    for i, ch in enumerate(digits):
        n = int(ch) * (2 if i % 2 == 0 else 1)
        total += n // 10 + n % 10
    return (10 - total % 10) % 10


used_pnr = set()


def make_pnr(age, male, r=rng):
    while True:
        latest = D(CRIME_DATE.year - age, CRIME_DATE.month, CRIME_DATE.day)
        earliest = D(CRIME_DATE.year - age - 1, CRIME_DATE.month, CRIME_DATE.day) + dt.timedelta(days=1)
        born = earliest + dt.timedelta(days=r.randrange((latest - earliest).days + 1))
        serial = f"{r.randrange(100):02d}{r.choice('13579' if male else '02468')}"
        body = born.strftime("%y%m%d") + serial
        pnr = born.strftime("%Y%m%d") + "-" + serial + str(luhn(body))
        if pnr not in used_pnr:
            used_pnr.add(pnr)
            return pnr


def pnr_born(born, male, r):
    """A valid personal number for a fixed date of birth."""
    while True:
        serial = f"{r.randrange(100):02d}{r.choice('13579' if male else '02468')}"
        pnr = born.strftime("%Y%m%d") + "-" + serial + str(luhn(born.strftime("%y%m%d") + serial))
        if pnr not in used_pnr:
            used_pnr.add(pnr)
            return pnr


def random_plate(r=rng):
    while True:
        p = "".join(r.choice(PLATE_LETTERS) for _ in range(3)) + " " + \
            f"{r.randrange(100):02d}" + r.choice(PLATE_LAST)
        if "H 42" not in p and p not in used_plates:
            used_plates.add(p)
            return p


used_plates = set()
used_person_ids, used_license_ids, used_card_ids = set(), set(), set()

# ------------------------------------------------------------- planted cast
# Each special: person + optional license. Fixed ids keep the walkthrough stable.
SPECIAL = [
    # key, id, name, street, number, license(dict) or None
    dict(key="witness1", id=16371, name="Gustav Öberg", street="Hisingsgatan", number=97,
         lic=dict(id=318771, age=67, height=178, eye="blå", hair="grå", gender="man",
                  plate="NUP 13K", make="Volvo", model="V70")),
    dict(key="witness2", id=41529, name="Elin Sjöberg", street="Lindholmsallén", number=12,
         lic=dict(id=490173, age=27, height=164, eye="grön", hair="brun", gender="kvinna",
                  plate="ELS 28B", make="Polestar", model="2")),
    dict(key="thief", id=67318, name="Jonas Berglund", street="Kvillegatan", number=8,
         lic=dict(id=723514, age=31, height=183, eye="brun", hair="brun", gender="man",
                  plate="KHH 42W", make="Volkswagen", model="Golf")),
    dict(key="decoy_card1", id=28644, name="Viktor Lindqvist", street="Eriksbergsgatan", number=31,
         lic=dict(id=255409, age=24, height=176, eye="blå", hair="blond", gender="man",
                  plate="MKL 58T", make="Toyota", model="Corolla")),
    dict(key="decoy_card2", id=53902, name="Oscar Nyström", street="Sannegårdsgatan", number=5,
         lic=dict(id=611058, age=29, height=185, eye="brun", hair="svart", gender="man",
                  plate="BZT 07N", make="Saab", model="9-3")),
    dict(key="decoy_card3", id=72215, name="Ida Holmgren", street="Vågmästaregatan", number=19,
         lic=None),
    dict(key="decoy_plate1", id=35187, name="Karin Ekberg", street="Masthuggstorget", number=3,
         lic=dict(id=402266, age=45, height=169, eye="grå", hair="blond", gender="kvinna",
                  plate="BHH 421", make="Kia", model="Niro")),
    dict(key="decoy_plate2", id=80946, name="Rasmus Dahlberg", street="Säterigatan", number=44,
         lic=dict(id=870031, age=38, height=181, eye="blå", hair="brun", gender="man",
                  plate="RXH 42C", make="BMW", model="X3")),
    dict(key="mastermind", id=88214, name="Cecilia Wallin", street="Långedragsvägen", number=61,
         lic=dict(id=930472, age=52, height=168, eye="grön", hair="röd", gender="kvinna",
                  plate="GWL 77C", make="Volvo", model="XC90")),
    dict(key="decoy_mm1", id=19730, name="Annika Holm", street="Delsjövägen", number=22,
         lic=dict(id=147385, age=47, height=166, eye="blå", hair="röd", gender="kvinna",
                  plate="TOR 51D", make="Volvo", model="XC90")),
    dict(key="decoy_mm2", id=46058, name="Lena Forsberg", street="Guldhedsgatan", number=9,
         lic=dict(id=558920, age=58, height=170, eye="brun", hair="röd", gender="kvinna",
                  plate="FAL 33M", make="Volvo", model="XC90")),
]
S = {s["key"]: s for s in SPECIAL}
SPECIAL_NAMES = {s["name"] for s in SPECIAL}

persons, licenses = [], []
for s in SPECIAL:
    lic = s["lic"]
    male = (lic["gender"] == "man") if lic else s["name"].split()[0] in MALE
    age = lic["age"] if lic else 26
    s["pnr"] = make_pnr(age, male)
    used_person_ids.add(s["id"])
    if lic:
        used_license_ids.add(lic["id"])
        used_plates.add(lic["plate"])
        licenses.append((lic["id"], lic["age"], lic["height"], lic["eye"], lic["hair"], lic["gender"],
                         lic["plate"], lic["make"], lic["model"]))
    persons.append((s["id"], s["name"], lic["id"] if lic else None, s["number"], s["street"], s["pnr"]))

# ---------------------------------------------------------- filler people
N_PERSONS = 10000


def new_id(used, lo, hi, r=rng):
    while True:
        i = r.randint(lo, hi)
        if i not in used:
            used.add(i)
            return i


def mastermind_like(gender, hair, height, make, model):
    return gender == "kvinna" and hair == "röd" and make == "Volvo" and model == "XC90" and 160 <= height <= 175


makes, weights = zip(*CAR_WEIGHTS.items())
while len(persons) < N_PERSONS:
    male = rng.random() < 0.5
    first = rng.choice(MALE if male else FEMALE)
    name = f"{first} {rng.choice(LAST)}"
    if name in SPECIAL_NAMES:
        continue
    street = rng.choice(STREETS)
    number = rng.randint(1, 90 if street == "Hisingsgatan" else 99)
    if street == "Lindholmsallén" and first == "Elin":
        continue
    pid = new_id(used_person_ids, 10000, 99999)
    age = rng.randint(18, 84)
    pnr = make_pnr(age, male)
    lic_id = None
    if rng.random() < 0.88 and age <= 80:
        gender = "man" if male else "kvinna"
        height = int(rng.gauss(180 if male else 166, 7))
        hair = rng.choice(HAIR if male else [h for h in HAIR if h != "skallig"])
        if age > 65 and rng.random() < 0.5:
            hair = rng.choice(["grå", "vit"])
        make = rng.choices(makes, weights)[0]
        model = rng.choice(CARS[make])
        if mastermind_like(gender, hair, height, make, model):
            model = "XC60"
        lic_id = new_id(used_license_ids, 100000, 999999)
        licenses.append((lic_id, age, height, rng.choice(EYES), hair, gender, random_plate(), make, model))
    persons.append((pid, name, lic_id, number, street, pnr))

person_ids = [p[0] for p in persons]
filler_ids = [p[0] for p in persons if p[1] not in SPECIAL_NAMES]
pnr_by_id = {p[0]: p[5] for p in persons}
name_by_id = {p[0]: p[1] for p in persons}

# ------------------------------------------------------- crime scene reports
CITIES = ["Göteborg"] * 8 + ["Stockholm", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping", "Helsingborg",
          "Jönköping", "Norrköping", "Lund", "Umeå", "Borås", "Trollhättan", "Kungälv", "Mölndal", "Partille",
          "Alingsås", "Kiruna", "Halmstad", "Uddevalla"]
TOWN_STREETS = ["Storgatan", "Kyrkogatan", "Drottninggatan", "Stationsgatan", "Järnvägsgatan", "Torggatan",
                "Skolgatan", "Parkgatan", "Hamngatan", "Södra Vägen"]
ITEMS = ["en cykel", "en bärbar dator", "en plånbok", "en mobiltelefon", "en handväska", "en verktygslåda",
         "en elsparkcykel", "en espressomaskin", "ett par skidor", "en gitarr", "en drönare", "ett kassaskåp",
         "tre kartonger med kanelbullar", "en båtmotor", "en kopparskulptur"]
PLACES = ["ett café", "en butik", "ett kontor", "en lägenhet", "ett förråd", "en restaurang", "en skola",
          "ett gym", "en båtklubb", "ett bibliotek"]
CRIME_TEMPLATES = {
    "stöld": ["{item} stals från {place} på {street}.",
              "Någon stal {item} ur en parkerad bil på {street}. Inga vittnen.",
              "{item} försvann från {place} på {street} under natten. Ägaren misstänker en granne."],
    "inbrott": ["Inbrott i {place} på {street}. Gärningspersonen tog sig in genom ett fönster.",
                "Larmet gick i {place} på {street}, men när polisen kom var det tomt. {item} saknas.",
                "Dörren till {place} på {street} hade brutits upp med kofot."],
    "rån": ["Rån mot {place} på {street}. Gärningspersonen flydde på en moped.",
            "En person blev rånad på {item} vid busshållplatsen på {street}."],
    "skadegörelse": ["Klotter på väggen till {place} på {street}.",
                     "Krossad ruta i {place} på {street}. Ingenting verkar ha stulits.",
                     "Någon har punkterat däcken på fyra bilar på {street}."],
    "bedrägeri": ["En pensionär lurades att lämna ut sina BankID-uppgifter via telefon.",
                  "Falska fakturor skickades till {place} på {street}.",
                  "En person sålde {item} på nätet men skickade aldrig varan."],
    "snatteri": ["{item} snattades från en butik på {street}.",
                 "En person gick ut från en mataffär på {street} utan att betala för en kundvagn full med godis."],
    "olaga intrång": ["En okänd person påträffades i källaren till {place} på {street}.",
                      "Någon har tagit sig in på byggarbetsplatsen på {street} under natten."],
}
CRIME_TYPES = list(CRIME_TEMPLATES)
CRIME_WEIGHTS = [8, 5, 2, 4, 3, 3, 2]

reports = []
start, end = D(2023, 1, 1), D(2025, 12, 31)
for _ in range(1300):
    date = start + dt.timedelta(days=rng.randrange((end - start).days + 1))
    ctype = rng.choices(CRIME_TYPES, CRIME_WEIGHTS)[0]
    city = rng.choice(CITIES)
    if date == CRIME_DATE and ctype == "stöld" and city == "Göteborg":
        continue
    street = rng.choice(STREETS if city == "Göteborg" else TOWN_STREETS)
    text = rng.choice(CRIME_TEMPLATES[ctype]).format(item=rng.choice(ITEMS), place=rng.choice(PLACES), street=street)
    reports.append((date, ctype, text[0].upper() + text[1:], city))

REAL_REPORT = ("Prototypen till examensprojektet ”Projekt Kråka” – en självflygande drönare – stals ur "
               "elektroniklabbet på Yrgo, Forskningsgången 4, natten innan examensmässan. "
               "Säkerhetskameran visar att det fanns två vittnen. Det första vittnet bor i det sista huset "
               "på Hisingsgatan. Det andra vittnet, som heter Elin, bor någonstans på Lindholmsallén.")
reports += [
    (CRIME_DATE, "stöld", REAL_REPORT, "Göteborg"),
    (CRIME_DATE, "stöld", "En elsparkcykel stals utanför centralstationen. Ägaren är mycket upprörd.", "Malmö"),
    (CRIME_DATE, "stöld", "Tre lådor med äpplen stals från en gårdsbutik.", "Borås"),
    (CRIME_DATE, "skadegörelse", "Någon har målat en mustasch på statyn av Poseidon på Götaplatsen.", "Göteborg"),
    (CRIME_DATE, "inbrott", "Inbrott i ett förråd på Lindholmspiren. Inget av värde verkar saknas.", "Göteborg"),
    (D(2025, 11, 13), "stöld", "En laddkabel stals från en laddstolpe på Lindholmsallén.", "Göteborg"),
    (D(2025, 11, 15), "stöld", "En kaffemaskin stals från ett lunchrum på Lindholmen Science Park.", "Göteborg"),
]
rng.shuffle(reports)

# -------------------------------------------------------------- yrgo cards
PROGRAMS = ["Webbutvecklare", "Mjukvaruutvecklare", "Digital designer", "Elektronikingenjör",
            "Inbyggda system", "UX-designer", "Spelutvecklare", "Fastighetsförvaltare",
            "Byggproduktionsledare", "IT-säkerhetstekniker", "Automationstekniker"]
LAB_PROGRAMS = ["Elektronikingenjör", "Inbyggda system", "Automationstekniker"]
CARD_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"


def new_card_id():
    while True:
        c = "".join(rng.choice(CARD_CHARS) for _ in range(5))
        if not c.startswith("48Z") and c not in used_card_ids:
            used_card_ids.add(c)
            return c


cards = []
special_cards = [
    ("48Z55", S["thief"]["id"], "Jonas Berglund", D(2024, 8, 19), "Labb", "Inbyggda system"),
    ("48Z7A", S["decoy_card1"]["id"], "Viktor Lindqvist", D(2025, 8, 18), "Labb", "Elektronikingenjör"),
    ("48ZQP", S["decoy_card2"]["id"], "Oscar Nyström", D(2024, 8, 19), "Labb", "Automationstekniker"),
    ("48ZK3", S["decoy_card3"]["id"], "Ida Holmgren", D(2025, 8, 18), "Student", "Digital designer"),
    ("TQ8RM", S["witness2"]["id"], "Elin Sjöberg", D(2025, 8, 18), "Student", "Webbutvecklare"),
    ("GX4T2", S["mastermind"]["id"], "Cecilia Wallin", D(2025, 10, 20), "Gäst", None),
]
for c in special_cards:
    used_card_ids.add(c[0])
cards += special_cards
SPECIAL_CARD_IDS = {c[0] for c in special_cards}

card_holders = rng.sample(filler_ids, 2600)
for pid in card_holders:
    ctype = rng.choices(["Student", "Labb", "Personal", "Gäst"], [62, 10, 16, 12])[0]
    if ctype in ("Student", "Labb"):
        issued = rng.choice([D(2023, 8, 21), D(2024, 1, 15), D(2024, 8, 19), D(2025, 1, 13), D(2025, 8, 18)])
        program = rng.choice(LAB_PROGRAMS if ctype == "Labb" else PROGRAMS)
    elif ctype == "Personal":
        issued = D(2015, 1, 1) + dt.timedelta(days=rng.randrange(3800))
        program = None
    else:
        issued = D(2025, 1, 1) + dt.timedelta(days=rng.randrange(310))
        program = None
    cards.append((new_card_id(), pid, name_by_id[pid], issued, ctype, program))

# -------------------------------------------------------- yrgo access log
DOORS = ["Huvudentré"] * 6 + ["Elektroniklabb", "Bibliotek", "Verkstad", "Kafé", "Datorsal 3", "Personalingång"]


def t(h, m):
    return dt.time(h, m)


def rand_visit(day_start=7 * 60 + 30, day_end=18 * 60):
    tin = rng.randint(day_start, day_end - 30)
    tout = min(tin + rng.randint(30, 9 * 60), 22 * 60 + 30)
    return dt.time(tin // 60, tin % 60), dt.time(tout // 60, tout % 60)


access = []
filler_cards = [c for c in cards if c[0] not in SPECIAL_CARD_IDS]
day = D(2025, 8, 25)
while day <= D(2025, 11, 28):
    if day.weekday() < 5:
        active = [c for c in filler_cards if c[3] <= day]
        for c in rng.sample(active, rng.randint(90, 140)):
            tin, tout = rand_visit()
            door = "Personalingång" if c[4] == "Personal" and rng.random() < 0.6 else rng.choice(DOORS)
            if door == "Elektroniklabb" and c[4] not in ("Labb", "Personal"):
                door = "Huvudentré"
            access.append((c[0], day, tin, tout, door))
        # evening courses
        for c in rng.sample(active, rng.randint(10, 25)):
            tin, tout = rand_visit(17 * 60, 18 * 60 + 30)
            access.append((c[0], day, tin, max(tout, t(19, 0)), "Huvudentré"))
    day += dt.timedelta(days=1)

access += [
    # Elin's evening course on Monday 10 November — she sees the thief in the entrance.
    ("TQ8RM", D(2025, 11, 3), t(17, 2), t(21, 5), "Huvudentré"),
    ("TQ8RM", D(2025, 11, 10), t(17, 4), t(21, 8), "Huvudentré"),
    ("TQ8RM", D(2025, 11, 17), t(16, 58), t(21, 2), "Huvudentré"),
    ("48Z55", D(2025, 11, 4), t(8, 15), t(16, 30), "Elektroniklabb"),
    ("48Z55", D(2025, 11, 6), t(9, 2), t(15, 47), "Elektroniklabb"),
    ("48Z55", D(2025, 11, 10), t(17, 41), t(19, 36), "Huvudentré"),
    ("48Z55", D(2025, 11, 12), t(8, 30), t(12, 10), "Elektroniklabb"),
    ("48Z7A", D(2025, 11, 10), t(8, 5), t(15, 22), "Elektroniklabb"),
    ("48Z7A", D(2025, 11, 11), t(8, 11), t(16, 3), "Elektroniklabb"),
    ("48ZQP", D(2025, 11, 7), t(9, 30), t(14, 45), "Elektroniklabb"),
    ("48ZQP", D(2025, 11, 12), t(10, 0), t(15, 15), "Verkstad"),
    ("48ZK3", D(2025, 11, 10), t(9, 15), t(16, 0), "Huvudentré"),
    ("48ZK3", D(2025, 11, 13), t(9, 10), t(15, 30), "Datorsal 3"),
    # The mastermind's guest visit two days before the theft.
    ("GX4T2", D(2025, 11, 12), t(10, 5), t(11, 32), "Elektroniklabb"),
]
access.sort(key=lambda r: (r[1], r[2]))

# ---------------------------------------------------------- event check-ins
EVENTS = {
    4711: "Lindholmen Tech Mingel",
    1023: "Göteborgs Kulturkalas",
    2208: "Yrgo Öppet Hus",
    3150: "Hackathon på Lindholmen",
    5402: "Jazzkväll på Järntorget",
    6019: "Vetenskapsfestivalen",
    7333: "After work på Eriksberg",
    8095: "Bokmässan",
    9120: "Hemmamatch på Scandinavium",
    9877: "Löparträff i Slottsskogen",
}
checkins = []
# Tech mingel every other Thursday 2024-01-04 .. 2025-12-18
mingel_dates = []
d = D(2024, 1, 4)
while d <= D(2025, 12, 18):
    mingel_dates.append(d)
    d += dt.timedelta(days=14)
mm_ids = {S[k]["id"] for k in ("mastermind", "decoy_mm1", "decoy_mm2")}
crowd = [i for i in filler_ids]
regulars = rng.sample(crowd, 300)
for d in mingel_dates:
    for pid in set(rng.sample(regulars, rng.randint(18, 30)) + rng.sample(crowd, rng.randint(10, 25))):
        checkins.append((pid, 4711, EVENTS[4711], d))
for eid, ename in EVENTS.items():
    if eid == 4711:
        continue
    for _ in range(rng.randint(8, 20)):
        d = D(2024, 1, 1) + dt.timedelta(days=rng.randrange(730))
        for pid in rng.sample(crowd, rng.randint(40, 120)):
            checkins.append((pid, eid, ename, d))
checkins += [
    (S["mastermind"]["id"], 4711, EVENTS[4711], D(2025, 10, 2)),
    (S["mastermind"]["id"], 4711, EVENTS[4711], D(2025, 10, 16)),
    (S["mastermind"]["id"], 4711, EVENTS[4711], D(2025, 10, 30)),
    (S["mastermind"]["id"], 1023, EVENTS[1023], D(2025, 8, 14)),
    (S["decoy_mm1"]["id"], 4711, EVENTS[4711], D(2025, 10, 16)),
    (S["decoy_mm1"]["id"], 8095, EVENTS[8095], D(2025, 9, 25)),
    (S["decoy_mm2"]["id"], 4711, EVENTS[4711], D(2025, 9, 4)),
    (S["decoy_mm2"]["id"], 4711, EVENTS[4711], D(2025, 9, 18)),
    (S["decoy_mm2"]["id"], 4711, EVENTS[4711], D(2025, 10, 2)),
    (S["decoy_mm2"]["id"], 4711, EVENTS[4711], D(2025, 11, 13)),
    (S["thief"]["id"], 3150, EVENTS[3150], D(2025, 3, 8)),
    (S["witness2"]["id"], 2208, EVENTS[2208], D(2025, 2, 6)),
]
rng.shuffle(checkins)

# ------------------------------------------------------------------ income
incomes = {}
for p in persons:
    if rng.random() < 0.75:
        incomes[p[5]] = int(min(max(rng.lognormvariate(12.9, 0.35), 120000), 1600000)) // 100 * 100
incomes[S["mastermind"]["pnr"]] = 2450000
incomes[S["decoy_mm1"]["pnr"]] = 512300
incomes[S["decoy_mm2"]["pnr"]] = 438900
incomes[S["thief"]["pnr"]] = 246800
incomes.pop(S["decoy_card3"]["pnr"], None)
income_rows = sorted(incomes.items())

# --------------------------------------------------------------- interviews
FILLER_LINES = [
    "Jag såg ingenting.", "Jag var hemma hela kvällen och tittade på Melodifestivalen.",
    "Jag minns faktiskt inte vad jag gjorde den dagen.", "Jag var och fikade på Haga med en kompis.",
    "Det regnade så mycket att jag knappt vågade gå ut.", "Jag åkte spårvagn linje 6 hela vägen till Kortedala.",
    "Jag jobbade sent på kontoret.", "Min granne spelar dragspel varje natt, så jag sov dåligt.",
    "Jag hörde en hund skälla, men det gör den alltid.", "Jag var på Liseberg, fast det var stängt.",
    "Jag tog Älvsnabben över till Lindholmen och tillbaka.", "Jag satt och pluggade SQL hela kvällen.",
    "Jag vet inte varför ni pratar med mig.", "Jag var och handlade på Nordstan.",
    "Jag gick en promenad i Slottsskogen och tittade på sälarna.", "Jag har inget att tillägga.",
    "Jag lagade kroppkakor till middag och somnade sedan i soffan.",
    "Jag kan inte prata nu, jag ska på en innebandymatch.", "Jag såg en måse stjäla en räksmörgås, räknas det?",
    "Jag var på Frölundas match på Scandinavium.", "Jag tror att jag såg en blå bil, men jag är inte säker.",
    "Jag har ett alibi: min katt.", "Jag var ute och seglade i skärgården.",
    "Jag var på gymmet och tränade ben.", "Jag hörde något om en drönare, men det var säkert bara skvaller.",
]
interviews = []
for pid in rng.sample(filler_ids, 4800):
    interviews.append((pid, " ".join(rng.sample(FILLER_LINES, rng.randint(1, 3)))))
interviews += [
    (S["witness1"]["id"], "Jag hörde ett brak från Yrgo och såg en man springa ut med en stor låda under armen. "
     "Han hade ett passerkort i ett orange nyckelband, och sådana har bara de med labbehörighet. "
     "Kortnumret började på \"48Z\". Han hoppade in i en bil vars registreringsnummer innehöll \"H 42\"."),
    (S["witness2"]["id"], "Jag såg när det hände, och jag kände igen tjuven från Yrgo. "
     "Han gick förbi mig i entrén när jag var där på min kvällskurs måndagen den 10 november."),
    (S["thief"]["id"], "Okej, okej, jag erkänner. Jag blev anlitad av en kvinna med gott om pengar. "
     "Jag vet inte vad hon heter, men hon är mellan 165 och 170 cm lång, har rött hår och kör en Volvo XC90. "
     "Jag vet att hon var på \"Lindholmen Tech Mingel\" tre gånger i oktober 2025. "
     "Hon ville ha ritningarna och koden till drönaren, och jag behövde pengarna."),
    (S["decoy_card1"]["id"], "Jag var i labbet hela dagen den 10 november och lödde kretskort. Fråga vem som helst."),
    (S["decoy_mm2"]["id"], "Tech-minglen? Jag går dit ibland för att träffa gamla kollegor. Inget konstigt med det."),
]
rng.shuffle(interviews)

# ------------------------------------------------- part 3: the Chalmers case
# Cecilia Wallin gave the police a false description that led them away from her accomplice. Everything she says
# about the thief is the opposite of the truth. Uses its own RNG so parts 1-2 stay byte-identical.
rng3 = random.Random(20250321)
CHALMERS_DATE = D(2025, 3, 21)
CHALMERS_EVENT = (3301, "Chalmers Innovationsdag")
EVENTS[CHALMERS_EVENT[0]] = CHALMERS_EVENT[1]

# Truth: man, taller than Cecilia (168 cm), not blond, drives a Tesla, checked in at the event that day.
PART3 = [
    dict(key="chalmers_thief", name="Daniel Falk", street="Gibraltargatan", number=54,
         lic=(39, 191, "brun", "svart", "man", "LPN 19R", "Tesla", "Model Y"), visits=[CHALMERS_DATE]),
    dict(key="chalmers_guard", name="Sanna Lindgren", street="Olofshöjdsgatan", number=7,
         lic=(44, 171, "blå", "blond", "kvinna", "SAL 62B", "Toyota", "RAV4"), visits=[]),
    dict(key="chalmers_phd", name="Mattias Hedlund", street="Doktor Allards gata", number=15,
         lic=None, visits=[CHALMERS_DATE]),
    # Tesla-driving visitors that each fail one of the reversed clues.
    dict(key="c_decoy1", name="Johanna Bergman", street="Aschebergsgatan", number=28,
         lic=(35, 172, "grön", "svart", "kvinna", "JBG 64S", "Tesla", "Model 3"), visits=[CHALMERS_DATE]),
    dict(key="c_decoy2", name="Tobias Wikström", street="Engelbrektsgatan", number=41,
         lic=(28, 165, "blå", "brun", "man", "TLU 08K", "Tesla", "Model Y"), visits=[CHALMERS_DATE]),
    dict(key="c_decoy3", name="Erik Hellström", street="Föreningsgatan", number=3,
         lic=(46, 183, "blå", "blond", "man", "ESQ 72H", "Tesla", "Model 3"), visits=[CHALMERS_DATE]),
    dict(key="c_decoy4", name="Malin Ekström", street="Smaragdgatan", number=11,
         lic=(31, 162, "brun", "brun", "kvinna", "MEK 15P", "Tesla", "Model Y"), visits=[CHALMERS_DATE]),
    dict(key="c_decoy5", name="Frida Nordin", street="Mölndalsvägen", number=88,
         lic=(26, 159, "grå", "röd", "kvinna", "FNO 90E", "Tesla", "Model 3"), visits=[CHALMERS_DATE]),
    # Fits every reversed clue, but visited the event the year before.
    dict(key="c_decoy6", name="Andreas Sundberg", street="Guldhedsgatan", number=36,
         lic=(42, 188, "brun", "brun", "man", "AHB 37T", "Tesla", "Model 3"), visits=[D(2024, 3, 22)]),
]
def add_cast(cast, r):
    """Adds new named people (and their licenses/cars) to the data. Fails if a name or plate is taken."""
    existing_names = {p[1] for p in persons}
    for s in cast:
        assert s["name"] not in existing_names, s["name"]
        assert s["lic"] is None or (s["lic"][5] not in used_plates and "H 42" not in s["lic"][5]), s["lic"][5]
        pid = new_id(used_person_ids, 10000, 99999, r)
        lic_id = None
        if s["lic"]:
            age, height, eye, hair, gender, plate, make, model = s["lic"]
            assert not mastermind_like(gender, hair, height, make, model), s["name"]
            lic_id = new_id(used_license_ids, 100000, 999999, r)
            used_plates.add(plate)
            licenses.append((lic_id, *s["lic"]))
        else:
            age, gender = s.get("age", 29), s.get("gender", "man")
        s["id"] = pid
        s["pnr"] = pnr_born(s["born"], gender == "man", r) if "born" in s else make_pnr(age, gender == "man", r)
        persons.append((pid, s["name"], lic_id, s["number"], s["street"], s["pnr"]))
        S[s["key"]] = s


add_cast(PART3, rng3)

# Taking Cecilia at her word must give zero matches, so no blond woman shorter than her may drive a Tesla.
licenses = [(l[0], l[1], l[2], l[3], "brun" if l[4] == "blond" else l[4], *l[5:])
            if l[5] == "kvinna" and l[7] == "Tesla" and l[2] < 168 else l for l in licenses]

tesla_owners = {p[0] for p in persons if p[2] in {l[0] for l in licenses if l[7] == "Tesla"}}
event_crowd = [i for i in filler_ids if i not in tesla_owners]
for d in (D(2024, 3, 22), CHALMERS_DATE):
    for pid in rng3.sample(event_crowd, rng3.randint(110, 150)):
        checkins.insert(rng3.randrange(len(checkins) + 1), (pid, *CHALMERS_EVENT, d))
for s in PART3:
    for d in s["visits"]:
        checkins.insert(rng3.randrange(len(checkins) + 1), (s["id"], *CHALMERS_EVENT, d))
checkins.insert(rng3.randrange(len(checkins) + 1), (S["mastermind"]["id"], *CHALMERS_EVENT, CHALMERS_DATE))

for s in PART3:
    if s["lic"]:
        incomes[s["pnr"]] = rng3.randint(2800, 6500) * 100
incomes[S["chalmers_thief"]["pnr"]] = 318400
income_rows = sorted(incomes.items())

reports.insert(rng3.randrange(len(reports) + 1), (
    CHALMERS_DATE, "stöld",
    "En prototyp till ett nytt solid-state-batteri stals ur batterilabbet på Chalmers, Johanneberg, under "
    "kvällen. Huvudvittnet Cecilia Wallins signalement ledde ingenstans, och utredningen lades ned i brist "
    "på bevis.",
    "Göteborg"))

part3_interviews = [
    (S["mastermind"]["id"], "Ja, jag var på Chalmers den kvällen i mars, på Innovationsdagen. När jag gick mot "
     "parkeringen såg jag tjuven springa ut ur batterilabbet. Jag såg henne tydligt: det var en kvinna, kortare än "
     "jag, med blont hår. Och hon var definitivt inte en av besökarna på Innovationsdagen – hon kom utifrån."),
    (S["chalmers_guard"]["id"], "Jag gick min kvällsrunda på Chalmers när larmet gick i batterilabbet. Jag sprang ut "
     "och såg tjuven hoppa in i en Tesla och köra iväg mot Gibraltargatan. Det var för mörkt för att se "
     "registreringsnumret eller hur personen såg ut."),
    (S["chalmers_phd"]["id"], "Jag jobbade sent i labbet bredvid på Chalmers den 21 mars. Hela byggnaden var låst "
     "för alla utom besökarna på Chalmers Innovationsdag – de hade fått tillfälliga besökskort som gick till "
     "labben. Så tjuven måste ha varit en av besökarna som checkade in den dagen."),
    (rng3.choice(filler_ids), "Jag läste om batteristölden på Chalmers i GP, men jag vet ingenting mer än det."),
    # The thief never says "Chalmers" or Cecilia's name, so a text search can't skip the deduction.
    (S["chalmers_thief"]["id"], "Okej, jag erkänner. Det var jag som tog batteriprototypen ur labbet i Johanneberg. "
     "Men det var inte min idé! Det var hon med det röda håret som kör en Volvo XC90 som planerade allt. "
     "Hon betalade mig 200 000 kronor och lovade att ge polisen en falsk beskrivning så att jag skulle gå fri."),
]
for row in part3_interviews:
    interviews.insert(rng3.randrange(len(interviews) + 1), row)

# --------------------------------------------- part 4: the drone over the river
# A copy of Projekt Kråka hovers over Göta älv. Its Remote ID is half unreadable, so the pilot is found by
# matching the operator register with `_` and the congestion tax camera at Lindholmsmotet.
rng4 = random.Random(20251210)
DRONE_DATE = D(2025, 12, 10)
PILOT_SPOT = (57.70720, 11.93720)   # the car park on Lindholmspiren
RIVER_ID = "SWE-OP-7?3?K2"

PART4 = [
    dict(key="parking_guard", name="Moa Isaksson", street="Eriksbergsgatan", number=17, lic=None,
         age=34, gender="kvinna"),
    # Operators whose ids fit SWE-OP-7_3_K2. Each one fails exactly one camera clue.
    dict(key="drone_club", name="Sixten Mårtensson", street="Kvillegatan", number=40,
         lic=(61, 177, "blå", "grå", "man", "SXM 24F", "Volvo", "V60"), op=("SWE-OP-7A3XK2", D(2023, 4, 2)),
         toll=[("Lindholmsmotet", "in", (13, 52, 18)), ("Lindholmsmotet", "ut", (14, 31, 5))]),
    dict(key="new_operator", name="Tove Lundin", street="Wieselgrensgatan", number=6,
         lic=(29, 163, "grön", "blond", "kvinna", "TLN 81A", "Kia", "Ceed"), op=("SWE-OP-7T3BK2", D(2025, 12, 8)),
         toll=[("Tingstadstunneln", "in", (13, 15, 44)), ("Tingstadstunneln", "ut", (16, 42, 9))]),
    dict(key="late_arrival", name="Melvin Ekström", street="Sannegårdsgatan", number=71,
         lic=(23, 184, "brun", "svart", "man", "MEL 55U", "Toyota", "Yaris"), op=("SWE-OP-7E3PK2", D(2024, 9, 16)),
         toll=[("Lindholmsmotet", "in", (14, 38, 27)), ("Lindholmsmotet", "ut", (17, 5, 51))]),
    # An old, longer id that only fits 7%3%K2: the camera can't rule him out, only `_` can.
    dict(key="old_id", name="Patrik Söderberg", street="Frölundagatan", number=12,
         lic=(48, 182, "grå", "brun", "man", "PSB 63K", "Skoda", "Octavia"), op=("SWE-OP-7W31N0XK2", D(2021, 6, 11)),
         toll=[("Lindholmsmotet", "in", (12, 40, 3)), ("Lindholmsmotet", "ut", (15, 31, 37))]),
]
add_cast(PART4, rng4)
S["c_decoy6"].update(op=("SWE-OP-7R3MK2", D(2025, 5, 14)),
                     toll=[("Lindholmsmotet", "in", (13, 47, 12)), ("Lindholmsmotet", "ut", (15, 8, 40))])
PILOTS = [S[k] for k in ("c_decoy6", "drone_club", "new_operator", "late_arrival", "old_id")]

# The operator register: new ids have 6 characters, ids from before 2023 have 9.
OP_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
fits_river_id = re.compile(r"^SWE-OP-7.*3.*K2$")
operators = [(s["op"][0], s["id"], s["op"][1]) for s in PILOTS]
used_ops = {o[0] for o in operators}
for pid in rng4.sample(filler_ids, 245):
    registered = D(2019, 3, 1) + dt.timedelta(days=rng4.randrange(2470))
    while True:
        oid = "SWE-OP-" + "".join(rng4.choice(OP_CHARS) for _ in range(9 if registered < D(2023, 2, 1) else 6))
        if oid not in used_ops and not fits_river_id.match(oid):
            break
    used_ops.add(oid)
    operators.append((oid, pid, registered))
operators.sort()
new_ops = [o[0] for o in operators if len(o[0]) == 13 and o[0] not in {s["op"][0] for s in PILOTS}]

# Remote ID signals, one every 10 seconds per flight.
SITES = [(57.6850, 11.9430), (57.6890, 12.0300), (57.7500, 11.9800), (57.6700, 11.8530), (57.7200, 11.7700),
         (57.7290, 12.0050), (57.6520, 11.9110), (57.7210, 11.9530), (57.6780, 11.9900), (57.7350, 11.8900)]
MAJORNA, ERIKSBERG = (57.6905, 11.9150), (57.7030, 11.9130)


def damage(oid, positions):
    chars = list(oid)
    for i in positions:
        chars[7 + i] = "?"
    return "".join(chars)


def flight(r, oid, start, minutes, centre, pilot=None, top=60):
    pilot = pilot or (centre[0] + r.uniform(-0.0008, 0.0008), centre[1] + r.uniform(-0.0012, 0.0012))
    lat, lon = centre
    n = minutes * 6 + 1
    rows = []
    for k in range(n):
        lat = min(max(lat + r.uniform(-0.0002, 0.0002), centre[0] - 0.002), centre[0] + 0.002)
        lon = min(max(lon + r.uniform(-0.0003, 0.0003), centre[1] - 0.003), centre[1] + 0.003)
        alt = max(0, min(top + r.randint(-3, 3), 4 * k, 4 * (n - 1 - k)))
        rows.append((start + dt.timedelta(seconds=10 * k), oid, round(lat, 5), round(lon, 5), alt,
                     round(pilot[0] + r.uniform(-0.00003, 0.00003), 5), round(pilot[1] + r.uniform(-0.00003, 0.00003), 5)))
    return rows


signals = []
day = D(2025, 12, 1)
while day <= D(2025, 12, 19):
    for _ in range(0 if day == DRONE_DATE else rng4.choice([0, 1, 1, 2, 2, 3])):
        oid = rng4.choice(operators)[0]
        if rng4.random() < 0.12:
            oid = damage(oid, rng4.sample(range(len(oid) - 7), rng4.randint(1, 2)))
        start = dt.datetime.combine(day, dt.time(rng4.randint(9, 15), rng4.randrange(60), rng4.randrange(60)))
        signals += flight(rng4, oid, start, rng4.randint(5, 30), rng4.choice(SITES), top=rng4.randint(30, 110))
    day += dt.timedelta(days=1)
signals += flight(rng4, rng4.choice(operators)[0], dt.datetime(2025, 12, 10, 10, 12, 40), 22, SITES[1], top=80)
signals += flight(rng4, damage(rng4.choice(new_ops), [0, 3]), dt.datetime(2025, 12, 10, 14, 5, 30), 43, MAJORNA,
                  top=35)
signals += flight(rng4, rng4.choice(operators)[0], dt.datetime(2025, 12, 10, 14, 31, 10), 41, ERIKSBERG, top=50)
# Kråka 2 sweeps back and forth over the river while the pilot stands still in the car park.
for k in range(35 * 6 + 1):
    signals.append((dt.datetime(2025, 12, 10, 14, 20) + dt.timedelta(seconds=10 * k), RIVER_ID,
                    round(57.7050 + 0.0004 * math.cos(k / 25) + rng4.uniform(-0.00005, 0.00005), 5),
                    round(11.9500 - 0.0075 * math.cos(k / 40) + rng4.uniform(-0.00005, 0.00005), 5),
                    max(0, min(45 + rng4.randint(-2, 2), 4 * k, 4 * (210 - k))),
                    round(PILOT_SPOT[0] + rng4.uniform(-0.00003, 0.00003), 5),
                    round(PILOT_SPOT[1] + rng4.uniform(-0.00003, 0.00003), 5)))
signals.sort(key=lambda r: (r[0], r[1]))
assert sum(1 for s in signals if s[1] == RIVER_ID) == 211

# Congestion tax cameras, weekdays 1-12 December. Most plates are in the car register, some are from out of town.
STATIONS = ["Lindholmsmotet", "Hisingsbron", "Tingstadstunneln", "Älvsborgsbron"]
TAX_END = 18 * 3600 + 29 * 60 + 59
pilot_plates = {s["lic"][5] for s in PILOTS}
local_plates = [l[6] for l in licenses if l[6] not in pilot_plates]
visitor_plates = [random_plate(rng4) for _ in range(400)]
tolls = []
day = D(2025, 12, 1)
while day <= D(2025, 12, 12):
    if day.weekday() < 5:
        midnight = dt.datetime.combine(day, dt.time())
        for plate in rng4.sample(local_plates, rng4.randint(450, 550)) + rng4.sample(visitor_plates, rng4.randint(30, 60)):
            st_in = rng4.choices(STATIONS, [3, 3, 3, 2])[0]
            st_out = st_in if rng4.random() < 0.5 else rng4.choice(STATIONS)
            if rng4.random() < 0.7:
                tin, tout = rng4.randint(6 * 3600, 9 * 3600 + 1800), rng4.randint(15 * 3600, TAX_END + 3600)
            else:
                tin = rng4.randint(9 * 3600 + 1800, 16 * 3600)
                tout = tin + rng4.randint(20 * 60, 4 * 3600)
            passes = [(st_in, "in", tin)] + ([(st_out, "ut", tout)] if tout <= TAX_END else [])
            if rng4.random() < 0.08:
                passes = [rng4.choice(passes)]
            tolls += [(plate, st, d, midnight + dt.timedelta(seconds=sec)) for st, d, sec in passes]
    day += dt.timedelta(days=1)
for s in PILOTS:
    tolls += [(s["lic"][5], st, d, dt.datetime(2025, 12, 10, *hms)) for st, d, hms in s["toll"]]
tolls.sort(key=lambda r: (r[3], r[0]))

reports.insert(rng4.randrange(len(reports) + 1), (
    DRONE_DATE, "olovlig drönarflygning",
    "En drönare som ser exakt ut som Yrgos Projekt Kråka flög över Göta älv mellan Lindholmspiren och Stenpiren "
    "kl. 14.20–14.55. Älvsnabben fick stå still i över en halvtimme. Drönarens Remote ID-signal fångades upp, men "
    "operatörs-id:t gick bara att läsa delvis. Enligt signalen stod piloten på parkeringen vid Lindholmspiren "
    f"(latitud {PILOT_SPOT[0]:.4f}, longitud {PILOT_SPOT[1]:.4f}) under hela flygningen. "
    "En parkeringsvakt på Lindholmspiren har hörts av polisen.",
    "Göteborg"))
interviews.insert(rng4.randrange(len(interviews) + 1), (
    S["parking_guard"]["id"],
    "Jag jobbar som parkeringsvakt på Lindholmspiren. Den 10 december kom en bil in på parkeringen strax innan "
    "drönaren lyfte. Föraren tog fram en stor fjärrkontroll och stod sedan vid bilen och tittade ut över älven hela "
    "tiden. När drönaren hade landat lade hen in den i bagageluckan och körde därifrån. Jag hann inte se "
    "registreringsnumret. Men alla bilar till och från Lindholmen måste passera trängselskattekameran vid "
    "Lindholmsmotet."))
for s in PART4:
    if rng4.random() < 0.8:
        incomes[s["pnr"]] = rng4.randint(2600, 5200) * 100

# ------------------------------------------------ part 5: the fake LIA placement
# Twelve students pay for internships at a shell company. Its board is a straw man and a deputy whose personal
# number doesn't exist; the date of birth in that number leads to the straw man's neighbour, Annika Holm.
rng5 = random.Random(20260119)
LIA_DATE = D(2026, 1, 19)
annika = S["decoy_mm1"]
PART5 = [
    dict(key="strawman", name="Åke Blomqvist", street=annika["street"], number=annika["number"], lic=None,
         age=78, gender="man"),
    dict(key="accountant", name="Bengt Claesson", street="Doktor Sydows gata", number=8,
         lic=(74, 176, "blå", "vit", "man", "BCL 12S", "Volvo", "V90")),
    # Born the same day as Annika, but lives somewhere else.
    dict(key="same_birthday", name="Astrid Nyberg", street="Plantagegatan", number=14, born=D(1978, 3, 26),
         lic=(47, 171, "brun", "brun", "kvinna", "ANY 30D", "Hyundai", "Kona")),
    dict(key="neighbour1", name="Selma Fransson", street=annika["street"], number=annika["number"],
         lic=(31, 168, "blå", "blond", "kvinna", "SFR 47M", "Volkswagen", "ID.4")),
    dict(key="neighbour2", name="Edvin Nordström", street=annika["street"], number=annika["number"], lic=None,
         age=19, gender="man"),
]
add_cast(PART5, rng5)
assert annika["pnr"].startswith("19780326")
assert [p[1] for p in persons if p[5][:8] == annika["pnr"][:8]] == ["Annika Holm", "Astrid Nyberg"]
serial = "286"
FAKE_PNR = f"{annika['pnr'][:8]}-{serial}{(luhn(annika['pnr'][2:8] + serial) + 3) % 10}"
assert FAKE_PNR not in used_pnr
stairwell = {p[5] for p in persons if (p[4], p[3]) == (annika["street"], annika["number"])}

used_orgs = set()


def org_number(registered, r):
    while True:
        body = ("556" if registered.year < 2014 else "559") + "".join(str(r.randrange(10)) for _ in range(6))
        org = body[:6] + "-" + body[6:] + str(luhn(body))
        if org not in used_orgs:
            used_orgs.add(org)
            return org


TRADES = ["Bygg", "El", "Måleri", "Redovisning", "Konsult", "Fastigheter", "VVS", "Design", "Data", "Transport",
          "Städ", "Bageri", "Rör", "Mark", "Juridik", "Tandvård", "Frisör", "Event", "Reklam", "Snickeri"]
PREFIXES = ["Älv", "Hisings", "Göta", "Kvarn", "Hamn", "Väst", "Sjö", "Fyr", "Kust", "Skär", "Hav", "Kran", "Varvs",
            "Masthuggs", "Lindholms", "Eriksbergs"]
SUFFIXES = ["teknik", "data", "konsult", "invest", "logistik", "media", "gruppen", "systems", "partner", "design",
            "service", "labs"]
OFFICE_STREETS = ["Lindholmsallén", "Theres Svenssons gata", "Hörselgången", "Gullbergs Strandgata", "Lilla Bommen"]
companies, roles = [], []
company_names = set()
board_pool = [i for i in filler_ids if int(pnr_by_id[i][:4]) <= 2000 and pnr_by_id[i] not in stairwell]
role_count = {}


def board_member(r):
    while True:
        pid = r.choice(board_pool)
        if role_count.get(pid, 0) < 3:
            role_count[pid] = role_count.get(pid, 0) + 1
            return pnr_by_id[pid]


while len(companies) < 390:
    if rng5.random() < 0.5:
        name = f"{rng5.choice(LAST)}s {rng5.choice(TRADES)} AB"
    else:
        name = f"{rng5.choice(PREFIXES)}{rng5.choice(SUFFIXES)} AB"
    if name in company_names:
        continue
    company_names.add(name)
    registered = D(1985, 1, 1) + dt.timedelta(days=rng5.randrange(14915))
    if rng5.random() < 0.25:
        street, number = rng5.choice(OFFICE_STREETS), rng5.randint(1, 40)
    else:
        street, number = rng5.choice(STREETS), rng5.randint(1, 99)
    org = org_number(registered, rng5)
    companies.append((org, name, registered, street, number))
    if rng5.random() < 0.55:
        roles += [(org, board_member(rng5), "Styrelseledamot"), (org, board_member(rng5), "Suppleant")]
    else:
        roles += [(org, board_member(rng5), "Ordförande")]
        roles += [(org, board_member(rng5), "Styrelseledamot") for _ in range(rng5.randint(1, 3))]
        if rng5.random() < 0.3:
            roles.append((org, board_member(rng5), "Suppleant"))
    if rng5.random() < 0.25:
        roles.append((org, board_member(rng5), "VD"))
real_companies = [c for c in companies if c[2] < D(2025, 6, 1)]

# The retired accountant: six family companies over thirty years, all at different addresses.
for name, registered, street, number in [
        ("Claessons Redovisning AB", D(1991, 4, 15), "Doktor Sydows gata", 8),
        ("Claesson Fastigheter AB", D(1996, 9, 2), "Guldhedsgatan", 51),
        ("Claesson & Döttrar Bygg AB", D(2003, 3, 20), "Mölndalsvägen", 17),
        ("Bengts Båtar AB", D(2008, 5, 6), "Saltholmsgatan", 33),
        ("Familjen Claesson Invest AB", D(2014, 11, 24), "Södra vägen", 62),
        ("Claesson Skog AB", D(2019, 2, 11), "Danska vägen", 4)]:
    org = org_number(registered, rng5)
    companies.append((org, name, registered, street, number))
    roles += [(org, S["accountant"]["pnr"], "Ordförande"), (org, board_member(rng5), "Suppleant")]

# Seven shell companies registered in December 2025 at an office hotel on Lindholmspiren.
SHELLS = ["Kråkvind Innovation AB", "Lindholmen Talang AB", "Älvdrönare Konsult AB", "Nordisk Praktikplats AB",
          "Vingslag Teknik AB", "Hamnkranen Invest AB", "Fyrljus Rekrytering AB"]
shell_orgs = {}
for name, d in zip(SHELLS, sorted(rng5.sample(range(1, 21), len(SHELLS)))):
    registered = D(2025, 12, d)
    org = org_number(registered, rng5)
    shell_orgs[name] = (org, registered)
    companies.append((org, name, registered, "Lindholmspiren", 9))
    roles += [(org, S["strawman"]["pnr"], "Styrelseledamot"), (org, FAKE_PNR, "Suppleant")]
# Cecilia's own company. Nobody else sits on its board, so it is no shortcut to Annika.
org = org_number(D(2024, 2, 12), rng5)
companies.append((org, "Nordvind Drönarteknik AB", D(2024, 2, 12), "Lindholmspiren", 5))
roles += [(org, S["mastermind"]["pnr"], "Styrelseledamot"), (org, S["mastermind"]["pnr"], "VD")]
assert len({c[1] for c in companies}) == len(companies)
assert [c[1] for c in companies if "Kråk" in c[1] or "Nordvind" in c[1]] == [SHELLS[0], "Nordvind Drönarteknik AB"]
rng5.shuffle(roles)
companies.sort()

# LIA offers. Real ones are free; the twelve from Kråkvind cost 1 500 kr each.
lia_cards = [c for c in cards if c[0] not in SPECIAL_CARD_IDS and c[4] in ("Student", "Labb")]
victims = rng5.sample([c for c in lia_cards if c[3] == D(2024, 8, 19) and c[5] in ("Inbyggda system", "Elektronikingenjör")], 12)
shell_org, shell_registered = shell_orgs[SHELLS[0]]
offers = [(c[0], shell_org, shell_registered + dt.timedelta(days=rng5.randint(2, 15)), 1500) for c in victims]
for c in rng5.sample([c for c in lia_cards if c[3] in (D(2024, 8, 19), D(2025, 1, 13))], 140):
    offers.append((c[0], rng5.choice(real_companies)[0], D(2025, 9, 15) + dt.timedelta(days=rng5.randrange(124)), 0))
offers.sort(key=lambda o: (o[2], o[0]))

for _ in range(35):
    date = D(2026, 1, 1) + dt.timedelta(days=rng5.randrange(31))
    ctype = rng5.choices(CRIME_TYPES, CRIME_WEIGHTS)[0]
    city = rng5.choice(CITIES)
    if (date, ctype, city) == (LIA_DATE, "bedrägeri", "Göteborg"):
        continue
    street = rng5.choice(STREETS if city == "Göteborg" else TOWN_STREETS)
    text = rng5.choice(CRIME_TEMPLATES[ctype]).format(item=rng5.choice(ITEMS), place=rng5.choice(PLACES), street=street)
    reports.insert(rng5.randrange(len(reports) + 1), (date, ctype, text[0].upper() + text[1:], city))
reports.insert(rng5.randrange(len(reports) + 1), (
    LIA_DATE, "bedrägeri",
    "Tolv studenter från Yrgo anmäler Kråkvind Innovation AB, Lindholmspiren 9. De erbjöds betald LIA men fick "
    "först skriva på ett sekretessavtal, ladda upp källkoden till sina examensprojekt för ”teknisk granskning” och "
    "betala 1 500 kronor för ”säkerhetsprövning”. På första LIA-dagen fanns bara ett tomt skrivbord i ett "
    "kontorshotell. Ingen svarar i telefon.",
    "Göteborg"))
interviews.insert(rng5.randrange(len(interviews) + 1), (
    S["strawman"]["id"],
    "Jag fick 5 000 kronor för att skriva under några papper. Det var en trevlig dam i min trappuppgång som "
    "ordnade allt. Hon sa att det bara var en formalitet."))
for s in PART5:
    if rng5.random() < 0.8:
        incomes[s["pnr"]] = rng5.randint(2600, 5200) * 100
incomes[S["strawman"]["pnr"]] = 142000
incomes[S["accountant"]["pnr"]] = 365000
incomes.pop(S["neighbour2"]["pnr"], None)
income_rows = sorted(incomes.items())

# ---------------------------------------------------------------- solution
def h(name):
    return hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()


MSG_THIEF = ("Grattis, du hittade tjuven! Men vänta, det finns mer... Om du vill ha en riktig utmaning "
             "kan du försöka ta reda på vem som egentligen låg bakom stölden. Läs förhöret med tjuven. "
             "Vill du göra det ännu svårare? Försök klara det med högst två SQL-frågor. "
             "Använd samma INSERT-sats för att kontrollera ditt svar.")
MSG_MASTER = ("Grattis, du hittade hjärnan bakom stölden! Projekt Kråka är tillbaka på Yrgo i tid till "
              "examensmässan. Men vänta... Cecilia Wallins namn förekommer i en annan polisutredning, där hennes "
              "vittnesmål skickade polisen åt fel håll. Nu när vi vet att hon inte går att lita på kanske det "
              "fallet går att lösa. Sök efter henne i brottsplatsrapporterna!")
MSG_CHALMERS = ("Grattis, du löste även Chalmersfallet! Cecilia Wallins vittnesmål var lögn från början till slut, "
                "och nu kan både hon och hennes medhjälpare ställas inför rätta. Batteriprototypen är tillbaka "
                "på Chalmers. Men lugnet varar inte länge. Den 10 december står Älvsnabben plötsligt still mitt "
                "på Göta älv, och över vattnet svävar en drönare som ser exakt ut som Projekt Kråka. "
                "Läs brottsplatsrapporterna från den dagen!")
MSG_PILOT = ("Rätt! Andreas Sundberg – mannen som stämde in på allt i Chalmersfallet utom årtalet – är testpilot på "
             "Nordvind Drönarteknik AB, Cecilia Wallins bolag. ”Ritningarna kom från chefen. Hon sa att de var våra "
             "egna.” Projekt Kråka var borta en hel natt innan polisen hittade den. Det räckte för att kopiera allt. "
             "Cecilia sitter nu häktad, men någon fortsätter att sköta hennes affärer. Den 19 januari 2026 anmäler "
             "tolv studenter från Yrgo ett företag för bedrägeri. Läs brottsplatsrapporterna från den dagen!")
MSG_STRAWMAN = ("Rätt spår! Åke Blomqvist är bara en målvakt som har lånat ut sitt namn. Vem ligger bakom? "
                "Läs hans förhör.")
MSG_FINAL = ("Rätt! Annika Holm drev bluffbolagen åt Nordvind medan Cecilia satt häktad. Studenternas källkod skulle "
             "bli nästa version av Kråka 2. Studenterna får tillbaka sina avgifter, och Yrgo granskar numera alla "
             "LIA-företag extra noga. Hela nätverket kring Cecilia Wallin är avslöjat. "
             "Nu är det verkligen dags för en välförtjänt fika!")
MSG_WRONG = "Det var tyvärr inte rätt person. Försök igen!"

# ------------------------------------------------------------------ output
HEADER = """-- =====================================================================
--  SQL-MYSTERIET PÅ YRGO
--  Ett detektivspel i SQL, inspirerat av "The SQL Murder Mystery"
--  (https://github.com/NUKnightLab/sql-mysteries).
--  För MySQL 8.4.
-- =====================================================================
--
--  UPPDRAGET
--  ---------
--  Ett brott har begåtts i Göteborg och polisen behöver din hjälp.
--  Kommissarien gav dig brottsplatsrapporten, men du har lyckats tappa
--  bort den. Du minns bara vagt att brottet var en stöld ("stöld") som
--  skedde den 14 november 2025, och att den ägde rum i Göteborg.
--
--  Allt du behöver finns i den här databasen. Börja med att hämta
--  rätt brottsplatsrapport från tabellen crime_scene_report och följ
--  sedan ledtrådarna.
--
--  TIPS
--  ----
--    SHOW TABLES;                 -- vilka tabeller finns?
--    DESCRIBE crime_scene_report; -- vilka kolumner har en tabell?
--
--  KONTROLLERA DITT SVAR
--  ---------------------
--  När du tror att du har hittat tjuven, kör:
--
--    INSERT INTO solution VALUES (1, 'Förnamn Efternamn');
--    SELECT value FROM solution;
--
--  INSTALLATION
--  ------------
--    mysql -u root -p < yrgo_mystery.sql
--  eller öppna filen i MySQL Workbench och kör hela skriptet.
--
--  Alla personer och händelser är påhittade.
-- =====================================================================

SET NAMES utf8mb4;

DROP DATABASE IF EXISTS yrgo_mystery;
CREATE DATABASE yrgo_mystery CHARACTER SET utf8mb4 COLLATE utf8mb4_sv_0900_ai_ci;
USE yrgo_mystery;

CREATE TABLE drivers_license (
    id           INT PRIMARY KEY,
    age          INT NOT NULL,
    height       INT NOT NULL,
    eye_color    VARCHAR(20) NOT NULL,
    hair_color   VARCHAR(20) NOT NULL,
    gender       VARCHAR(20) NOT NULL
);

CREATE TABLE car (
    plate_number VARCHAR(10) PRIMARY KEY,
    owner_id     INT NOT NULL,
    make         VARCHAR(30) NOT NULL,
    model        VARCHAR(30) NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES drivers_license (id)
);

CREATE TABLE person (
    id                  INT PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    license_id          INT NULL,
    address_number      INT NOT NULL,
    address_street_name VARCHAR(100) NOT NULL,
    personal_number     CHAR(13) NOT NULL UNIQUE,
    FOREIGN KEY (license_id) REFERENCES drivers_license (id)
);

CREATE TABLE crime_scene_report (
    date        DATE NOT NULL,
    type        VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    city        VARCHAR(50) NOT NULL
);

CREATE TABLE interview (
    person_id  INT NOT NULL,
    transcript TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES person (id)
);

CREATE TABLE yrgo_card (
    id          CHAR(5) PRIMARY KEY,
    person_id   INT NOT NULL,
    name        VARCHAR(100) NOT NULL,
    issued_date DATE NOT NULL,
    card_type   VARCHAR(20) NOT NULL,
    program     VARCHAR(50) NULL,
    FOREIGN KEY (person_id) REFERENCES person (id)
);

CREATE TABLE yrgo_access_log (
    card_id     CHAR(5) NOT NULL,
    access_date DATE NOT NULL,
    time_in     TIME NOT NULL,
    time_out    TIME NOT NULL,
    door        VARCHAR(30) NOT NULL,
    FOREIGN KEY (card_id) REFERENCES yrgo_card (id)
);

CREATE TABLE event_checkin (
    person_id  INT NOT NULL,
    event_id   INT NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    date       DATE NOT NULL,
    FOREIGN KEY (person_id) REFERENCES person (id)
);

CREATE TABLE income (
    personal_number CHAR(13) PRIMARY KEY,
    annual_income   INT NOT NULL
);

CREATE TABLE drone_operator (
    operator_id     VARCHAR(20) PRIMARY KEY,
    person_id       INT NOT NULL,
    registered_date DATE NOT NULL,
    FOREIGN KEY (person_id) REFERENCES person (id)
);

CREATE TABLE remote_id_signal (
    received_at DATETIME NOT NULL,
    operator_id VARCHAR(20) NOT NULL,
    drone_lat   DECIMAL(8, 5) NOT NULL,
    drone_lon   DECIMAL(8, 5) NOT NULL,
    altitude_m  INT NOT NULL,
    pilot_lat   DECIMAL(8, 5) NOT NULL,
    pilot_lon   DECIMAL(8, 5) NOT NULL
);

CREATE TABLE toll_passage (
    plate_number VARCHAR(10) NOT NULL,
    station      VARCHAR(30) NOT NULL,
    direction    VARCHAR(3) NOT NULL,
    passed_at    DATETIME NOT NULL
);

CREATE TABLE company (
    org_number          CHAR(11) PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    registered_date     DATE NOT NULL,
    address_street_name VARCHAR(100) NOT NULL,
    address_number      INT NOT NULL
);

CREATE TABLE company_role (
    org_number      CHAR(11) NOT NULL,
    personal_number CHAR(13) NOT NULL,
    role            VARCHAR(30) NOT NULL,
    FOREIGN KEY (org_number) REFERENCES company (org_number)
);

CREATE TABLE lia_offer (
    card_id      CHAR(5) NOT NULL,
    org_number   CHAR(11) NOT NULL,
    offered_date DATE NOT NULL,
    fee_paid     INT NOT NULL,
    FOREIGN KEY (card_id) REFERENCES yrgo_card (id),
    FOREIGN KEY (org_number) REFERENCES company (org_number)
);

CREATE TABLE solution (
    user  INT,
    value TEXT
);
"""


def write_inserts(f, table, rows, batch=500):
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        f.write(f"INSERT INTO {table} VALUES\n")
        f.write(",\n".join("(" + ", ".join(sql(v) for v in r) + ")" for r in chunk))
        f.write(";\n")
    f.write("\n")


# The car registry is separate from the license registry; each license holder owns one car.
cars = sorted((l[6], l[0], l[7], l[8]) for l in licenses)
licenses = sorted(l[:6] for l in licenses)
persons.sort()
cards.sort()


# Annika Holm and Andreas Sundberg are also decoys in parts 2 and 3, so their answers only count once the
# case before has been solved. Until then they get the usual "wrong" message.
def after(msg, answer):
    return f"IF(EXISTS (SELECT 1 FROM solution WHERE value = {sql(msg)}), {sql(answer)}, {sql(MSG_WRONG)})"


TRIGGER = f"""CREATE TRIGGER check_solution BEFORE INSERT ON solution FOR EACH ROW
SET NEW.value = CASE SHA2(LOWER(TRIM(NEW.value)), 256)
    WHEN {sql(h("Jonas Berglund"))} THEN {sql(MSG_THIEF)}
    WHEN {sql(h("Cecilia Wallin"))} THEN {sql(MSG_MASTER)}
    WHEN {sql(h("Daniel Falk"))} THEN {sql(MSG_CHALMERS)}
    WHEN {sql(h("Andreas Sundberg"))} THEN {after(MSG_CHALMERS, MSG_PILOT)}
    WHEN {sql(h("Åke Blomqvist"))} THEN {after(MSG_PILOT, MSG_STRAWMAN)}
    WHEN {sql(h("Annika Holm"))} THEN {after(MSG_PILOT, MSG_FINAL)}
    ELSE {sql(MSG_WRONG)}
END;

"""
# The trigger is hidden between two batches in the middle of the file, so the answer messages aren't the first
# or last thing you see when opening the script in an editor.
TRIGGER_AFTER_ROW = 5000

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(HEADER + "\n")
    write_inserts(f, "drivers_license", licenses)
    write_inserts(f, "car", cars)
    write_inserts(f, "person", persons)
    write_inserts(f, "crime_scene_report", reports)
    write_inserts(f, "interview", interviews)
    write_inserts(f, "yrgo_card", cards)
    write_inserts(f, "yrgo_access_log", access[:TRIGGER_AFTER_ROW])
    f.write(TRIGGER)
    write_inserts(f, "yrgo_access_log", access[TRIGGER_AFTER_ROW:])
    write_inserts(f, "event_checkin", checkins)
    write_inserts(f, "income", income_rows)
    write_inserts(f, "drone_operator", operators)
    write_inserts(f, "remote_id_signal", signals)
    write_inserts(f, "toll_passage", tolls)
    write_inserts(f, "company", companies)
    write_inserts(f, "company_role", roles)
    write_inserts(f, "lia_offer", offers)

print("persons", len(persons), "licenses", len(licenses), "cars", len(cars), "reports", len(reports), "interviews", len(interviews),
      "cards", len(cards), "access", len(access), "checkins", len(checkins), "income", len(income_rows),
      "operators", len(operators), "signals", len(signals), "tolls", len(tolls), "companies", len(companies),
      "roles", len(roles), "offers", len(offers))
