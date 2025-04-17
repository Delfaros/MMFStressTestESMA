import os
import pandas as pd

def intotxt(csv_dir, output_txt):
    # Charger les CSV existants
    tables = {}
    for i in range(1, 15):
        path = os.path.join(csv_dir, f"table{i}.csv")
        if os.path.exists(path):
            tables[i] = pd.read_csv(path, dtype=str).fillna("")

    # Métadonnées, avec le numéro de SELECT qu'on souhaite
    tables_meta = {
        1:  {"select_num": 1,  "desc": "Liquidity discount factor - Sovereign bonds by residual maturity - Reference countries (in %)", "key": "Country",           "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        2:  {"select_num": 2,  "desc": "Liquidity discount factor - Sovereign bonds by rating and residual maturity (in %)",       "key": "Rating",            "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        3:  {"select_num": 3,  "desc": "Liquidity discount factor - Corporate bonds by rating and residual maturity (in %)",      "key": "Rating",            "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        4:  {"select_num": 4,  "desc": "Price impact parameter (in %)",                                                    "key": "Label",             "val": "Value"},
        5:  {"select_num": 5,  "desc": "Credit Spread by residual maturity - Government bonds (basis points)",             "key": "Country",           "mats": ["3M","6M","1Y","2Y"]},
        6:  {"select_num": 6,  "desc": "Corporate credit spreads (basis points)",                                      "key": "Rating",            "cats": ["Non-financial","Financial covered","Financial","ABS"]},
        7:  {"select_num": 7,  "desc": "Loss given default",                                                          "key": "Label",             "val": "Value"},
        8:  {"select_num": 8,  "desc": "Interest rate yield shocks absolute changes (basis points)",                     "key": "Country",           "mats": ["1M","3M","6M","1Y","2Y"]},
        9:  {"select_num": 8,  "desc": "Interest rate yield shocks absolute changes (basis points)",                     "key": "Geographic Area",   "mats": ["1M","3M","6M","1Y","2Y"]},
        10: {"select_num": 9,  "desc": "FX shocks (appreciation of the EUR against the USD) relative changes (%)",        "key": "ExchangeRateName",  "val": "Shock"},
        11: {"select_num": 10, "desc": "FX shocks (depreciation of the EUR against the USD) relative changes (%)",        "key": "ExchangeRateName",  "val": "Shock"},
        12: {"select_num": 12, "desc": "Bucket factor",                                                               "key": "BucketInfo",        "val": "Pourcentage"},
        13: {"select_num": 11, "desc": "Net outflows (level of redemption)",                                          "key": "Investor",          "val": "NetOutflows(%)"},
        14: {"select_num": 14, "desc": "Net outflows (macro systematic shocks)",                                       "key": "Label",             "val": "Value"},
    }

    lines = []
    # === Nouveau bloc à injecter avant TABLE 1 ===
    lines.append("--ELSE IF @DateEtalonnage >= '01/01/2025' and @DateEtalonnage <= '31/12/2025'\n")
    lines.append("--INSERT INTO [MarketDate].[dbo].[ST_MMF_Parameters]\n")
    lines.append("--SELECT\n")
    lines.append("--  0 as 'Table_ID'\n")
    lines.append("--  'Etalonnages' as 'Table_Description'\n")
    lines.append("--  'YYYY/MM étalonnages' as 'Line_Description'\n")
    lines.append("--  'YYYY/MM étalonnages' as 'Column_Description'\n")
    lines.append("--  202501 as 'Value'\n\n")
    # ============================================

    for i, df in tables.items():
        meta = tables_meta[i]
        sel  = meta["select_num"]

        # Section header
        lines.append(f"----TABLE {i}" + "-"*115 + "\n\n")

        # 1,2,3 : mêmes mats
        if i in (1,2,3):
            for _, r in df.iterrows():
                key = r[meta["key"]]
                for mat in meta["mats"]:
                    val = r.get(mat, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{key}','{mat}',{val}\n")

        # 4 : pied de page
        elif i == 4:
            for _, r in df.iterrows():
                lab, val = r["Label"], r["Value"]
                expr = "POWER(CAST(0.1 AS FLOAT), 13.0)" if "E-13" in val \
                       else f"{val} * POWER(CAST(0.1 AS FLOAT), 13.0)"
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','All',{expr}\n")

        # 5 : country + mats
        elif i == 5:
            for _, r in df.iterrows():
                c = r["Country"]
                for m in meta["mats"]:
                    v = r.get(m, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{c}','{m}',{v}\n")

        # 6 : rating + cats
        elif i == 6:
            for _, r in df.iterrows():
                rat = r["Rating"]
                for cat in meta["cats"]:
                    v = r.get(cat, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{rat}','{cat}',{v}\n")

        # 7 : label + value fixe
        elif i == 7:
            for _, r in df.iterrows():
                lab, v = r["Label"], r["Value"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','Loss given default (%)',{v}\n")

        # 8 & 9 : zone + mats
        elif i in (8,9):
            for _, r in df.iterrows():
                ct = r[meta["key"]]
                for m in meta["mats"]:
                    v = r.get(m, "")
                    lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{ct}','{m}',{v}\n")

        # 10 & 11 : FX shocks
        elif i in (10,11):
            for _, r in df.iterrows():
                ex, sh = r["ExchangeRateName"], r["Shock"]
                try:
                    float(sh)
                except:
                    continue
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{ex}','Shock',{sh}\n")

        # 12 : buckets
        elif i == 12:
            for _, r in df.iterrows():
                b, p = r["BucketInfo"], r["Pourcentage"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{b}','Bucket factor (%)',{p}\n")

        # 13 : net outflows
        elif i == 13:
            for _, r in df.iterrows():
                inv, no = r["Investor"], r["NetOutflows(%)"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{inv}','Net outflows (%)',{no}\n")

        # 14 : macro shocks
        elif i == 14:
            for _, r in df.iterrows():
                lab, v = r["Label"], r["Value"]
                lines.append(f"--UNION SELECT {sel},'{meta['desc']}','{lab}','Net outflows (%)',{v}\n")

        lines.append("\n")

    # Ligne finale fixe
    lines.append("--UNION SELECT 13,'Choc de marché','Choc de marché','Choc de marché (%)',95\n")

    # Écriture
    os.makedirs(csv_dir, exist_ok=True)
    with open(os.path.join(csv_dir, output_txt), "w", encoding="utf-8") as f:
        f.writelines(lines)

# Exécution
intotxt(csv_dir="data/output", output_txt="sql.txt")
print("Terminé – sql.txt généré.")  
