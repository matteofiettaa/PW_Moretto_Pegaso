import csv
from pathlib import Path
from statistics import NormalDist, linear_regression, stdev
from math import ceil

# Revisione mensile e pesi nominali fissi: sono ipotesi del modello.
revisione_mesi = 1
livello_servizio = 0.95

peso_coil_kg = {
    "alluminio": 5000,
    "acciaio_carbonio": 10000,
    "acciaio_inox": 2000,
    "rame": 500,
}

print("Revisione ogni:", revisione_mesi, "mese")
print("Livello di servizio obiettivo:", livello_servizio * 100, "%")
print("Pesi nominali dei coil in kg:", peso_coil_kg)

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

lead_time_mesi = {}

for riga in dati_storici:
    materiale = riga["materiale"]
    lead_time_mesi[materiale] = int(riga["lead_time_mesi"])

print("Previsioni caricate:", len(dati_previsti))
print("Lead time in mesi:", lead_time_mesi)

previsioni_per_materiale = {}
domanda_copertura_kg = {}

for materiale in peso_coil_kg:
    previsioni = []

    for riga in dati_previsti:
        if riga["materiale"] == materiale:
            previsioni.append(float(riga["previsione_kg"]))

    previsioni_per_materiale[materiale] = previsioni

    # Serve materiale fino all'arrivo della fornitura che si potrà ordinare alla prossima revisione.
    copertura_mesi = lead_time_mesi[materiale] + revisione_mesi

    if len(previsioni) < copertura_mesi:
        raise ValueError(f"Previsioni insufficienti per {materiale}")

    domanda_copertura = sum(previsioni[:copertura_mesi])
    domanda_copertura_kg[materiale] = domanda_copertura

    print(
        materiale,
        "- copertura:", copertura_mesi,
        "mesi - domanda prevista:", round(domanda_copertura, 2),
        "kg",
    )

# Il modello punta al 95% di cicli senza carenze. È un obiettivo teorico.
coefficiente_sicurezza = NormalDist().inv_cdf(livello_servizio)

print(
    "Coefficiente di sicurezza:",
    round(coefficiente_sicurezza, 3),
)

metodi_scorte = {}

for riga in dati_previsti:
    metodi_scorte[riga["materiale"]] = riga["metodo"]

# Si riusano i 12 mesi su cui è stato scelto il metodo. Per stimare la scorta
# si raccoglie un nuovo errore per ogni previsione a un mese.
errori_mensili_kg = {}

for materiale in peso_coil_kg:
    storico = []

    for riga in dati_storici:
        if riga["materiale"] == materiale:
            storico.append(int(riga["consumo_kg"]))

    metodo = metodi_scorte[materiale]
    errori = []

    for i in range(24, len(storico)):
        # Quando si fa la previsione, l'ultimo consumo noto è quello del mese precedente.
        passato = storico[:i]

        if metodo == "media":
            previsione = sum(passato) / len(passato)

        elif metodo == "cmm3":
            previsione = sum(passato[-3:]) / 3

        elif metodo == "stagionale":
            previsione = passato[-12]

        elif metodo == "trend":
            pendenza, intercetta = linear_regression(
                range(len(passato)), passato
            )
            previsione = intercetta + pendenza * len(passato)

        else:
            raise ValueError(f"Metodo non riconosciuto: {metodo}")

        errore = storico[i] - previsione
        errori.append(errore)

    errori_mensili_kg[materiale] = errori

    print(
        materiale,
        "- errori mensili calcolati:", len(errori),
    )

errore_medio_kg = {}
deviazione_errori_kg = {}

for materiale, errori in errori_mensili_kg.items():
    media_errori = sum(errori) / len(errori)
    # La media segnala eventuali errori sistematici. Il margine usa la deviazione standard campionaria.
    deviazione = stdev(errori)

    errore_medio_kg[materiale] = media_errori
    deviazione_errori_kg[materiale] = deviazione

    print(
        materiale,
        "- errore medio:", round(media_errori, 2),
        "- deviazione standard:", round(deviazione, 2),
        "kg",
    )

# La varianza cresce con i mesi di copertura se gli errori mensili sono
# indipendenti e hanno varianza costante. Per il margine al 95% si assume
# che l'errore complessivo sia circa normale, con media zero.
scorta_sicurezza_kg = {}

