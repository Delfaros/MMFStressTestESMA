import os
import pandas as pd
import re

def intotxt(csv_dir):
    # 1) Demande de la date au format MM/YYYY
    date_input = input("Entrez la date du document (MM/YYYY) : ").strip()
    if not re.match(r'^(0[1-9]|1[0-2])/[0-9]{4}$', date_input):
        raise ValueError("Format invalide, utilisez MM/YYYY")
    # prefix = MMYYYY pour les noms de fichiers
    prefix = date_input.replace("/", "")
    # yyyymm = YYYYMM pour la valeur SQL
    yyyymm = date_input[3:] + date_input[:2]

    # 2) Charger les CSV nommés MMYYYYtable{i}.csv
    tables = {}
    for i in range(1, 15):
        fn = f"{prefix}table{i}.csv"
        path = os.path.join(csv_dir, fn)
        if os.path.exists(path):
            tables[i] = pd.read_csv(path, dtype=str).fillna("")
        else:
            print(f"Avertissement : fichier manquant {fn} (table {i} ignorée)")

    # 3) Métadonnées et mapping de SELECT
    tables_meta = {
        1:  {"select_num": 1,  "desc": "Liquidity discount factor - Sovereign bonds by residual maturity - Reference countries (in %)", "key": "Country",         "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        2:  {"select_num": 2,  "desc": "Liquidity discount factor - Sovereign bonds by rating and residual maturity (in %)",   "key": "Rating",          "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        3:  {"select_num": 3,  "desc": "Liquidity discount factor - Corporate bonds by rating and residual maturity (in %)",   "key": "Rating",          "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        4:  {"select_num": 4,  "desc": "Price impact parameter (in %)",                                                       "key": "Label",           "val": "Value"},
        5:  {"select_num": 5,  "desc": "Credit Spread by residual maturity - Government bonds (basis points)",              "key": "Country",         "mats": ["3M","6M","1Y","2Y"]},
        6:  {"select_num": 6,  "desc": "Corporate credit spreads (basis points)",                                         "key": "Rating",          "cats": ["Non-financial","Financial covered","Financial","ABS"]},
        7:  {"select_num": 7,  "desc": "Loss given default",                                                                  "key": "Label",           "val": "Value"},
        8:  {"select_num": 8,  "desc": "Interest rate yield shocks absolute changes (basis points)",                     "key": "Country",         "mats": ["1M","3M","6M","1Y","2Y"]},
        9:  {"select_num": 8,  "desc": "Interest rate yield shocks absolute changes (basis points)",                     "key": "Geographic Area", "mats": ["1M","3M","6M","1Y","2Y"]},
       10:  {"select_num": 9,  "desc": "FX shocks (appreciation of the EUR against the USD) relative changes (%)",           "key": "ExchangeRateName","val": "Shock"},
       11:  {"select_num": 10, "desc": "FX shocks (depreciation of the EUR against the USD) relative changes (%)",           "key": "ExchangeRateName","val": "Shock"},
       12:  {"select_num": 12, "desc": "Bucket factor",                                                                      "key": "BucketInfo",      "val": "Pourcentage"},
       13:  {"select_num": 11, "desc": "Net outflows (level of redemption)",                                                   "key": "Investor",        "val": "NetOutflows(%)"},
       14:  {"select_num": 14, "desc": "Net outflows (macro systematic shocks)",                                               "key": "Label",           "val": "Value"},
    }

    # 4) Construction des lignes SQL en commentaires
    lines = []
    lines.append("--ELSE IF @DateEtalonnage >= '01/01/2025' and @DateEtalonnage <= '31/12/2025'\n")
    lines.append("--INSERT INTO [MarketDate].[dbo].[ST_MMF_Parameters]\n")
    lines.append("--SELECT\n")
    lines.append("--  0 as 'Table_ID'\n")
    lines.append("--  'Etalonnages' as 'Table_Description'\n")
    lines.append("--  'YYYY/MM étalonnages' as 'Line_Description'\n")
    lines.append("--  'YYYY/MM étalonnages' as 'Column_Description'\n")
    lines.append(f"--  {yyyymm} as 'Value'\n\n")

    for i, df in tables.items():
        meta = tables_meta[i]
        sel  = meta["select_num"]
        lines.append(f"----TABLE {i}" + "-"*100 + "\n\n")

        if i in (1,2,3):
            for _, r in df.iterrows():
                key = r[meta["key"]]
                for mat in meta["mats"]:
                    val = r.get(mat, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{key}','{mat}',{val}\n")

        elif i == 4:
            for _, r in df.iterrows():
                lab, val = r["Label"], r["Value"].strip()
                if val == "-":
                    continue
                m_ = re.match(r"^(-?\d+(?:\.\d+)?)[Ee]-(\d+)$", val)
                if m_:
                    coef, exp = m_.group(1), m_.group(2)
                    expr = f"{coef} * POWER(CAST(0.1 AS FLOAT), {exp}.0)"
                else:
                    expr = val
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','All',{expr}\n")

        elif i == 5:
            for _, r in df.iterrows():
                c = r["Country"]
                for m in meta["mats"]:
                    v = r.get(m, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{c}','{m}',{v}\n")

        elif i == 6:
            for _, r in df.iterrows():
                rat = r["Rating"]
                for cat in meta["cats"]:
                    v = r.get(cat, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{rat}','{cat}',{v}\n")

        elif i == 7:
            for _, r in df.iterrows():
                lab, v = r["Label"], r["Value"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','Loss given default (%)',{v}\n")

        elif i in (8,9):
            for _, r in df.iterrows():
                area = r[meta["key"]]
                for m in meta["mats"]:
                    v = r.get(m, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{area}','{m}',{v}\n")

        elif i in (10,11):
            for _, r in df.iterrows():
                ex, sh = r["ExchangeRateName"], r["Shock"]
                try:
                    float(sh)
                except:
                    continue
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{ex}','Shock',{sh}\n")

        elif i == 12:
            for _, r in df.iterrows():
                b, p = r["BucketInfo"], r["Pourcentage"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{b}','Bucket factor (%)',{p}\n")

        elif i == 13:
            for _, r in df.iterrows():
                inv, no = r["Investor"], r["NetOutflows(%)"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{inv}','Net outflows (%)',{no}\n")

        elif i == 14:
            for _, r in df.iterrows():
                lab, v = r["Label"], r["Value"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','Net outflows (%)',{v}\n")

        lines.append("\n")

    lines.append("--UNION SELECT 13,'Choc de marché','Choc de marché','Choc de marché (%)',95\n")

    # 5) Enregistrement sous "MMYYYYsqltxt.txt"
    os.makedirs(csv_dir, exist_ok=True) 
    name = f"{prefix}sqltxt.txt"
    with open(os.path.join(csv_dir, name), "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Fichier généré : {name}")

if __name__ == "__main__":
    intotxt(csv_dir="data/output")
