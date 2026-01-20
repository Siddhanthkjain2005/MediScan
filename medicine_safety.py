import pandas as pd
from difflib import get_close_matches

class MedicineSafetyChecker:
    def __init__(self, filepath='medicine_safety.csv'):
        # Load CSV (unchanged)
        self.df = pd.read_csv(filepath)

        # Debug (unchanged / optional)
        print("Loaded columns:", self.df.columns.tolist())

        # Normalized name column (unchanged)
        self.df['medicine_name_lower'] = (
            self.df['medicine_name']
            .astype(str)
            .str.lower()
            .str.strip()
        )

    def check_safety(self, extracted_name):
        name = extracted_name.strip().lower()

        # --------------------
        # Exact match
        # --------------------
        row_df = self.df[self.df['medicine_name_lower'] == name]
        if not row_df.empty:
            row = row_df.iloc[0]
            return {
                'found': True,
                'medicine_name': row['medicine_name'],
                'label': row['label'],
                'ingredients': row['ingredients'],

                # 🔹 ADDED ONLY (synthetic features)
                'avg_daily_dosage_mg': float(row['avg_daily_dosage_mg']),
                'side_effect_score': float(row['side_effect_score']),
                'toxicity_index': float(row['toxicity_index']),
                'interaction_count': int(row['interaction_count']),
                'graph_degree_centrality': float(row['graph_degree_centrality']),
                'graph_clustering_coeff': float(row['graph_clustering_coeff']),
            }

        # --------------------
        # Fuzzy match
        # --------------------
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

                # 🔹 ADDED ONLY (synthetic features)
                'avg_daily_dosage_mg': float(row['avg_daily_dosage_mg']),
                'side_effect_score': float(row['side_effect_score']),
                'toxicity_index': float(row['toxicity_index']),
                'interaction_count': int(row['interaction_count']),
                'graph_degree_centrality': float(row['graph_degree_centrality']),
                'graph_clustering_coeff': float(row['graph_clustering_coeff']),
            }

        # --------------------
        # Not found
        # --------------------
        return {
            'found': False
        }
