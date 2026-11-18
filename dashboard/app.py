import streamlit as st
import csv
import random
from pathlib import Path
from math import ceil


def leggi_csv(cartella, nome_file):
    percorso = cartella_progetto / cartella / nome_file
    with percorso.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


st.set_page_config(
    page_title="Project Work — Domanda e scorte",
    layout="wide",
)

st.title("Domanda e scorte")

st.caption(
    "Project Work L-31 — Caso di studio Moretto Group. "
    "Dati e parametri sintetici per uso didattico."
)

cartella_progetto = Path(__file__).resolve().parent.parent
revisione_mesi = 1
mesi_simulazione = 12

nomi_materiali = {
    "alluminio": "Alluminio",
    "acciaio_carbonio": "Acciaio al carbonio",
    "acciaio_inox": "Acciaio inox",
    "rame": "Rame",
}

materiale_selezionato = st.selectbox(
    "Seleziona il materiale",
    options=list(nomi_materiali),
    format_func=nomi_materiali.get,
)

dati_storici = leggi_csv("dati", "domanda_sintetica.csv")
dati_previsioni = leggi_csv("previsioni", "previsioni_future.csv")
risultati_metodi = leggi_csv("risultati", "confronto_metodi.csv")
piano_iniziale = leggi_csv("scorte", "pianificazione_iniziale.csv")
dati_simulazione = leggi_csv("risultati", "simulazione_scorte.csv")

dati_materiale = []

for riga in dati_storici:
    if riga["materiale"] == materiale_selezionato:
        riga["consumo_kg"] = int(riga["consumo_kg"])
        riga["lead_time_mesi"] = int(riga["lead_time_mesi"])
        dati_materiale.append(riga)

previsioni_materiale = []

for riga in dati_previsioni:
    if riga["materiale"] == materiale_selezionato:
        riga["previsione_kg"] = float(riga["previsione_kg"])
        previsioni_materiale.append(riga)

confronto_materiale = []

for riga in risultati_metodi:
    if riga["materiale"] == materiale_selezionato:
        confronto_materiale.append({
            "Metodo": riga["metodo"],
            "MAE (kg)": round(float(riga["mae_kg"]), 2),
            "RMSE (kg)": round(float(riga["rmse_kg"]), 2),
        })

for riga in piano_iniziale:
    if riga["materiale"] == materiale_selezionato:
        piano_selezionato = riga

scorte_materiale = []

for riga in dati_simulazione:
    if riga["materiale"] == materiale_selezionato:
        scorte_materiale.append({
            "mese": riga["mese"],
            "Giacenza": float(riga["giacenza_fine_kg"]),
            "Ordini in arrivo": float(riga["pipeline_fine_kg"]),
            "Arretrati": float(riga["arretrati_fine_kg"]),
        })

lead_time_base = int(piano_selezionato["lead_time_mesi"])
giacenza_iniziale = float(piano_selezionato["giacenza_iniziale_kg"])
peso_coil = float(piano_selezionato["peso_coil_kg"])
sicurezza_base = float(piano_selezionato["scorta_sicurezza_kg"])

# La scorta ciclica è un riferimento teorico; la pipeline media deriva dai mesi simulati.
media_domanda_base = sum(
    riga["previsione_kg"]
    for riga in previsioni_materiale[:mesi_simulazione]
) / mesi_simulazione

ciclica_base = media_domanda_base * revisione_mesi / 2

pipeline_media_base = sum(
    riga["Ordini in arrivo"] for riga in scorte_materiale
) / len(scorte_materiale)

scheda_domanda, scheda_scorte, scheda_scenari = st.tabs(
    ["Domanda", "Scorte", "Scenari"]
)

with scheda_domanda:
    st.subheader("Storico e previsioni")

    st.caption(
        "36 mesi storici e 18 mesi previsti. "
        f"Metodo selezionato: {previsioni_materiale[0]['metodo']}."
    )

    storico_previsioni = []

    for riga in dati_materiale:
        storico_previsioni.append({
            "mese": riga["mese"],
            "Storico sintetico": riga["consumo_kg"],
            "Previsione": None,
        })

    for riga in previsioni_materiale:
        storico_previsioni.append({
            "mese": riga["mese"],
            "Storico sintetico": None,
            "Previsione": riga["previsione_kg"],
        })

    st.line_chart(
        storico_previsioni,
        x="mese",
        y=["Storico sintetico", "Previsione"],
        x_label="Mese",
        y_label="Consumo (kg)",
    )

    with st.expander("Mostra dettagli: metodi e dati"):
        st.subheader("Confronto dei metodi")

        st.caption(
            "Primi 24 mesi per il calcolo, successivi 12 per la valutazione. "
            "Si seleziona il metodo con MAE più basso."
        )

        st.dataframe(confronto_materiale, hide_index=True)

        st.write(
            "MAE: errore assoluto medio. "
            "RMSE: dà più peso agli errori grandi."
        )
        st.write(
            "Entrambi sono espressi in kg: "
            "valori inferiori indicano errori minori."
        )

        st.write("Consumi storici")
        st.dataframe(dati_materiale, hide_index=True)

        st.write("Previsioni future")
        st.dataframe(previsioni_materiale, hide_index=True)

