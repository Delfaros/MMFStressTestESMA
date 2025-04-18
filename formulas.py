import pandas as pd

tests = {
    'ET':   {'d2024': 1, 's2024': 2},
    'EEM':  {'d2024': 4, 's2024': 3},
    'CM':   {'d2024': 5, 's2024': 5},
    'ECRM': {'d2024': 5, 's2024': 10},
}

# Construction du dataFrame
rows = []
for name, vals in tests.items():
    d = vals['d2024']
    s = vals['s2024']
    rows.append({
        'Test': name,
        'd2024': d,
        's2024': s,
        'delta2024': d - s
    })
df = pd.DataFrame(rows)
print(df)
