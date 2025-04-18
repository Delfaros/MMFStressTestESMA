import os
import re
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------
# Configuration : dossier de sortie et texte parasite à supprimer
# ---------------------------------------------------------------------
OUTPUT_DIR = os.path.join('data', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

UNWANTED_REGEX = r"ESMA - 201-203.*?www\.esma\.europa\.eu \d+"

def clean_pdf_text(raw_text):
    return re.sub(UNWANTED_REGEX, "", raw_text)

# ---------------------------------------------------------------------
# Lecture multi-lignes depuis la console
# ---------------------------------------------------------------------
def read_multiline_input(prompt):
    """
    - Collez votre tableau, terminez par 'END'.
    - Tapez 'SKIP' pour passer ce tableau.
    - Tapez 'REUSE' pour réutiliser le dernier CSV existant.
    """
    print(prompt)
    print("(Terminez l'entrée par 'END'. Tapez 'SKIP' pour passer, 'REUSE' pour réutiliser.)")
    first = input().strip()
    if first.upper() in ("SKIP", "REUSE"):
        return first.upper()
    lines = [first]
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

# ---------------------------------------------------------------------
# Réutilisation du CSV le plus récent
# ---------------------------------------------------------------------
def reuse_latest(table_num, prefix):
    pattern = re.compile(r'^(\d{6})table' + str(table_num) + r'\.csv$')
    candidates = []
    for fname in os.listdir(OUTPUT_DIR):
        m = pattern.match(fname)
        if m:
            dt = datetime.strptime(m.group(1), "%m%Y")
            candidates.append((dt, fname))
    if not candidates:
        print(f"⚠️ Aucun CSV existant pour table{table_num} à réutiliser.")
        return None
    latest = max(candidates, key=lambda x: x[0])[1]
    df = pd.read_csv(os.path.join(OUTPUT_DIR, latest), dtype=str)
    new_name = f"{prefix}table{table_num}.csv"
    df.to_csv(os.path.join(OUTPUT_DIR, new_name), index=False, encoding="utf-8")
    print(f"=> Réutilisé {latest} → {new_name}")
    return df

# ---------------------------------------------------------------------
# Parseurs pour les tableaux (1 à 14)
# ---------------------------------------------------------------------
def parse_table_1_and_2(raw_text):
    # ... ton code existant pour parser 1 & 2 ...
    # (inchangé)
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return pd.DataFrame(), pd.DataFrame()
    table1_data = []
    table2_data = []
    for line in lines[2:]:
        tokens = line.split()
        new_tokens = []
        skip = 0
        for i, t in enumerate(tokens):
            if skip:
                skip -= 1
                continue
            if i + 3 < len(tokens) and tokens[i] == "Below" and tokens[i+1] == "BBB" and tokens[i+2] == "or" and tokens[i+3] == "unrated":
                new_tokens.append("Below BBB or unrated")
                skip = 3
            else:
                new_tokens.append(t)
        if len(new_tokens) != 12:
            print(f"Format inattendu dans Tableaux 1&2 : {line}")
            continue
        table1_data.append(new_tokens[:6])
        table2_data.append(new_tokens[6:])
    columns1 = ["Country", "3M", "6M", "1Y", "1.5Y", "2Y"]
    columns2 = ["Rating", "3M", "6M", "1Y", "1.5Y", "2Y"]
    df1 = pd.DataFrame(table1_data, columns=columns1)
    df2 = pd.DataFrame(table2_data, columns=columns2)
    return df1, df2

def parse_table_3(raw_text):
    # ... ton code existant pour parser 3 ...
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return pd.DataFrame()
    header_tokens = lines[1].split()
    if len(header_tokens) != 5:
        print("Attention (Table 3) : ligne d'en-tête inattendue.")
        return pd.DataFrame()
    columns = ["Rating"] + header_tokens
    table_data = []
    for line in lines[2:]:
        tokens = line.split()
        new_tokens = []
        skip = 0
        for i, t in enumerate(tokens):
            if skip:
                skip -= 1
                continue
            if i + 3 < len(tokens) and tokens[i] == "Below" and tokens[i+1] == "BBB" and tokens[i+2] == "or" and tokens[i+3] == "unrated":
                new_tokens.append("Below BBB or unrated")
                skip = 3
            else:
                new_tokens.append(t)
        if len(new_tokens) != 6:
            print(f"Format inattendu dans Table 3: {line}")
            continue
        table_data.append(new_tokens)
    return pd.DataFrame(table_data, columns=columns)

def parse_table_4(raw_text):
    # ... ton code existant pour parser 4 ...
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_rows = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        label = " ".join(tokens[:-1])
        value = tokens[-1]
        data_rows.append([label, value])
    return pd.DataFrame(data_rows, columns=["Label", "Value"])

def parse_table_5(raw_text):
    # ... idem pour 5 ...
    import re
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_lines = lines[2:]
    table_data = []
    num_pattern = re.compile(r'^-?\d+(?:\.\d+)?(?:E-?\d+)?$')
    known_geos = ["Advanced economies","Emerging markets","EA (weighted averages)","EU (weighted averages)"]
    for line in data_lines:
        parts = line.rsplit(maxsplit=4)
        if len(parts) < 5:
            continue
        text_part, *nums = parts
        if not all(num_pattern.match(x) for x in nums):
            continue
        geo = None; country = ""
        for kg in known_geos:
            if text_part.startswith(kg):
                geo = kg
                country = text_part[len(kg):].strip()
                break
        if geo is None:
            toks = text_part.split()
            geo = toks[0]
            country = " ".join(toks[1:])
        if country == "":
            country = geo
        table_data.append([geo, country] + nums)
    cols = ["Geographic Area","Country","3M","6M","1Y","2Y"]
    return pd.DataFrame(table_data, columns=cols)

def parse_table_6(raw_text):
    # ... idem pour 6 ...
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_lines = lines[2:]
    table_data = []
    for line in data_lines:
        tokens = line.split()
        if len(tokens) != 5:
            print(f"Format inattendu dans Table 6 : {line}")
            continue
        table_data.append(tokens)
    cols = ["Rating","Non-financial","Financial covered","Financial","ABS"]
    return pd.DataFrame(table_data, columns=cols)

def parse_table_7(raw_text):
    # ... idem pour 7 ...
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_rows = []
    for i, line in enumerate(lines):
        if i == 0: continue
        tokens = line.split()
        if len(tokens) < 2: continue
        data_rows.append([" ".join(tokens[:-1]), tokens[-1]])
    return pd.DataFrame(data_rows, columns=["Label","Value"])

def parse_table_8(raw_text):
    # ... idem pour 8 ...
    import re
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_lines = lines[3:]
    fixed = []
    for line in data_lines:
        if fixed and line and line[0].islower():
            fixed[-1] += " " + line
        else:
            fixed.append(line)
    known_areas = ["EU","Rest of Europe","North America","Australia and Pacific","South and Central America","Asia","Africa"]
    rows = []
    for line in fixed:
        parts = line.rsplit(maxsplit=5)
        if len(parts) < 6: continue
        text_part, v1, v2, v3, v4, v5 = parts
        for area in known_areas:
            if text_part.startswith(area + " "):
                text_part = text_part[len(area):].strip()
                break
        m = re.search(r"Interest rate swap", text_part)
        country = text_part[:m.start()].strip() if m else text_part
        rows.append([country, v1, v2, v3, v4, v5])
    return pd.DataFrame(rows, columns=["Country","1M","3M","6M","1Y","2Y"])

def parse_table_9(raw_text):
    # ... idem pour 9 ...
    import re
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_lines = lines[3:]
    table_data = []
    i = 0
    while i < len(data_lines):
        line = data_lines[i]
        nums = re.findall(r'\d+', line)
        if len(nums) >= 5:
            geo = re.split(r'\s+Default value', line)[0].strip()
            table_data.append([geo] + nums[-5:])
            i += 1
        else:
            if i+1 < len(data_lines):
                next_nums = re.findall(r'\d+', data_lines[i+1])
                if len(next_nums) == 5:
                    geo = re.split(r'\s+Default value', line)[0].strip()
                    table_data.append([geo] + next_nums)
                    i += 2
                else:
                    i += 1
            else:
                i += 1
    return pd.DataFrame(table_data, columns=["Geographic Area","1M","3M","6M","1Y","2Y"])

def parse_table_10(raw_text):
    # ... idem pour 10 ...
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data_lines = lines[3:]
    fixed = []
    for line in data_lines:
        if fixed and line and line[0].islower():
            fixed[-1] += " " + line
        else:
            fixed.append(line)
    rows = []
    for line in fixed:
        parts = line.rsplit(maxsplit=2)
        if len(parts) == 3 and re.match(r'^-?\d+(\.\d+)?$', parts[2]):
            rows.append([parts[1], parts[2]])
    return pd.DataFrame(rows, columns=["ExchangeRateName","Shock"])

def parse_table_11(raw_text):
    # ... idem pour 11 ...
    return parse_table_10(raw_text)  # même logique que 10

def parse_table_12_and_13(raw_text):
    import re
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Table 13
    inv_pat = re.compile(r'(Professional investor|Retail investor)\s+(\d+)')
    rows13 = [[m.group(1), m.group(2)] for l in lines if (m:=inv_pat.search(l))]
    df13 = pd.DataFrame(rows13, columns=["Investor","NetOutflows(%)"])
    # Table 12
    buckets = []
    for l in lines:
        if "x100%" in l: buckets.append(["Weekly liquid assets (bucket 1)",100])
        if "x85%" in l:  buckets.append(["Weekly liquid assets (bucket 2)",85])
    df12 = pd.DataFrame(buckets, columns=["BucketInfo","Pourcentage"])
    return df12, df13

def parse_table_14(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    rows = []
    for i, line in enumerate(lines):
        if i == 0: continue
        toks = line.split()
        if len(toks) < 2: continue
        rows.append([" ".join(toks[:-1]), toks[-1]])
    return pd.DataFrame(rows, columns=["Label","Value"])

# ---------------------------------------------------------------------
# MAIN : Itérer sur les tableaux et sauvegarder les CSV
# ---------------------------------------------------------------------
def main():
    # 1) Saisie de la date
    while True:
        date_doc = input("Entrez la date du document MMF de l'ESMA (MM/YYYY) : ").strip()
        if re.match(r'^(0[1-9]|1[0-2])\/\d{4}$', date_doc):
            break
        print("Format invalide, réessayez (ex. 02/2025).")
    prefix = date_doc.replace("/", "")

    tables = [
        {"desc": "Tableaux 1 & 2",  "func": "parse_table_1_and_2",  "count": 2},
        {"desc": "Tableau 3",       "func": "parse_table_3",        "count": 1},
        {"desc": "Tableau 4",       "func": "parse_table_4",        "count": 1},
        {"desc": "Tableau 5",       "func": "parse_table_5",        "count": 1},
        {"desc": "Tableau 6",       "func": "parse_table_6",        "count": 1},
        {"desc": "Tableau 7",       "func": "parse_table_7",        "count": 1},
        {"desc": "Tableau 8",       "func": "parse_table_8",        "count": 1},
        {"desc": "Tableau 9",       "func": "parse_table_9",        "count": 1},
        {"desc": "Tableau 10",      "func": "parse_table_10",       "count": 1},
        {"desc": "Tableau 11",      "func": "parse_table_11",       "count": 1},
        {"desc": "Tableaux 12 & 13","func": "parse_table_12_and_13","count": 2},
        {"desc": "Tableau 14",      "func": "parse_table_14",       "count": 1},
    ]

    parse_functions = {g["func"]: globals()[g["func"]] for g in tables}
    table_num = 1

    for group in tables:
        desc, func_key, count = group["desc"], group["func"], group["count"]
        user_input = read_multiline_input(f"\nVeuillez coller le contenu pour {desc} :")

        # SKIP
        if user_input == "SKIP":
            print(f"=> {desc} SKIPPED")
            table_num += count
            continue

        # REUSE
        if user_input == "REUSE":
            for tn in range(table_num, table_num+count):
                reuse_latest(tn, prefix)
            table_num += count
            continue

        # PARSING NORMAL
        parser = parse_functions[func_key]
        result = parser(user_input)

        if count == 2:
            dfA, dfB = result
            fnA = f"{prefix}table{table_num}.csv"
            fnB = f"{prefix}table{table_num+1}.csv"
            dfA.to_csv(os.path.join(OUTPUT_DIR, fnA), index=False, encoding="utf-8")
            dfB.to_csv(os.path.join(OUTPUT_DIR, fnB), index=False, encoding="utf-8")
            print(f"=> Sauvegardés : {fnA} et {fnB}")
        else:
            df = result
            fn = f"{prefix}table{table_num}.csv"
            df.to_csv(os.path.join(OUTPUT_DIR, fn), index=False, encoding="utf-8")
            print(f"=> Sauvegardé : {fn}")

        table_num += count

if __name__ == "__main__":
    main()