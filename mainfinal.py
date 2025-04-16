import os
import re
import pandas as pd

# ---------------------------------------------------------------------
# Configuration : dossier de sortie et texte parasite à supprimer
# ---------------------------------------------------------------------
OUTPUT_DIR = os.path.join('data', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Chaîne parasite souvent présente dans les PDF :
UNWANTED_REGEX = r"ESMA - 201-203.*?www\.esma\.europa\.eu \d+"

def clean_pdf_text(raw_text):
    """
    Supprime toutes les occurrences de l'entête/pied de page parasite.
    """
    text = re.sub(UNWANTED_REGEX, "", raw_text)
    return text

# ---------------------------------------------------------------------
# Lecture multi-lignes depuis la console
# ---------------------------------------------------------------------
def read_multiline_input(prompt):
    """
    Demande à l'utilisateur de coller un texte multi-ligne dans la console.
    L'entrée se termine par une ligne contenant exactement 'END'.
    Si l'utilisateur entre "SKIP" (seule ligne), la fonction retourne la chaîne "SKIP".
    """
    print(prompt)
    print("(Terminez l'entrée par une ligne seule contenant'END'. Tapez 'SKIP' pour passer ce tableau.)")
    lines = []
    first_line = input().strip()
    if first_line.upper() == "SKIP":
        return "SKIP"
    else:
        lines.append(first_line)
    while True:
        line = input()
        if line.strip() in ["END"]:
            break
        lines.append(line)
    return "\n".join(lines)

# ---------------------------------------------------------------------
# Parseur pour Tableaux 1 & 2
# ---------------------------------------------------------------------
def parse_table_1_and_2(raw_text):
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

# ---------------------------------------------------------------------
# Parseur Tableau 3
# ---------------------------------------------------------------------
def parse_table_3(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return pd.DataFrame()
    header_tokens = lines[1].split()  
    if len(header_tokens) != 5:
        print("Attention (Table 3) : ligne d'en-tête inattendue.")
        return pd.DataFrame()
    columns = ["Rating"] + header_tokens
    data_lines = lines[2:]
    table_data = []
    for line in data_lines:
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
    df = pd.DataFrame(table_data, columns=columns)
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 4
# ---------------------------------------------------------------------
def parse_table_4(raw_text):
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
    df = pd.DataFrame(data_rows, columns=["Label", "Value"])
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 5
# ---------------------------------------------------------------------
def parse_table_5(raw_text):
    import re
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return pd.DataFrame()
    data_lines = lines[2:]
    table_data = []
    num_pattern = re.compile(r'^-?\d+(?:\.\d+)?(?:E-?\d+)?$')
    for line in data_lines:
        parts = line.rsplit(maxsplit=4)
        if len(parts) < 5:
            continue
        text_part = parts[0]
        num_values = parts[1:]
        if not all(num_pattern.match(val) for val in num_values):
            continue
        tokens = text_part.split()
        if len(tokens) >= 2 and tokens[0] == "Advanced" and tokens[1] == "economies":
            geo = "Advanced economies"
            country = " ".join(tokens[2:])
        else:
            n = len(tokens)
            if n % 2 == 0:
                half = n // 2
                geo = " ".join(tokens[:half])
                country = " ".join(tokens[half:])
            else:
                geo = tokens[0]
                country = " ".join(tokens[1:]) if n > 1 else ""
        row = [geo, country] + num_values
        table_data.append(row)
    columns = ["Geographic Area", "Country", "3M", "6M", "1Y", "2Y"]
    df = pd.DataFrame(table_data, columns=columns)
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 6
# ---------------------------------------------------------------------
def parse_table_6(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return pd.DataFrame()
    columns = ["Rating", "Non-financial", "Financial covered", "Financial", "ABS"]
    data_lines = lines[2:]
    table_data = []
    for line in data_lines:
        tokens = line.split()
        if len(tokens) != 5:
            print(f"Format inattendu dans Table 6 : {line}")
            continue
        row = tokens
        table_data.append(row)
    df = pd.DataFrame(table_data, columns=columns)
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 7
# ---------------------------------------------------------------------
def parse_table_7(raw_text):
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
    df = pd.DataFrame(data_rows, columns=["Label", "Value"])
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 8
# ---------------------------------------------------------------------
def parse_table_8(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return pd.DataFrame()
    header_tokens = lines[2].split()
    columns = ["GeoCountryDesc", "1M", "3M", "6M", "1Y", "2Y"]
    data_lines = lines[3:]
    table_data = []
    for line in data_lines:
        parts = line.rsplit(maxsplit=5)
        if len(parts) < 6:
            continue
        text_part = parts[0]
        nums = parts[1:]
        row = [text_part] + nums
        table_data.append(row)
    df = pd.DataFrame(table_data, columns=columns)
    return df

# ---------------------------------------------------------------------
# Parseur Tableau 9
# ---------------------------------------------------------------------
def parse_table_9(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) < 4:
        return pd.DataFrame()

    data_lines = lines[3:]  # ignorer les titres (3 lignes)
    table_data = []

    i = 0
    while i < len(data_lines):
        line = data_lines[i]

        nums = re.findall(r'\d+', line)
        if len(nums) >= 5:
            num_values = nums[-5:]
            geo_area = re.split(r'\s+Default value', line)[0]
            table_data.append([geo_area.strip()] + num_values)
            i += 1
        else:
            # cas original, chiffres à la ligne suivante
            if (i + 1) < len(data_lines):
                next_line = data_lines[i + 1]
                num_values = re.findall(r'\d+', next_line)
                if len(num_values) == 5:
                    geo_area = re.split(r'\s+Default value', line)[0]
                    table_data.append([geo_area.strip()] + num_values)
                    i += 2
                else:
                    print(f"Ligne ignorée (format inattendu) : {line}")
                    i += 1
            else:
                print(f"Ligne finale ignorée (pas de données numériques) : {line}")
                i += 1

    columns = ["Geographic Area", "1M", "3M", "6M", "1Y", "2Y"]
    df = pd.DataFrame(table_data, columns=columns)
    return df



# ---------------------------------------------------------------------
# Parseur Tableau 10
# ---------------------------------------------------------------------
def parse_table_10(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return pd.DataFrame()

    data_lines = lines[3:]
    fixed_lines = []
    for line in data_lines:
        if fixed_lines and line and line[0].islower():
            fixed_lines[-1] += " " + line
        else:
            fixed_lines.append(line)

    table_data = []
    for line in fixed_lines:
        parts = line.rsplit(maxsplit=2)
        if len(parts) == 3:
            exchange_rate = parts[1]
            shock = parts[2]
            if re.match(r'^-?\d+(\.\d+)?$', shock):  # Vérifie que Shock est numérique
                table_data.append([exchange_rate, shock])
            else:
                print(f"Ligne ignorée (Shock non-numérique) : {line}")
        else:
            print(f"Ligne ignorée (format inattendu) : {line}")

    columns = ["ExchangeRateName", "Shock"]
    df = pd.DataFrame(table_data, columns=columns)
    return df


# ---------------------------------------------------------------------
# Parseur Tableau 11
# ---------------------------------------------------------------------
def parse_table_11(raw_text):
    text = clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 3:
        return pd.DataFrame()

    data_lines = lines[3:]
    fixed_lines = []
    for line in data_lines:
        if fixed_lines and line and line[0].islower():
            fixed_lines[-1] += " " + line
        else:
            fixed_lines.append(line)

    table_data = []
    for line in fixed_lines:
        parts = line.rsplit(maxsplit=2)
        if len(parts) == 3:
            exchange_rate = parts[1]
            shock = parts[2]
            if re.match(r'^-?\d+(\.\d+)?$', shock):  # Vérifie que Shock est numérique
                table_data.append([exchange_rate, shock])
            else:
                print(f"Ligne ignorée (Shock non-numérique) : {line}")
        else:
            print(f"Ligne ignorée (format inattendu) : {line}")

    columns = ["ExchangeRateName", "Shock"]
    df = pd.DataFrame(table_data, columns=columns)
    return df


# ---------------------------------------------------------------------
# Parseur Tableaux 12 & 13
# ---------------------------------------------------------------------
def parse_table_12_and_13(raw_text):
    import pandas as pd
    import re
    
    # Nettoyage initial si nécessaire
    text = raw_text.strip() if hasattr(raw_text, 'strip') else clean_pdf_text(raw_text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    # ----- Extraction du tableau 13 (comme dans le code original) -----
    investor_pattern = re.compile(r'(Professional investor|Retail investor)\s+(\d+)')
    investor_lines = [line for line in lines if "investor" in line.lower()]
    df13_rows = []
    
    for line in investor_lines:
        match = investor_pattern.search(line)
        if match:
            df13_rows.append([match.group(1), match.group(2)])
    
    df13 = pd.DataFrame(df13_rows, columns=['Investor', 'NetOutflows(%)'])
    
    # ----- Extraction des lignes commençant par x et se terminant au premier ) -----
    # Recombiner toutes les lignes en un seul texte pour la recherche
    full_text = ' '.join(lines)
    
    # Trouver toutes les occurrences commençant par x et se terminant au premier )
    pattern = re.compile(r'(x\d+%[^)]*\))')
    matches = pattern.findall(full_text)
    
    # Créer le DataFrame pour le tableau 12
    df12 = pd.DataFrame(matches, columns=['BucketInfo'])
    
    return df12, df13

# ---------------------------------------------------------------------
# Parseur Tableau 14
# ---------------------------------------------------------------------
def parse_table_14(raw_text):
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
    df = pd.DataFrame(data_rows, columns=["Label", "Value"])
    return df

# ---------------------------------------------------------------------
# MAIN : Itérer sur les tableaux et sauvegarder les CSV
# ---------------------------------------------------------------------
def main():
    tables = [
        {"desc": "Tableaux 1 & 2", "func": "parse_table_1_and_2", "count": 2},
        {"desc": "Tableau 3",      "func": "parse_table_3",        "count": 1},
        {"desc": "Tableau 4",      "func": "parse_table_4",        "count": 1},
        {"desc": "Tableau 5",      "func": "parse_table_5",        "count": 1},
        {"desc": "Tableau 6",      "func": "parse_table_6",        "count": 1},
        {"desc": "Tableau 7",      "func": "parse_table_7",        "count": 1},
        {"desc": "Tableau 8",      "func": "parse_table_8",        "count": 1},
        {"desc": "Tableau 9",      "func": "parse_table_9",        "count": 1},
        {"desc": "Tableau 10",     "func": "parse_table_10",       "count": 1},
        {"desc": "Tableau 11",     "func": "parse_table_11",       "count": 1},
        {"desc": "Tableaux 12 & 13", "func": "parse_table_12_and_13", "count": 2},
        {"desc": "Tableau 14",     "func": "parse_table_14",       "count": 1},
    ]
    
    parse_functions = {
        "parse_table_1_and_2": parse_table_1_and_2,
        "parse_table_3": parse_table_3,
        "parse_table_4": parse_table_4,
        "parse_table_5": parse_table_5,
        "parse_table_6": parse_table_6,
        "parse_table_7": parse_table_7,
        "parse_table_8": parse_table_8,
        "parse_table_9": parse_table_9,
        "parse_table_10": parse_table_10,
        "parse_table_11": parse_table_11,
        "parse_table_12_and_13": parse_table_12_and_13,
        "parse_table_14": parse_table_14,
    }
    
    table_num = 1
    for group in tables:
        desc = group["desc"]
        func_key = group["func"]
        count = group["count"]
        raw_text = read_multiline_input(f"\nVeuillez coller le contenu pour {desc} :")
        if raw_text.strip().upper() == "SKIP":
            print(f"=> {desc} SKIPPED")
            table_num += count
            continue
        parser_func = parse_functions[func_key]
        if count == 2:
            dfA, dfB = parser_func(raw_text)
            outA = os.path.join(OUTPUT_DIR, f"table{table_num}.csv")
            outB = os.path.join(OUTPUT_DIR, f"table{table_num+1}.csv")
            dfA.to_csv(outA, index=False, encoding="utf-8")
            dfB.to_csv(outB, index=False, encoding="utf-8")
            print(f"=> Sauvegardés : {outA} et {outB}")
            table_num += 2
        else:
            df = parser_func(raw_text)
            outpath = os.path.join(OUTPUT_DIR, f"table{table_num}.csv")
            df.to_csv(outpath, index=False, encoding="utf-8")
            print(f"=> Sauvegardé : {outpath}")
            table_num += 1

if __name__ == "__main__":
    main()