for materiale in peso_coil_kg:
    copertura_mesi = lead_time_mesi[materiale] + revisione_mesi
    deviazione = deviazione_errori_kg[materiale]

    scorta_sicurezza = (
        coefficiente_sicurezza
        * deviazione
        * copertura_mesi ** 0.5
    )

    scorta_sicurezza_kg[materiale] = scorta_sicurezza

    print(
        materiale,
        "- scorta di sicurezza:",
        round(scorta_sicurezza, 2),
        "kg",
    )

livello_obiettivo_kg = {}

for materiale in peso_coil_kg:
    livello_obiettivo = (
        domanda_copertura_kg[materiale]
        + scorta_sicurezza_kg[materiale]
    )

    livello_obiettivo_kg[materiale] = livello_obiettivo

    print(
        materiale,
        "- livello obiettivo:",
        round(livello_obiettivo, 2),
        "kg",
    )

giacenza_iniziale_kg = {
    "alluminio": 150000,
    "acciaio_carbonio": 450000,
    "acciaio_inox": 15000,
    "rame": 13000,
}

ordini_in_arrivo_kg = {}
arretrati_kg = {}

for materiale in peso_coil_kg:
    ordini_in_arrivo_kg[materiale] = 0
    arretrati_kg[materiale] = 0

ordini_proposti = {}

for materiale in peso_coil_kg:
    posizione_scorte = (
        giacenza_iniziale_kg[materiale]
        + ordini_in_arrivo_kg[materiale]
        - arretrati_kg[materiale]
    )

    fabbisogno = max(
        0,
        livello_obiettivo_kg[materiale] - posizione_scorte,
    )

    # L'ordine deve coprire il fabbisogno con un numero intero di coil.
    numero_coil = ceil(fabbisogno / peso_coil_kg[materiale])
    quantita_ordine = numero_coil * peso_coil_kg[materiale]

    ordini_proposti[materiale] = {
        "numero_coil": numero_coil,
        "quantita_kg": quantita_ordine,
    }

    print(
        materiale,
        "- coil da ordinare:", numero_coil,
        "- quantità:", quantita_ordine,
        "kg",
    )

righe_piano = []

for materiale in peso_coil_kg:
    righe_piano.append({
        "materiale": materiale,
        "lead_time_mesi": lead_time_mesi[materiale],
        "giacenza_iniziale_kg": giacenza_iniziale_kg[materiale],
        "scorta_sicurezza_kg": scorta_sicurezza_kg[materiale],
        "livello_obiettivo_kg": livello_obiettivo_kg[materiale],
        "peso_coil_kg": peso_coil_kg[materiale],
        "numero_coil": ordini_proposti[materiale]["numero_coil"],
        "quantita_ordine_kg": ordini_proposti[materiale]["quantita_kg"],
    })

percorso_piano = (
    cartella_progetto
    / "scorte"
    / "pianificazione_iniziale.csv"
)

campi = [
    "materiale",
    "lead_time_mesi",
    "giacenza_iniziale_kg",
    "scorta_sicurezza_kg",
    "livello_obiettivo_kg",
    "peso_coil_kg",
    "numero_coil",
    "quantita_ordine_kg",
]

with percorso_piano.open("w", newline="", encoding="utf-8") as file:
    scrittore = csv.DictWriter(file, fieldnames=campi)
    scrittore.writeheader()
    scrittore.writerows(righe_piano)

print("Piano salvato:", percorso_piano.name)
print("Materiali pianificati:", len(righe_piano))

# La scorta ciclica è una stima. L'arrotondamento a bobine intere può lasciare più materiale in magazzino.
scorta_ciclica_media_kg = {}

for materiale, previsioni in previsioni_per_materiale.items():
    domanda_annuale = previsioni[:12]
    domanda_media = sum(domanda_annuale) / len(domanda_annuale)

    scorta_ciclica = domanda_media * revisione_mesi / 2
    scorta_ciclica_media_kg[materiale] = scorta_ciclica

    print(
        materiale,
        "- scorta ciclica media di riferimento:",
        round(scorta_ciclica, 2),
        "kg",
    )
