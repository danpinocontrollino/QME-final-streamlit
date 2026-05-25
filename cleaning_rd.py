import pandas as pd

# 1. Carica il dataset principale delle università
df_master = pd.read_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/actual_implementation/final_merged_dataset.csv')

# 2. Carica il file R&D che abbiamo pulito nello step precedente
df_rd = pd.read_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/cleaned_world_bank_rd.csv')

# 3. Rimuoviamo la colonna inutile e rinominiamo l'anno
df_rd = df_rd.drop(columns=['Indicator Name'])
df_rd = df_rd.rename(columns={'2026': 'R&D Expenditure (%)'})

# 4. IL MERGE REALE (Left Join)
# Questo comando aggancia i valori R&D basandosi sulla colonna 'Country'.
# 'how="left"' assicura che le nazioni del World Bank assenti nel tuo df_master vengano scartate.
df_final = pd.merge(df_master, df_rd, on='Country', how='left')

# Opzionale: Rimuoviamo il 'Country Code' se non ti serve nel cruscotto
if 'Country Code' in df_final.columns:
    df_final = df_final.drop(columns=['Country Code'])

# 5. Gestione dei valori mancanti (Safety Check)
# Se una nazione nel tuo dataset non ha dati R&D (es. Taiwan non è tracciata dalla World Bank), 
# possiamo assegnare la media globale (es. 1.5%) per evitare che i grafici si rompano.
df_final['R&D Expenditure (%)'] = df_final['R&D Expenditure (%)'].fillna(1.5)

# 6. Salviamo il dataset definitivo pronto per il cruscotto
df_final.to_csv('final_merged_dataset_with_RD.csv', index=False)

print("✅ Merge completato con successo!")
print(f"Righe nel dataset originale: {len(df_master)}")
print(f"Righe nel nuovo dataset: {len(df_final)}") # Dovrebbe essere identico!
print("\nAnteprima delle nuove colonne:")
print(df_final[['Name', 'Country', 'R&D Expenditure (%)']].head())