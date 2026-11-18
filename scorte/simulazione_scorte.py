import csv
from pathlib import Path
from math import ceil
import matplotlib.pyplot as plt

cartella_progetto = Path(__file__).resolve().parent.parent

percorso_previsioni = (
    cartella_progetto / "previsioni" / "previsioni_future.csv"
)

percorso_piano = (
    cartella_progetto / "scorte" / "pianificazione_iniziale.csv"
)

with percorso_previsioni.open("r", newline="", encoding="utf-8") as file:
    dati_previsti = list(csv.DictReader(file))

with percorso_piano.open("r", newline="", encoding="utf-8") as file:
    piano_iniziale = list(csv.DictReader(file))

# Caso base: consumi uguali alle previsioni e arrivi puntuali.
mesi_simulazione = 12

print("Previsioni caricate:", len(dati_previsti))
print("Materiali caricati:", len(piano_iniziale))
print("Mesi da simulare:", mesi_simulazione)

previsioni_per_materiale = {}

for riga in dati_previsti:
    materiale = riga["materiale"]

    if materiale not in previsioni_per_materiale:
        previsioni_per_materiale[materiale] = []

    previsioni_per_materiale[materiale].append({
        "mese": riga["mese"],
        "domanda_kg": float(riga["previsione_kg"]),
    })

for materiale, previsioni in previsioni_per_materiale.items():
    print(
        materiale,
        "- mesi disponibili:", len(previsioni),
        "- primo mese:", previsioni[0]["mese"],
        "- ultimo mese:", previsioni[-1]["mese"],
    )

revisione_mesi = 1
risultati_simulazione = []

for parametri in piano_iniziale:
    materiale = parametri["materiale"]
    lead_time = int(parametri["lead_time_mesi"])
    peso_coil = float(parametri["peso_coil_kg"])
    scorta_sicurezza = float(parametri["scorta_sicurezza_kg"])

    # Un saldo di -100 kg indica che restano da soddisfare 100 kg di domanda.
    saldo = float(parametri["giacenza_iniziale_kg"])
    previsioni = previsioni_per_materiale[materiale]
    arrivi_programmati = [0.0] * len(previsioni)

    for i in range(mesi_simulazione):
        mese = previsioni[i]["mese"]
        domanda = previsioni[i]["domanda_kg"]

        # A inizio mese si ricevono le consegne. Poi si ordina e infine si scala il consumo.
        arrivi = arrivi_programmati[i]
        saldo += arrivi

        # Include anche gli ordini che arriveranno dopo i 12 mesi simulati.
        pipeline = sum(arrivi_programmati[i + 1:])
        posizione_scorte = saldo + pipeline

        copertura = lead_time + revisione_mesi
        finestra = previsioni[i:i + copertura]

        if len(finestra) < copertura:
            raise ValueError(f"Previsioni insufficienti per {materiale}")

        domanda_copertura = 0
        for previsione in finestra:
            domanda_copertura += previsione["domanda_kg"]

        obiettivo = domanda_copertura + scorta_sicurezza
        fabbisogno = max(0, obiettivo - posizione_scorte)

        numero_coil = ceil(fabbisogno / peso_coil)
        quantita_ordine = numero_coil * peso_coil

        arrivi_programmati[i + lead_time] += quantita_ordine
        pipeline += quantita_ordine

        saldo -= domanda

        risultati_simulazione.append({
            "mese": mese,
            "materiale": materiale,
            "domanda_kg": domanda,
            "arrivi_kg": arrivi,
            "numero_coil_ordinati": numero_coil,
            "ordine_kg": quantita_ordine,
            "giacenza_fine_kg": max(0, saldo),
            "arretrati_fine_kg": max(0, -saldo),
            "pipeline_fine_kg": pipeline,
            "livello_obiettivo_kg": obiettivo,
        })

print("Righe simulate:", len(risultati_simulazione))
print("Prima riga:", risultati_simulazione[0])

percorso_simulazione = (
    cartella_progetto
    / "risultati"
    / "simulazione_scorte.csv"
)

campi = list(risultati_simulazione[0].keys())

with percorso_simulazione.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(file, fieldnames=campi)
    scrittore.writeheader()
    scrittore.writerows(risultati_simulazione)

print("Simulazione salvata:", percorso_simulazione.name)

