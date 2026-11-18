import random
import csv
from pathlib import Path

# Consumi e tempi di consegna sono ipotesi del progetto.
mesi = 36
materiali = [
    "alluminio",
    "acciaio_carbonio",
    "acciaio_inox",
    "rame",
]

lead_time_mesi = {
    "alluminio": 3,
    "acciaio_carbonio": 2,
    "acciaio_inox": 1,
    "rame": 6,
}

consumo_base_kg = {
    "alluminio": 40000,
    "acciaio_carbonio": 200000,
    "acciaio_inox": 10000,
    "rame": 2000,
}

profili_domanda = {
    "alluminio": "trend",
    "acciaio_carbonio": "stagionale",
    "acciaio_inox": "variabile",
    "rame": "stabile",
}

anno = 2023
mese = 11
date_mensili = []

for i in range(mesi):
    date_mensili.append(f"{anno}-{mese:02d}")

    mese += 1
    if mese == 13:
        mese = 1
        anno += 1

random.seed(42)  # Per riottenere gli stessi consumi conta anche l'ordine delle estrazioni.

consumi_rame_kg = []

for data_mese in date_mensili:
    consumo = random.randint(1800, 2200)
    consumi_rame_kg.append(consumo)

consumi_inox_kg = []

for data_mese in date_mensili:
    consumo = random.randint(7500, 12500)
    consumi_inox_kg.append(consumo)

consumi_alluminio_kg = []

for i in range(mesi):
    valore_trend = consumo_base_kg["alluminio"] + 200 * i
    oscillazione = random.randint(-2000, 2000)
    consumo = valore_trend + oscillazione
    consumi_alluminio_kg.append(consumo)

fattori_stagionali = {
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 0.8,
    9: 1.1,
    10: 1.1,
    11: 1.1,
    12: 0.9,
}

consumi_carbonio_kg = []

for data_mese in date_mensili:
    numero_mese = int(data_mese[5:7])
    fattore = fattori_stagionali[numero_mese]

    consumo_stagionale = consumo_base_kg["acciaio_carbonio"] * fattore
    oscillazione = random.randint(-10000, 10000)
    consumo = round(consumo_stagionale) + oscillazione

    consumi_carbonio_kg.append(consumo)

consumi_per_materiale = {
    "alluminio": consumi_alluminio_kg,
    "acciaio_carbonio": consumi_carbonio_kg,
    "acciaio_inox": consumi_inox_kg,
    "rame": consumi_rame_kg,
}

dataset = []

for i in range(mesi):
    for materiale in materiali:
        riga = {
            "mese": date_mensili[i],
            "materiale": materiale,
            "consumo_kg": consumi_per_materiale[materiale][i],
            "lead_time_mesi": lead_time_mesi[materiale],
        }
        dataset.append(riga)

print("Righe del dataset:", len(dataset))
print("Prima riga:", dataset[0])

percorso_csv = Path(__file__).resolve().parent / "domanda_sintetica.csv"

with percorso_csv.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(
        file,
        fieldnames=["mese", "materiale", "consumo_kg", "lead_time_mesi"],
    )
    scrittore.writeheader()
    scrittore.writerows(dataset)

print("File salvato:", percorso_csv.name)
