import csv
from pathlib import Path
from statistics import linear_regression

cartella_progetto = Path(__file__).resolve().parent.parent

percorso_dati = (
    cartella_progetto / "dati" / "domanda_sintetica.csv"
)

percorso_metodi = (
    cartella_progetto / "risultati" / "metodi_selezionati.csv"
)

with percorso_dati.open("r", newline="", encoding="utf-8") as file:
    dati = list(csv.DictReader(file))

with percorso_metodi.open("r", newline="", encoding="utf-8") as file:
    scelte = list(csv.DictReader(file))

metodi_selezionati = {}

for riga in scelte:
    metodi_selezionati[riga["materiale"]] = riga["metodo"]

# Per il rame, con sei mesi di consegna, alla revisione del mese 12 servono previsioni fino al mese 18.
orizzonte = 18

print("Righe storiche lette:", len(dati))
print("Metodi caricati:", metodi_selezionati)

ultimo_mese = dati[-1]["mese"]

anno = int(ultimo_mese[:4])
mese = int(ultimo_mese[5:7])

date_future = []

for i in range(orizzonte):
    mese += 1

    if mese == 13:
        mese = 1
        anno += 1

    date_future.append(f"{anno}-{mese:02d}")

print("Mesi da prevedere:", len(date_future))
print("Prima previsione:", date_future[0])
print("Ultima previsione:", date_future[-1])

previsioni_future = {}

# Media e regressione usano tutti i 36 mesi disponibili.
# Il CMM3 usa gli ultimi tre mesi e il metodo stagionale riprende l'ultimo anno.
for materiale, metodo in metodi_selezionati.items():
    storico = []

    for riga in dati:
        if riga["materiale"] == materiale:
            storico.append(int(riga["consumo_kg"]))

    if metodo == "media":
        media = sum(storico) / len(storico)
        previsioni = [media] * orizzonte

    elif metodo == "cmm3":
        cmm3 = sum(storico[-3:]) / 3
        previsioni = [cmm3] * orizzonte

    elif metodo == "stagionale":
        ultimo_anno = storico[-12:]
        previsioni = []

        for i in range(orizzonte):
            previsioni.append(ultimo_anno[i % 12])

    elif metodo == "trend":
        pendenza, intercetta = linear_regression(
            range(len(storico)), storico
        )
        previsioni = []

        for i in range(orizzonte):
            mese_futuro = len(storico) + i
            previsione = intercetta + pendenza * mese_futuro
            previsioni.append(previsione)

    else:
        raise ValueError(f"Metodo non riconosciuto: {metodo}")

    previsioni_future[materiale] = previsioni

    print(
        materiale,
        "- metodo:", metodo,
        "- prima previsione:", round(previsioni[0], 2),
        "- ultima previsione:", round(previsioni[-1], 2),
        "kg",
    )

righe_previsioni = []

for i in range(orizzonte):
    for materiale, previsioni in previsioni_future.items():
        righe_previsioni.append({
            "mese": date_future[i],
            "materiale": materiale,
            "previsione_kg": previsioni[i],
            "metodo": metodi_selezionati[materiale],
        })

percorso_previsioni = (
    cartella_progetto
    / "previsioni"
    / "previsioni_future.csv"
)

with percorso_previsioni.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(
        file,
        fieldnames=["mese", "materiale", "previsione_kg", "metodo"],
    )
    scrittore.writeheader()
    scrittore.writerows(righe_previsioni)

print("File salvato:", percorso_previsioni.name)
print("Previsioni salvate:", len(righe_previsioni))