for parametri in piano_iniziale:
    materiale = parametri["materiale"]
    giacenza_iniziale = float(parametri["giacenza_iniziale_kg"])

    totale_arrivi = 0
    totale_consumi = 0
    totale_ordini = 0
    mesi_con_arretrati = 0

    for riga in risultati_simulazione:
        if riga["materiale"] != materiale:
            continue

        totale_arrivi += riga["arrivi_kg"]
        totale_consumi += riga["domanda_kg"]
        totale_ordini += riga["ordine_kg"]

        saldo_atteso = giacenza_iniziale + totale_arrivi - totale_consumi
        saldo_registrato = (
            riga["giacenza_fine_kg"] - riga["arretrati_fine_kg"]
        )

        pipeline_attesa = totale_ordini - totale_arrivi

        if abs(saldo_atteso - saldo_registrato) > 0.01:
            raise ValueError(
                f"Bilancio giacenze errato: {materiale}, {riga['mese']}"
            )

        if abs(pipeline_attesa - riga["pipeline_fine_kg"]) > 0.01:
            raise ValueError(
                f"Bilancio pipeline errato: {materiale}, {riga['mese']}"
            )

        if riga["arretrati_fine_kg"] > 0.01:
            mesi_con_arretrati += 1

    print(
        materiale,
        "- bilanci corretti",
        "- mesi con arretrati:", mesi_con_arretrati,
    )

for parametri in piano_iniziale:
    materiale = parametri["materiale"]
    sicurezza = float(parametri["scorta_sicurezza_kg"])

    mesi = []
    giacenze = []
    pipeline = []

    for riga in risultati_simulazione:
        if riga["materiale"] == materiale:
            mesi.append(riga["mese"])
            giacenze.append(riga["giacenza_fine_kg"])
            pipeline.append(riga["pipeline_fine_kg"])

    plt.figure(figsize=(12, 5))

    plt.plot(
        mesi, giacenze,
        marker="o",
        label="Giacenza a fine mese",
    )

    plt.plot(
        mesi, pipeline,
        marker="o",
        linestyle="--",
        label="Ordini in arrivo a fine mese",
    )

    plt.axhline(
        sicurezza,
        color="red",
        linestyle=":",
        label="Scorta di sicurezza di riferimento",
    )

    nome = materiale.replace("_", " ").capitalize()
    plt.title(f"{nome} — simulazione base delle scorte")
    plt.xlabel("Mese")
    plt.ylabel("Quantità (kg)")
    plt.xticks(rotation=45)
    plt.ylim(0, max(giacenze + pipeline + [sicurezza]) * 1.1)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    percorso_grafico = (
        cartella_progetto
        / "risultati"
        / f"scorte_{materiale}.png"
    )

    plt.savefig(percorso_grafico, dpi=150)
    plt.close()

    print("Grafico salvato:", percorso_grafico.name)

for parametri in piano_iniziale:
    if parametri["materiale"] == "acciaio_carbonio":
        parametri_carbonio = parametri

# Per la prova sull'acciaio al carbonio si anticipano tre bobine già previste, da settembre ad agosto.
scenario_anticipato = {}

for riga in risultati_simulazione:
    if riga["materiale"] == "acciaio_carbonio":
        scenario_anticipato[riga["mese"]] = riga.copy()

coil_anticipati = 3
peso_coil = float(parametri_carbonio["peso_coil_kg"])
quantita_anticipata = coil_anticipati * peso_coil

if int(parametri_carbonio["lead_time_mesi"]) != 2:
    raise ValueError("Questo scenario prevede un lead time di 2 mesi")

if scenario_anticipato["2027-07"]["ordine_kg"] < quantita_anticipata:
    raise ValueError("L'ordine di luglio non contiene abbastanza coil")

scenario_anticipato["2027-06"]["numero_coil_ordinati"] += coil_anticipati
scenario_anticipato["2027-06"]["ordine_kg"] += quantita_anticipata

scenario_anticipato["2027-07"]["numero_coil_ordinati"] -= coil_anticipati
scenario_anticipato["2027-07"]["ordine_kg"] -= quantita_anticipata

scenario_anticipato["2027-08"]["arrivi_kg"] += quantita_anticipata
scenario_anticipato["2027-09"]["arrivi_kg"] -= quantita_anticipata

saldo = float(parametri_carbonio["giacenza_iniziale_kg"])
pipeline = 0.0

for mese in sorted(scenario_anticipato):
    riga = scenario_anticipato[mese]

    saldo += riga["arrivi_kg"] - riga["domanda_kg"]
    pipeline += riga["ordine_kg"] - riga["arrivi_kg"]

    riga["giacenza_fine_kg"] = max(0, saldo)
    riga["arretrati_fine_kg"] = max(0, -saldo)
    riga["pipeline_fine_kg"] = pipeline

for mese in ["2027-06", "2027-07", "2027-08", "2027-09"]:
    riga = scenario_anticipato[mese]

    print(
        mese,
        "- ordine:", round(riga["ordine_kg"], 2),
        "- arrivi:", round(riga["arrivi_kg"], 2),
        "- giacenza:", round(riga["giacenza_fine_kg"], 2),
        "kg",
    )

