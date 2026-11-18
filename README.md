# Quando ordinare le materie prime? Il caso Moretto

Per questo project work ho realizzato una dashboard in Python che aiuta a rispondere a due domande: **quanto materiale ordinare e quando far partire l’ordine?** Per rispondere servono tre informazioni: quanto materiale si prevede di consumare, quanto ce n’è in magazzino e quanto tempo impiega il fornitore a consegnarlo.

Il progetto prende come riferimento il caso Moretto e considera quattro materiali: alluminio, acciaio al carbonio, acciaio inox e rame. I consumi e i dati di magazzino sono sintetici e servono a simulare situazioni diverse.

## Come leggere la dashboard

Scegli un materiale e apri una delle tre schede:

- **Domanda** mostra i consumi degli ultimi 36 mesi e le previsioni future. Puoi vedere quale dei quattro metodi previsionali ha commesso l’errore più basso per quel materiale.
- **Scorte** mostra il primo ordine da emettere, sia in chilogrammi sia in bobine intere (*coil*). Il grafico distingue il materiale già in magazzino da quello ordinato e non ancora ricevuto.
- **Scenari** permette di cambiare i consumi o i tempi di consegna e vedere cosa succede agli ordini e alle scorte.

Per fare una prova, seleziona **Alluminio** e, nella scheda **Scenari**, porta il tempo di consegna da **3 a 6 mesi**. Il primo ordine sale da **9 a 39 bobine**. Il materiale in magazzino si esaurisce in attesa della prima consegna e i mesi con arretrati passano da **0 a 3**.

## Come avviarla

Serve Python 3.12. Scarica il progetto, estrai la cartella e apri il terminale dove si trova `requirements.txt`. I dati sono già inclusi. Esegui i tre comandi per il tuo sistema.

**macOS o Linux**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run dashboard/app.py
```

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Apri nel browser l’indirizzo indicato da Streamlit.

*Project work L-31 · Informatica per le Aziende Digitali · Università Telematica Pegaso · Traccia PW24*
