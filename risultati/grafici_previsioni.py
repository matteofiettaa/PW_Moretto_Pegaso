import csv
from pathlib import Path

import matplotlib.pyplot as plt

cartella_progetto = Path(__file__).resolve().parent.parent

percorso_storico = (
    cartella_progetto / "dati" / "domanda_sintetica.csv"
)

percorso_previsioni = (
    cartella_progetto / "previsioni" / "previsioni_future.csv"
)

with percorso_storico.open("r", newline="", encoding="utf-8") as file:
    dati_storici = list(csv.DictReader(file))

with percorso_previsioni.open("r", newline="", encoding="utf-8") as file:
    dati_previsti = list(csv.DictReader(file))

print("Righe storiche:", len(dati_storici))
print("Righe previsionali:", len(dati_previsti))

materiali = {
    "alluminio": "Alluminio",
    "acciaio_carbonio": "Acciaio al carbonio",
    "acciaio_inox": "Acciaio inox",
    "rame": "Rame",
}

for materiale, nome in materiali.items():
    mesi_storici = []
    consumi_storici = []
    mesi_previsti = []
    consumi_previsti = []

    for riga in dati_storici:
        if riga["materiale"] == materiale:
            mesi_storici.append(riga["mese"])
            consumi_storici.append(float(riga["consumo_kg"]))

    for riga in dati_previsti:
        if riga["materiale"] == materiale:
            mesi_previsti.append(riga["mese"])
            consumi_previsti.append(float(riga["previsione_kg"]))

    plt.figure(figsize=(12, 5))

    plt.plot(
        mesi_storici,
        consumi_storici,
        marker="o",
        label="Storico sintetico",
    )

    # La linea tratteggiata parte dall'ultimo consumo osservato per raccordarsi allo storico.
    plt.plot(
        [mesi_storici[-1]] + mesi_previsti,
        [consumi_storici[-1]] + consumi_previsti,
        marker="o",
        linestyle="--",
        label="Previsione",
    )

    plt.axvline(
        mesi_storici[-1],
        color="gray",
        linestyle=":",
        label="Fine storico",
    )

    mesi_totali = mesi_storici + mesi_previsti

    plt.title(f"{nome} — storico sintetico e previsione")
    plt.xlabel("Mese")
    plt.ylabel("Consumo (kg)")
    plt.xticks(mesi_totali[::6], rotation=45)
    massimo = max(consumi_storici + consumi_previsti)
    plt.ylim(0, massimo * 1.1)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    percorso_grafico = (
        cartella_progetto
        / "risultati"
        / f"storico_previsione_{materiale}.png"
    )

    plt.savefig(percorso_grafico, dpi=150)
    plt.close()

    print("Grafico salvato:", percorso_grafico.name)
