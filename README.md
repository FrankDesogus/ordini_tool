# Ordini Tool (PyQt + SQLite)

Tool desktop in Python per gestire:
- Fornitori
- Ordini
- Certificazioni

## Avvio rapido
1. Crea un virtualenv e installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
2. Avvia:
   ```bash
   python main.py
   ```

## Database
- SQLite (file locale): `data/app.db`
- Migrazioni: per semplicità la prima versione crea automaticamente le tabelle all'avvio.

## Import CSV
Menu: **File → Importa CSV**
- Importa Fornitori, Ordini, Certificazioni
- Upsert: usa `external_uid` come chiave univoca (se esiste aggiorna, altrimenti inserisce)

## KPI
Campo `puntualita_consegne_pct` in `fornitori` è calcolabile dal software (pulsante nel tab Fornitori).
Regola:
- Considera un ordine "valutabile" se ha `data_effettiva` e almeno una tra `data_conferma` o `data_richiesta`
- È "puntuale" se `data_effettiva <= data_conferma` (se presente) altrimenti `<= data_richiesta`
- KPI = puntuali / valutabili * 100
