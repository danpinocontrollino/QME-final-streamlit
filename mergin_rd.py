import pandas as pd

def clean_world_bank_data(input_csv, output_csv):
    print("⏳ Caricamento del dataset in corso...")
    
    # 1. Saltiamo le prime 4 righe (standard dei CSV scaricati dalla World Bank)
    # Se il tuo file è stato già modificato e ha solo 1 riga inutile, cambia in skiprows=1
    df = pd.read_csv(input_csv, skiprows=4)
    
    # Rimuoviamo eventuali colonne fantasma alla fine del CSV (come 'Unnamed: 68')
    df = df.dropna(axis=1, how='all')
    
    # 2. Identifichiamo le colonne fisse (metadata) e quelle degli anni
    meta_cols = ['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code']
    year_cols = [col for col in df.columns if col not in meta_cols]
    
    print("🔍 Ricerca del dato più recente per ogni nazione...")
    
    # 3. LA MAGIA: Troviamo l'ultimo numero valido disponibile (escludendo i NaN)
    # ffill(axis=1) copia l'ultimo numero verso destra. 
    # iloc[:, -1] prende l'ultimissima colonna risultante (che ora contiene l'ultimo anno valido).
    df['2026'] = df[year_cols].ffill(axis=1).iloc[:, -1]
    
    # 4. Rimuoviamo tutte le vecchie colonne degli anni, tenendo solo la nostra nuova colonna '2026'
    final_cols = ['Country Name', 'Country Code', 'Indicator Name', '2026']
    df_clean = df[final_cols]
    
    # Rinominiamo 'Country Name' in 'Country' per rendere facilissimo il merge successivo con il tuo dataset principale
    df_clean = df_clean.rename(columns={'Country Name': 'Country'})
    
    # 5. Salviamo il nuovo dataset pulito
    df_clean.to_csv(output_csv, index=False)
    
    print(f"✅ Pulizia completata! Il file è stato salvato come: {output_csv}")
    print("\nEcco un'anteprima dei dati puliti:")
    print(df_clean[['Country', '2026']].dropna().head())

# Eseguiamo la funzione
# Sostituisci il nome del file input se necessario
clean_world_bank_data(
    input_csv='/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/actual_implementation/world_bank_rd.csv', 
    output_csv='cleaned_world_bank_rd.csv'
)