with scheda_scorte:
    st.subheader("Primo ordine — novembre 2026")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Quantità da ordinare (kg)",
        round(float(piano_selezionato["quantita_ordine_kg"]), 2),
    )
    col2.metric(
        "Coil da ordinare",
        int(piano_selezionato["numero_coil"]),
    )
    col3.metric("Lead time (mesi)", lead_time_base)

    st.subheader("Scorte nel piano base")

    st.line_chart(
        scorte_materiale,
        x="mese",
        y=["Giacenza", "Ordini in arrivo", "Arretrati"],
        x_label="Mese",
        y_label="Quantità a fine mese (kg)",
    )

    with st.expander("Mostra dettagli: tipi di scorta e ipotesi"):
        st.dataframe([
            {
                "Tipo": "Ciclica media di riferimento",
                "Quantità (kg)": round(ciclica_base, 2),
            },
            {
                "Tipo": "Sicurezza",
                "Quantità (kg)": round(sicurezza_base, 2),
            },
            {
                "Tipo": "Pipeline media a fine mese",
                "Quantità (kg)": round(pipeline_media_base, 2),
            },
            {
                "Tipo": "Anticipata aggiuntiva nel piano base",
                "Quantità (kg)": 0.0,
            },
        ], hide_index=True)

        st.caption(
            "Valori con significati diversi: "
            "non vanno sommati come giacenza fisica."
        )

        st.write("Giacenza iniziale (kg):", giacenza_iniziale)
        st.write("Peso nominale del coil (kg):", peso_coil)
        st.write("Revisione degli ordini: ogni mese.")

        st.write(
            "Livello obiettivo (kg):",
            round(float(piano_selezionato["livello_obiettivo_kg"]), 2),
        )

        st.write(
            "Posizione delle scorte = "
            "giacenza + ordini in arrivo − arretrati."
        )

        st.write(
            "Ciclica: domanda media prevista nei primi 12 mesi × "
            "intervallo di revisione / 2. È un riferimento approssimato: "
            "non misura esattamente la giacenza, anche per effetto "
            "degli ordini in coil interi."
        )

        st.write(
            "Pipeline: ordini emessi e non ancora ricevuti; "
            "qui si mostra la media dei 12 valori a fine mese."
        )

        st.write(
            "La sicurezza deriva dagli errori previsionali storici, "
            "con obiettivo di servizio del 95% e ipotesi semplificative. "
            "Il 95% non è un risultato verificato."
        )

        st.write(
            "Nel piano base i consumi coincidono con le previsioni "
            "e gli arrivi sono puntuali."
        )

        st.dataframe(scorte_materiale, hide_index=True)

    if materiale_selezionato == "acciaio_carbonio":
        with st.expander("Mostra dettagli: scorta anticipata"):
            st.subheader("Scorta anticipata: confronto dedicato")

            dati_anticipo = leggi_csv(
                "risultati",
                "confronto_scorta_anticipata.csv",
            )

            confronto_anticipo = []

            for riga in dati_anticipo:
                confronto_anticipo.append({
                    "mese": riga["mese"],
                    "Piano base": float(riga["giacenza_base_kg"]),
                    "Arrivo anticipato": float(riga["giacenza_anticipata_kg"]),
                })

            st.caption(
                "Tre coil (30.000 kg) arrivano ad agosto 2027 "
                "anziché a settembre. L'ordine passa da luglio a giugno; "
                "gli acquisti totali restano invariati. "
                "È un'ipotesi didattica per avere materiale disponibile "
                "prima della ripresa autunnale. I tre coil sono una "
                "quantità scelta per il confronto, non un ottimo calcolato."
            )

            st.line_chart(
                confronto_anticipo,
                x="mese",
                y=["Piano base", "Arrivo anticipato"],
                x_label="Mese",
                y_label="Giacenza a fine mese (kg)",
            )

    else:
        st.caption(
            "Il caso di scorta anticipata è disponibile "
            "selezionando Acciaio al carbonio."
        )

