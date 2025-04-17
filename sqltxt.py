import os
import pandas as pd

def generate_sql_comments_final(csv_dir, output_txt):
    """
    Lit les CSV table1.csv jusqu'à table14.csv dans `csv_dir` et génère
    un fichier .txt formaté selon l'exemple fourni.
    """
    # Charger en string pour préserver le format exact des nombres
    tables = {}
    for i in range(1, 15):
        path = os.path.join(csv_dir, f"table{i}.csv")
        if os.path.exists(path):
            tables[i] = pd.read_csv(path, dtype=str)

    lines = []
    # Définition des descriptions et colonnes clés
    tables_meta = {
        1: {"desc": "Liquidity discount factor - Sovereign bonds by residual maturity - Reference countries (in %)", "key": "Country", "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        2: {"desc": "Liquidity discount factor - Sovereign bonds by rating and residual maturity (in %)", "key": "Rating", "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        3: {"desc": "Liquidity discount factor - Corporate bonds by rating and residual maturity (in %)", "key": "Rating", "mats": ["3M","6M","1Y","1.5Y","2Y"]},
        4: {"desc": "Price impact parameter (in %)", "key": "Label", "val": "Value"},
        5: {"desc": "Credit Spread by residual maturity - Government bonds (basis points)", "key": "Country", "mats": ["3M","6M","1Y","2Y"]},
        6: {"desc": "Corporate credit spreads (basis points)", "key": "Rating", "cats": ["Non-financial","Financial covered","Financial","ABS"]},
        7: {"desc": "Loss given default", "key": "Label", "val": "Value"},
        8: {"desc": "Interest rate yield shocks absolute changes (basis points)", "key": "GeoCountryDesc", "mats": ["1M","3M","6M","1Y","2Y"]},
        9: {"desc": "Interest rate yield shocks absolute changes (basis points)", "key": "Geographic Area", "mats": ["1M","3M","6M","1Y","2Y"]},
        10: {"desc": "FX shocks (appreciation of the EUR against the USD) relative changes (%)", "key": "ExchangeRateName", "val": "Shock"},
        11: {"desc": "FX shocks (depreciation of the EUR against the USD) relative changes (%)", "key": "ExchangeRateName", "val": "Shock"},
        12: {"desc": "Bucket factor", "key": "BucketInfo", "val": "Pourcentage"},
        13: {"desc": "Net outflows (level of redemption)", "key": "Investor", "val": "NetOutflows(%)"},
        14: {"desc": "Net outflows (macro systematic shocks)", "key": "Label", "val": "Value"},
    }

    # Generate sections
    for num in range(1, 15):
        if num not in tables:
            continue
        df = tables[num]
        meta = tables_meta[num]
        # Header line with ~115 dashes total
        dash_count = 115
        lines.append(f"----TABLE {num}" + "-" * dash_count + "\n\n")
        desc = meta["desc"]

        if num in (1,2,3):
            for _, row in df.iterrows():
                key = row[meta["key"]]
                for mat in meta["mats"]:
                    val = row.get(mat, "")
                    lines.append(f"--UNION SELECT {num},'{desc}','{key}','{mat}',{val}\n")
        elif num == 4:
            for _, row in df.iterrows():
                label = row["Label"]
                value = row["Value"]
                if "E-13" in value:
                    expr = "POWER(CAST(0.1 AS FLOAT), 13.0)"
                else:
                    expr = f"{value} * POWER(CAST(0.1 AS FLOAT), 13.0)"
                lines.append(f"--UNION SELECT {num},'{desc}','{label}','All',{expr}\n")
        elif num == 5:
            for _, row in df.iterrows():
                country = row["Country"]
                for mat in meta["mats"]:
                    val = row.get(mat, "")
                    lines.append(f"--UNION SELECT {num},'{desc}','{country}','{mat}',{val}\n")
        elif num == 6:
            for _, row in df.iterrows():
                rating = row["Rating"]
                for cat in meta["cats"]:
                    val = row.get(cat, "")
                    lines.append(f"--UNION SELECT {num},'{desc}','{rating}','{cat}',{val}\n")
        elif num == 7:
            for _, row in df.iterrows():
                label = row["Label"]
                val = row["Value"]
                lines.append(f"--UNION SELECT {num},'{desc}','{label}','Loss given default (%)',{val}\n")
        elif num in (8,9):
            for _, row in df.iterrows():
                area = row[meta["key"]]
                for mat in meta["mats"]:
                    val = row.get(mat, "")
                    lines.append(f"--UNION SELECT {num},'{desc}','{area}','{mat}',{val}\n")
        elif num in (10,11):
            for _, row in df.iterrows():
                exch = row["ExchangeRateName"]
                shock = row["Shock"]
                try:
                    float(shock)
                except:
                    continue
                lines.append(f"--UNION SELECT {num},'{desc}','{exch}','Shock',{shock}\n")
        elif num == 12:
            for _, row in df.iterrows():
                bucket = row["BucketInfo"]
                pct = row["Pourcentage"]
                lines.append(f"--UNION SELECT {num},'{desc}','{bucket}','Bucket factor (%)',{pct}\n")
        elif num == 13:
            for _, row in df.iterrows():
                inv = row["Investor"]
                val = row["NetOutflows(%)"]
                lines.append(f"--UNION SELECT {num},'{desc}','{inv}','Net outflows (%)',{val}\n")
        elif num == 14:
            for _, row in df.iterrows():
                label = row["Label"]
                val = row["Value"]
                lines.append(f"--UNION SELECT {num},'{desc}','{label}','Net outflows (%)',{val}\n")
        lines.append("\n")

    # Append dummy UNION SELECT 13
    lines.append("--UNION SELECT 13,'Choc de marché','Choc de marché','Choc de marché (%)',95\n")

    # Ensure output directory exists
    os.makedirs(csv_dir, exist_ok=True)
    # Write to final txt in csv_dir
    with open(os.path.join(csv_dir, output_txt), "w", encoding="utf-8") as f:
        f.writelines(lines)

# Execute
generate_sql_comments_final(csv_dir="data/output", output_txt="sql.txt")

print("caca")
