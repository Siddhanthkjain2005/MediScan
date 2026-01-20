import pandas as pd
from difflib import get_close_matches

class MedicineSafetyChecker:
    def __init__(self, filepath='medicine_safety.csv'):
        self.df = pd.read_csv(filepath)  # ✅ REMOVE sep="\t"

        # Safety check (optional but recommended)
        print("Loaded columns:", self.df.columns.tolist())

        self.df['medicine_name_lower'] = (
            self.df['medicine_name']
            .astype(str)
            .str.lower()
            .str.strip()
        )

    def check_safety(self, extracted_name):
     name = extracted_name.strip().lower()

    # Exact match
     row = self.df[self.df['medicine_name_lower'] == name]
     if not row.empty:
        row = row.iloc[0]
        return {
            'found': True,
            'medicine_name': row['medicine_name'],
            'label': row['label'],
            'ingredients': row['ingredients'],
            'source': 'exact'
        }

    # Fuzzy match
     candidates = get_close_matches(
        name,
        self.df['medicine_name_lower'].tolist(),
        n=1,
        cutoff=0.7
     )

     if candidates:
        row = self.df[self.df['medicine_name_lower'] == candidates[0]].iloc[0]
        return {
            'found': True,
            'medicine_name': row['medicine_name'],
            'label': row['label'],
            'ingredients': row['ingredients'],
            'source': 'fuzzy'
        }

     return {
        'found': False
    }