with scheda_scenari:
    st.subheader("Modifica lo scenario")

    col1, col2 = st.columns(2)

    with col1:
        lead_time_scenario = st.number_input(
            "Lead time dello scenario (mesi)",
            min_value=1,
            max_value=6,
            value=lead_time_base,
            step=1,
            key=f"lead_time_{materiale_selezionato}",
        )

        trend_percentuale = st.number_input(
            "Trend aggiuntivo (% per mese)",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
            key=f"trend_{materiale_selezionato}",
        )

    with col2:
        stagionalita_percentuale = st.number_input(
            "Intensità della stagionalità aggiuntiva (%)",
            min_value=0,
            max_value=40,
            value=0,
            step=5,
            key=f"stagionalita_{materiale_selezionato}",
        )

        variabilita_percentuale = st.number_input(
            "Oscillazione massima dei consumi (%)",
            min_value=0,
            max_value=50,
            value=0,
            step=5,
            key=f"variabilita_{materiale_selezionato}",
        )

    st.caption(
        "Trend e stagionalità si aggiungono alla previsione base; "
        "l'oscillazione modifica i consumi simulati."
    )

    profilo_stagionale = {
        1: 0.0,
        2: 0.0,
        3: 0.0,
        4: 0.0,
        5: 0.0,
        6: 0.0,
        7: 0.0,
        8: -1.0,
        9: 0.5,
        10: 0.5,
        11: 0.5,
        12: -0.5,
    }

    # Si parte dalla previsione del metodo già scelto per questo materiale.
    previsioni_scenario = []

    for i, riga in enumerate(previsioni_materiale):
        numero_mese = int(riga["mese"][5:7])

        fattore_trend = 1 + (trend_percentuale / 100) * i

        fattore_stagionale = (
            1
            + (stagionalita_percentuale / 100)
            * profilo_stagionale[numero_mese]
        )

        domanda_attesa = (
            riga["previsione_kg"]
            * fattore_trend
            * fattore_stagionale
        )

        previsioni_scenario.append({
            "mese": riga["mese"],
            "Previsione base": riga["previsione_kg"],
            "Domanda attesa scenario": domanda_attesa,
        })

    copertura_scenario = lead_time_scenario + revisione_mesi
    # L'ultimo mese simulato conta anche come primo mese di copertura dell'ultimo ordine.
    mesi_necessari = mesi_simulazione + copertura_scenario - 1

    if len(previsioni_scenario) < mesi_necessari:
        st.error(
            "Le previsioni disponibili non coprono l'intera simulazione."
        )
        st.stop()

    domanda_copertura_scenario = 0.0

    for riga in previsioni_scenario[:copertura_scenario]:
        domanda_copertura_scenario += riga["Domanda attesa scenario"]

    copertura_base = lead_time_base + revisione_mesi

    # La scorta cambia con il tempo di consegna. Gli errori di riferimento restano quelli storici.
    sicurezza_scenario = (
        sicurezza_base
        * (copertura_scenario / copertura_base) ** 0.5
    )

    # Riaprendo lo scenario con gli stessi parametri si ritrovano le stesse oscillazioni.
    generatore = random.Random(42)
    saldo_scenario = giacenza_iniziale
    arrivi_scenario = [0.0] * len(previsioni_scenario)
    scorte_scenario = []

    for i in range(mesi_simulazione):
        mese = previsioni_scenario[i]["mese"]
        domanda_attesa = previsioni_scenario[i]["Domanda attesa scenario"]

        arrivi_mese = arrivi_scenario[i]
        saldo_scenario += arrivi_mese

        # Un saldo negativo indica arretrati. Gli arrivi del mese sono già nel saldo.
        pipeline_scenario = sum(arrivi_scenario[i + 1:])
        posizione_scorte = saldo_scenario + pipeline_scenario

        domanda_periodo = 0.0

        for riga in previsioni_scenario[i:i + copertura_scenario]:
            domanda_periodo += riga["Domanda attesa scenario"]

        obiettivo_mese = domanda_periodo + sicurezza_scenario
        fabbisogno = max(0, obiettivo_mese - posizione_scorte)

        coil_mese = ceil(fabbisogno / peso_coil)
        ordine_mese = coil_mese * peso_coil

        arrivi_scenario[i + lead_time_scenario] += ordine_mese
        pipeline_scenario += ordine_mese

        # Quando si decide quanto ordinare, il consumo del mese deve ancora essere simulato.
        oscillazione = generatore.uniform(
            -variabilita_percentuale / 100,
            variabilita_percentuale / 100,
        )

        domanda_simulata = domanda_attesa * (1 + oscillazione)
        saldo_scenario -= domanda_simulata

        scorte_scenario.append({
            "mese": mese,
            "Domanda attesa (kg)": domanda_attesa,
            "Consumo simulato (kg)": domanda_simulata,
            "Arrivi (kg)": arrivi_mese,
            "Coil ordinati": coil_mese,
            "Ordine emesso (kg)": ordine_mese,
            "Giacenza": max(0, saldo_scenario),
            "Ordini in arrivo": pipeline_scenario,
            "Arretrati": max(0, -saldo_scenario),
            "Livello obiettivo (kg)": obiettivo_mese,
        })

    primo_mese = scorte_scenario[0]
    mesi_con_arretrati = 0
    totale_ordini_scenario = 0.0
    giacenze_finali = []

    for riga in scorte_scenario:
        if riga["Arretrati"] > 0.01:
            mesi_con_arretrati += 1

        totale_ordini_scenario += riga["Ordine emesso (kg)"]
        giacenze_finali.append(riga["Giacenza"])

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Primo ordine (kg)",
        round(primo_mese["Ordine emesso (kg)"], 2),
    )
    col2.metric("Coil del primo ordine", primo_mese["Coil ordinati"])
    col3.metric("Mesi con arretrati", mesi_con_arretrati)

    st.subheader("Domanda attesa: base e scenario")

    st.line_chart(
        previsioni_scenario,
        x="mese",
        y=["Previsione base", "Domanda attesa scenario"],
        x_label="Mese",
        y_label="Consumo (kg)",
    )

    st.subheader("Scorte nello scenario")

    st.line_chart(
        scorte_scenario,
        x="mese",
        y=["Giacenza", "Ordini in arrivo", "Arretrati"],
        x_label="Mese",
        y_label="Quantità a fine mese (kg)",
    )

    ciclica_scenario = sum(
        riga["Domanda attesa scenario"]
        for riga in previsioni_scenario[:mesi_simulazione]
    ) / mesi_simulazione * revisione_mesi / 2

    pipeline_media_scenario = sum(
        riga["Ordini in arrivo"] for riga in scorte_scenario
    ) / mesi_simulazione

    with st.expander("Mostra dettagli: confronto scorte e ipotesi"):
        st.dataframe([
            {
                "Indicatore (kg)": "Ciclica media di riferimento",
                "Base": round(ciclica_base, 2),
                "Scenario": round(ciclica_scenario, 2),
            },
            {
                "Indicatore (kg)": "Sicurezza",
                "Base": round(sicurezza_base, 2),
                "Scenario": round(sicurezza_scenario, 2),
            },
            {
                "Indicatore (kg)": "Pipeline media a fine mese",
                "Base": round(pipeline_media_base, 2),
                "Scenario": round(pipeline_media_scenario, 2),
            },
        ], hide_index=True)

        st.caption(
            "La scorta anticipata è analizzata nel confronto dedicato "
            "della scheda Scorte."
        )

        st.write("Periodo da coprire (mesi):", copertura_scenario)

        st.write(
            "Domanda attesa nel periodo iniziale (kg):",
            round(domanda_copertura_scenario, 2),
        )

        st.write(
            "Livello obiettivo iniziale (kg):",
            round(primo_mese["Livello obiettivo (kg)"], 2),
        )

        st.write(
            "Giacenza minima a fine mese (kg):",
            round(min(giacenze_finali), 2),
        )

        st.write(
            "Quantità ordinata nei 12 mesi (kg):",
            round(totale_ordini_scenario, 2),
        )

        st.write(
            "Gli ordini totali comprendono consegne successive "
            "alla fine della simulazione."
        )

        st.write(
            "Il trend è lineare: con 1%, il fattore è 1 nel primo mese, "
            "1,01 nel secondo, 1,02 nel terzo. Con stagionalità 20%, "
            "agosto diminuisce del 20%, settembre–novembre aumentano "
            "del 10% e dicembre diminuisce del 10%."
        )

        st.write(
            "Con oscillazione 20%, i consumi variano uniformemente "
            "tra l'80% e il 120% della domanda attesa. "
            "Il seme casuale fisso rende la prova ripetibile."
        )

        st.write(
            "La sicurezza usa gli errori storici e si adegua al lead time. "
            "Non viene ricalibrata su trend, stagionalità "
            "o oscillazione aggiuntivi."
        )

        st.write(
            "Stessa giacenza iniziale del piano base, nessun ordine "
            "preesistente o arretrato iniziale. Arrivi puntuali e revisione "
            "a inizio mese; consumi dopo l'ordine. Una singola simulazione "
            "non dimostra il raggiungimento del servizio del 95%."
        )

        st.dataframe(scorte_scenario, hide_index=True)
