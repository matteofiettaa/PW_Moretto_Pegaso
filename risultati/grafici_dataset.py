import matplotlib.pyplot as plt
import csv
from pathlib import Path

cartella_progetto = Path(__file__).resolve().parent.parent
percorso_csv = cartella_progetto / "dati" / "domanda_sintetica.csv"

with percorso_csv.open("r", newline="", encoding="utf-8") as file:
    lettore = csv.DictReader(file)
    dati = list(lettore)

print("Righe lette dal CSV:", len(dati))

materiali = {
    "alluminio": "Alluminio",
    "acciaio_carbonio": "Acciaio al carbonio",
    "acciaio_inox": "Acciaio inox",
    "rame": "Rame",
}

for materiale, nome in materiali.items():
    mesi = []
    consumi = []

    for riga in dati:
        if riga["materiale"] == materiale:
            mesi.append(riga["mese"])
            consumi.append(int(riga["consumo_kg"]))

    plt.figure(figsize=(10, 5))
    plt.plot(mesi, consumi, marker="o")

    plt.title(f"{nome} — consumi mensili sintetici")
    plt.xlabel("Mese")
    plt.ylabel("Consumo (kg)")
    plt.xticks(mesi[::6], rotation=45)
    plt.ylim(0, max(consumi) * 1.1)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    percorso_grafico = (
        cartella_progetto
        / "risultati"
        / f"grafico_{materiale}.png"
    )

    plt.savefig(percorso_grafico, dpi=150)
    plt.close()

    print("Grafico salvato:", percorso_grafico.name)