confronto_scorte = []

for riga_base in risultati_simulazione:
    if riga_base["materiale"] != "acciaio_carbonio":
        continue

    mese = riga_base["mese"]
    riga_anticipata = scenario_anticipato[mese]

    giacenza_base = riga_base["giacenza_fine_kg"]
    giacenza_anticipata = riga_anticipata["giacenza_fine_kg"]
    differenza = giacenza_anticipata - giacenza_base

    confronto_scorte.append({
        "mese": mese,
        "giacenza_base_kg": giacenza_base,
        "giacenza_anticipata_kg": giacenza_anticipata,
        "differenza_giacenza_kg": differenza,
    })

    if mese in ["2027-08", "2027-09"]:
        print(
            mese,
            "- giacenza base:", round(giacenza_base, 2),
            "- giacenza anticipata:", round(giacenza_anticipata, 2),
            "- differenza:", round(differenza, 2),
            "kg",
        )

percorso_confronto = (
    cartella_progetto
    / "risultati"
    / "confronto_scorta_anticipata.csv"
)

with percorso_confronto.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(
        file,
        fieldnames=list(confronto_scorte[0].keys()),
    )
    scrittore.writeheader()
    scrittore.writerows(confronto_scorte)

print("Confronto salvato:", percorso_confronto.name)

mesi_confronto = []
giacenze_base = []
giacenze_anticipate = []

for riga in confronto_scorte:
    mesi_confronto.append(riga["mese"])
    giacenze_base.append(riga["giacenza_base_kg"])
    giacenze_anticipate.append(riga["giacenza_anticipata_kg"])

plt.figure(figsize=(12, 5))

plt.plot(
    mesi_confronto,
    giacenze_base,
    marker="o",
    label="Piano base",
)

plt.plot(
    mesi_confronto,
    giacenze_anticipate,
    marker="o",
    linestyle="--",
    label="Arrivo anticipato di 3 coil",
)

plt.fill_between(
    mesi_confronto,
    giacenze_base,
    giacenze_anticipate,
    alpha=0.2,
    color="orange",
    label="Differenza di giacenza",
)

plt.title("Acciaio al carbonio — scenario di approvvigionamento anticipato")
plt.xlabel("Mese")
plt.ylabel("Giacenza a fine mese (kg)")
plt.xticks(rotation=45)
plt.ylim(0, max(giacenze_base + giacenze_anticipate) * 1.1)
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

percorso_grafico = (
    cartella_progetto
    / "risultati"
    / "confronto_scorta_anticipata.png"
)

plt.savefig(percorso_grafico, dpi=150)
plt.close()

print("Grafico salvato:", percorso_grafico.name)

totale_ordini_base = sum(
    riga["ordine_kg"]
    for riga in risultati_simulazione
    if riga["materiale"] == "acciaio_carbonio"
)

totale_ordini_anticipati = sum(
    riga["ordine_kg"]
    for riga in scenario_anticipato.values()
)

if abs(totale_ordini_base - totale_ordini_anticipati) > 0.01:
    raise ValueError("Gli acquisti totali dei due scenari sono diversi")

saldo_atteso = float(parametri_carbonio["giacenza_iniziale_kg"])
pipeline_attesa = 0.0
mesi_con_arretrati = 0

for mese in sorted(scenario_anticipato):
    riga = scenario_anticipato[mese]

    saldo_atteso += riga["arrivi_kg"] - riga["domanda_kg"]
    pipeline_attesa += riga["ordine_kg"] - riga["arrivi_kg"]

    saldo_registrato = (
        riga["giacenza_fine_kg"] - riga["arretrati_fine_kg"]
    )

    if abs(saldo_atteso - saldo_registrato) > 0.01:
        raise ValueError(f"Bilancio giacenze errato nello scenario: {mese}")

    if abs(pipeline_attesa - riga["pipeline_fine_kg"]) > 0.01:
        raise ValueError(f"Bilancio pipeline errato nello scenario: {mese}")

    if riga["pipeline_fine_kg"] < -0.01:
        raise ValueError(f"Pipeline negativa nello scenario: {mese}")

    if riga["arretrati_fine_kg"] > 0.01:
        mesi_con_arretrati += 1

print("Acquisti totali piano base:", round(totale_ordini_base, 2), "kg")
print("Acquisti totali anticipati:", round(totale_ordini_anticipati, 2), "kg")
print("Scenario anticipato: bilanci corretti")
print("Scenario anticipato - mesi con arretrati:", mesi_con_arretrati)
