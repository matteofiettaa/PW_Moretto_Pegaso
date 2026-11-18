import csv
from pathlib import Path
from statistics import linear_regression


def calcola_mae(osservati, previsti):
    # Media degli errori assoluti, espressa nella stessa unità dei consumi (kg).
    errori = []

    for i in range(len(osservati)):
        errore = abs(osservati[i] - previsti[i])
        errori.append(errore)

    return sum(errori) / len(errori)


def calcola_rmse(osservati, previsti):
    # Il quadrato dà maggiore peso agli errori più grandi; la radice riporta ai kg.
    errori_quadrati = []

    for i in range(len(osservati)):
        errore = osservati[i] - previsti[i]
        errori_quadrati.append(errore ** 2)

    media_quadrati = sum(errori_quadrati) / len(errori_quadrati)
    return media_quadrati ** 0.5


cartella_progetto = Path(__file__).resolve().parent.parent
percorso_csv = cartella_progetto / "dati" / "domanda_sintetica.csv"

with percorso_csv.open("r", newline="", encoding="utf-8") as file:
    dati = list(csv.DictReader(file))

materiali = [
    "alluminio",
    "acciaio_carbonio",
    "acciaio_inox",
    "rame",
]

dati_training = {}
dati_valutazione = {}

for materiale in materiali:
    serie = []

    for riga in dati:
        if riga["materiale"] == materiale:
            serie.append(int(riga["consumo_kg"]))

    # Tutte le previsioni del confronto partono dalla fine del 24° mese.
    # Nei 12 mesi successivi si confrontano le previsioni con i consumi osservati.
    dati_training[materiale] = serie[:24]
    dati_valutazione[materiale] = serie[24:]


previsioni_media = {}
previsioni_stagionali = {}
previsioni_cmm3 = {}
previsioni_trend = {}

for materiale in materiali:
    storico = dati_training[materiale]

    media = sum(storico) / len(storico)
    previsioni_media[materiale] = [media] * 12

    # Stagionale naïve: ripete i consumi degli stessi mesi dell'ultimo anno.
    previsioni_stagionali[materiale] = storico[-12:]

    # Nel confronto la media degli ultimi tre mesi si calcola una sola volta.
    ultimi_tre_mesi = storico[-3:]
    cmm3 = sum(ultimi_tre_mesi) / 3
    previsioni_cmm3[materiale] = [cmm3] * 12

    mesi_training = range(len(storico))
    pendenza, intercetta = linear_regression(mesi_training, storico)

    previsioni_trend[materiale] = []

    for mese in range(len(storico), len(storico) + 12):
        previsione = intercetta + pendenza * mese
        previsioni_trend[materiale].append(previsione)


metodi = {
    "media": previsioni_media,
    "stagionale": previsioni_stagionali,
    "cmm3": previsioni_cmm3,
    "trend": previsioni_trend,
}

risultati = []

for materiale in materiali:
    osservati = dati_valutazione[materiale]

    for nome_metodo, previsioni in metodi.items():
        previsti = previsioni[materiale]

        mae = calcola_mae(osservati, previsti)
        rmse = calcola_rmse(osservati, previsti)

        risultati.append({
            "materiale": materiale,
            "metodo": nome_metodo,
            "mae_kg": mae,
            "rmse_kg": rmse,
        })

        print(
            materiale,
            "-", nome_metodo,
            "- MAE:", round(mae, 2),
            "- RMSE:", round(rmse, 2),
            "kg",
        )


percorso_risultati = (
    cartella_progetto
    / "risultati"
    / "confronto_metodi.csv"
)

with percorso_risultati.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(
        file,
        fieldnames=["materiale", "metodo", "mae_kg", "rmse_kg"],
    )
    scrittore.writeheader()
    scrittore.writerows(risultati)

print("Risultati salvati:", percorso_risultati.name)
print("Combinazioni salvate:", len(risultati))

# La scelta usa il MAE non arrotondato; gli arrotondamenti servono solo alla stampa.
metodi_migliori = {}

for materiale in materiali:
    migliore = None

    for risultato in risultati:
        if risultato["materiale"] == materiale:
            if migliore is None or risultato["mae_kg"] < migliore["mae_kg"]:
                migliore = risultato

    metodi_migliori[materiale] = migliore["metodo"]

    print(
        materiale,
        "- metodo selezionato:", migliore["metodo"],
        "- MAE:", round(migliore["mae_kg"], 2),
        "kg",
    )

percorso_metodi = (
    cartella_progetto
    / "risultati"
    / "metodi_selezionati.csv"
)

with percorso_metodi.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(
        file,
        fieldnames=["materiale", "metodo"],
    )
    scrittore.writeheader()

    for materiale, metodo in metodi_migliori.items():
        scrittore.writerow({
            "materiale": materiale,
            "metodo": metodo,
        })

print("Metodi salvati:", percorso_metodi.name)
