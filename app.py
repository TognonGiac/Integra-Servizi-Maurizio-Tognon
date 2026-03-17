import streamlit as st
import io
import os
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter

# Importiamo la tua "mappa" dal file coordinate.py
from coordinate import coordinate_BATTERIE_ACCUMULO_HUAWEI, coordinate_TESLA, coordinate_HUAWEI_MONOFASE, coordinate_SUNGROW_MONOFASE

# --- FUNZIONE MAGICA PER COMPILARE IL PDF ---
def compila_pdf(pdf_vuoto_path, dati, coordinate_mappa, output_path):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Organizza i testi pagina per pagina
    pagine_da_scrivere = {}
    for chiave, valore in dati.items():
        if chiave in coordinate_mappa:
            coord = coordinate_mappa[chiave]
            if len(coord) == 3:
                pagina, x, y = coord
            else:
                pagina, x, y = 0, coord[0], coord[1]
            
            if pagina not in pagine_da_scrivere:
                pagine_da_scrivere[pagina] = []
            pagine_da_scrivere[pagina].append((x, y, str(valore), chiave))

    # Disegna i testi sul foglio trasparente
    max_page = max(pagine_da_scrivere.keys()) if pagine_da_scrivere else 0
    for p in range(max_page + 1):
        if p in pagine_da_scrivere:
            for x, y, testo, chiave in pagine_da_scrivere[p]:
                
                # --- LOGICA INTELLIGENTE PER TESTI E FONT ---
                if chiave == "chiavi in mano": 
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(x, y, testo)
                     
                elif chiave == "note":
                    # Se sono le note, usa un font normale e vai a capo da solo!
                    c.setFont("Helvetica", 12) 
                    # Taglia il testo ogni 90 caratteri (larghezza perfetta per un A4)
                    righe_note = textwrap.wrap(testo, width=85) 
                    
                    y_corrente = y # Partiamo dalla Y originale
                    for riga in righe_note:
                        c.drawString(x, y_corrente, riga)
                        y_corrente -= 15 # Scende di 15 "pixel" per la riga successiva
                        
                else:
                    # Per tutti gli altri campi normali
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x, y, testo)
                    
        c.showPage()
    
    c.save()
    packet.seek(0)

    # Unisce il foglio trasparente al PDF di tuo zio
    pdf_trasparente = PdfReader(packet)
    pdf_originale = PdfReader(pdf_vuoto_path)
    pdf_writer = PdfWriter()

    for i in range(len(pdf_originale.pages)):
        pagina_sfondo = pdf_originale.pages[i]
        if i < len(pdf_trasparente.pages):
            pagina_sfondo.merge_page(pdf_trasparente.pages[i])
        pdf_writer.add_page(pagina_sfondo)

    with open(output_path, "wb") as f:
        pdf_writer.write(f)

# --- INTERFACCIA SITO WEB ---
st.set_page_config(page_title="Generatore Preventivi", page_icon="⚡")
st.title("⚡ Generatore Preventivi - Integra Servizi")

st.subheader("1. Seleziona il modello")
tipo_preventivo = st.selectbox(
    "Quale preventivo devi generare?",
    ["Scegli...", "BATTERIE ACCUMOLO HUAWEI", "HUAWEI MONOFASE", "SUNGROW MONOFASE", "TESLA"]
)

if tipo_preventivo == "BATTERIE ACCUMOLO HUAWEI":
    
    data_offerta = st.text_input("Data dell'offerta (es. 04/03/2026):")
    referente = st.text_input("Referente commerciale:", value="Tognon Maurizio")
    telefono = st.text_input("Telefono referente:", value="348 581 3791")
    nome_cognome = st.text_input("Nome e Cognome del cliente:")
    indirizzo_residenza = st.text_input("Indirizzo di residenza:")
    telefono_cliente=st.text_input("Telefono cliente:")
    email_cliente=st.text_input("Email cliente:")
    indirizzo_se_diverso=st.text_input("Indirizzo installazione se diverso dalla residenza:")
    
    st.markdown("---")

    capacita_accumulo = st.number_input("Capacità accumulo totale in kWh:", min_value=0.0, value=None, step=0.5)
    numero_sistemi = st.number_input("Numero di sistemi di accumulo:", min_value=1, value=None, step=1)
    
    st.markdown("---")

    prezzo_base = st.number_input("Prezzo senza IVA €:", min_value=0.0, value=None, step=100.00)
    totale_finale = st.number_input("Totale Chiavi in Mano (IVA Inclusa) €:", min_value=0.0, value=None, step=100.00)
    
    if st.button("Genera Preventivo PDF"):

        kwh_formattato = f"{capacita_accumulo:.2f}".replace('.', ',') if capacita_accumulo is not None else ""
        prezzo_formattato = f"{prezzo_base:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " €" if prezzo_base is not None else ""
        totale_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if totale_finale is not None else ""
        totale_simbolo_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " €" if totale_finale is not None else ""
        sistemi_formattato = str(numero_sistemi) if numero_sistemi is not None else ""
            # 1. Raccogliamo le risposte di tuo zio in un dizionario
            # ATTENZIONE: I nomi qui a sinistra ("data", "cliente", ecc.) DEVONO
            # essere identici a quelli che hai usato in coordinate.py!
        dati_inseriti = {
            "data": data_offerta,
            "referente": referente,
            "telefono": telefono,
            "cliente": nome_cognome,
            "indirizzo": indirizzo_residenza,
            "telefono_cliente": telefono_cliente,
            "email_cliente": email_cliente,
            "indirizzo_installazione": indirizzo_se_diverso,
            "n_sistemi": sistemi_formattato,
            "kwh_totali": kwh_formattato,
            "prezzo": prezzo_formattato,
            "piu' iva": totale_formattato,
            "chiavi in mano": totale_simbolo_formattato
        }
            
        nome_modello = tipo_preventivo.replace(" ", "_")
        nome_cliente = nome_cognome.replace(" ", "_") if nome_cognome else ""
        
        nome_file_finale = f"{nome_modello}_{nome_cliente}.pdf"
        
        cartella_output = "cartella output"
        if not os.path.exists(cartella_output):
            os.makedirs(cartella_output) # Crea la cartella automaticamente!
                
        pdf_input = "assets/BATTERIE ACCUMULO HUAWEI.pdf"
        pdf_output_path = f"{cartella_output}/{nome_file_finale}"
        

        # Generiamo il PDF!
        try:
            compila_pdf(pdf_input, dati_inseriti, coordinate_BATTERIE_ACCUMULO_HUAWEI, pdf_output_path)
            st.success(f"✅ Preventivo generato con successo")
                
            # Creiamo il bottone per far scaricare il PDF a tuo zio
            with open(pdf_output_path, "rb") as pdf_file:
                st.download_button(
                    label="⬇️ SCARICA IL PREVENTIVO",
                    data=pdf_file,
                    file_name=f"Preventivo_Integra_{nome_cognome.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Errore durante la creazione del PDF. Assicurati che il file '{pdf_input}' esista! Dettaglio: {e}")

elif tipo_preventivo == "TESLA":
    
    data_offerta = st.text_input("Data dell'offerta (es. 04/03/2026):")
    referente = st.text_input("Referente commerciale:", value="Tognon Maurizio")
    telefono = st.text_input("Telefono referente:", value="348 581 3791")
        
    nome_cognome = st.text_input("Nome e Cognome del cliente:")
    indirizzo_residenza = st.text_input("Indirizzo di residenza:")
    telefono_cliente = st.text_input("Telefono del cliente:")
    email_cliente = st.text_input("E-mail del cliente:")
    indirizzo_installazione = st.text_input("Indirizzo installazione (se diverso dalla residenza):")
        
    st.markdown("---")

    potenza_nominale = st.number_input("Potenza Nominale (kW):", min_value=0.0, value=None, step=0.5)
    capacita_accumulo = st.number_input("Capacità accumulo totale in kWh:", min_value=0.0, value=None, step=0.5)
    moduli = st.number_input("Numero di moduli:", min_value=1, value=None, step=1)
    powerwall = st.number_input("Numero di Powerwall:", min_value=1, value=None, step=1)
    
    st.markdown("---")

    prezzo_base = st.number_input("Prezzo senza IVA €:", min_value=0.0, value=None, step=100.00)
    totale_finale = st.number_input("Totale Chiavi in Mano (IVA Inclusa) €:", min_value=0.0, value=None, step=100.00)
    note_aggiuntive = st.text_area("Note aggiuntive:")
                
    if st.button("Genera Preventivo TESLA"):
            
        # Formattiamo i numeri in modo sicuro
        potenza_formattata = f"{potenza_nominale:.2f}".replace('.', ',') if potenza_nominale is not None else ""
        kwh_formattato = f"{capacita_accumulo:.2f}".replace('.', ',') if capacita_accumulo is not None else ""
        prezzo_formattato = f"{prezzo_base:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " €" if prezzo_base is not None else ""
        totale_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if totale_finale is not None else ""
        totale_simbolo_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " €" if totale_finale is not None else ""
        moduli_formattato = str(moduli) if moduli is not None else ""
        powerwall_formattato = str(powerwall) if powerwall is not None else ""
            
        dati_inseriti = {
            "data": data_offerta,
            "referente": referente,
            "telefono": telefono,
            "cliente": nome_cognome,
            "indirizzo": indirizzo_residenza,
            "telefono_cliente": telefono_cliente,
            "email_cliente": email_cliente,
            "indirizzo_installazione": indirizzo_installazione,
                
            # Variabili specifiche Tesla
            "potenza_nominale": potenza_formattata,
            "kwh_totali": kwh_formattato,
            "moduli": moduli_formattato,
            "powerwall": powerwall_formattato,
                
            "prezzo": prezzo_formattato,
            "piu' iva": totale_formattato,
            "chiavi in mano": totale_simbolo_formattato,
            "note": note_aggiuntive
        }
                
        nome_modello = tipo_preventivo.replace(" ", "_")
        nome_cliente = nome_cognome.replace(" ", "_") if nome_cognome else ""
        nome_file_finale = f"{nome_modello}_{nome_cliente}.pdf"
        
        cartella_output = "cartella output"
        if not os.path.exists(cartella_output):
            os.makedirs(cartella_output)
                
        # NOME DEL FILE VUOTO (controlla che sia questo in assets!)
        pdf_input = "assets/MASTER TESLA.pdf" 
        pdf_output_path = f"{cartella_output}/{nome_file_finale}"
            
        try:
            compila_pdf(pdf_input, dati_inseriti, coordinate_TESLA, pdf_output_path)
            st.success("✅ Preventivo TESLA generato con successo!")
                
            with open(pdf_output_path, "rb") as pdf_file:
                st.download_button(
                    label="⬇️ SCARICA IL PREVENTIVO TESLA",
                    data=pdf_file,
                    file_name=nome_file_finale,
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Errore durante la creazione del PDF. Assicurati che il file '{pdf_input}' esista! Dettaglio: {e}")

elif tipo_preventivo == "HUAWEI MONOFASE":
    
    data_offerta = st.text_input("Data dell'offerta (es. 04/03/2026):")
    referente = st.text_input("Referente commerciale:", value="Tognon Maurizio")
    telefono = st.text_input("Telefono referente:", value="348 581 3791")
        
    nome_cognome = st.text_input("Nome e Cognome del cliente:")
    indirizzo_residenza = st.text_input("Indirizzo di residenza:")
    telefono_cliente = st.text_input("Telefono del cliente:")
    email_cliente = st.text_input("E-mail del cliente:")
    indirizzo_installazione = st.text_input("Indirizzo installazione (se diverso dalla residenza):")
    
    st.markdown("---")

    potenza_nominale = st.number_input("Potenza Nominale (kW):", min_value=0.0, value=None, step=0.5)
    capacita_accumulo = st.number_input("Capacità accumulo totale in kWh:", min_value=0.0, value=None, step=0.5)
    moduli = st.number_input("Numero di moduli:", min_value=1, value=None, step=1)
    sistemi_accumulo = st.number_input("Numero di sistemi di accumulo:", min_value=1, value=None, step=1)
    
    st.markdown("---")

    prezzo_base = st.number_input("Prezzo senza IVA €:", min_value=0.0, value=None, step=100.00)
    totale_finale = st.number_input("Totale Chiavi in Mano (IVA Inclusa) €:", min_value=0.0, value=None, step=100.00)
    
    note_aggiuntive = st.text_area("Note aggiuntive:")
                
    if st.button("Genera Preventivo HUAWEI MONOFASE"):
            
        # Formattiamo i numeri in modo sicuro
        potenza_formattata = f"{potenza_nominale:.2f}".replace('.', ',') if potenza_nominale is not None else ""
        kwh_formattato = f"{capacita_accumulo:.2f}".replace('.', ',') if capacita_accumulo is not None else ""
        prezzo_formattato = f"{prezzo_base:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_base is not None else ""
        totale_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if totale_finale is not None else ""
        totale_simbolo_formattato = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')+" €" if totale_finale is not None else ""
        moduli_formattato = str(moduli) if moduli is not None else ""
        sistemi_formattato = str(sistemi_accumulo) if sistemi_accumulo is not None else ""
            
        dati_inseriti = {
            "data": data_offerta,
            "referente": referente,
            "telefono": telefono,
            "cliente": nome_cognome,
            "indirizzo": indirizzo_residenza,
            "telefono_cliente": telefono_cliente,
            "email_cliente": email_cliente,
            "indirizzo_installazione": indirizzo_installazione,
                
            # Variabili specifiche Huawei Monofase
            "potenza_nominale": potenza_formattata,
            "kwh_totali": kwh_formattato,
            "moduli": moduli_formattato,
            "sistemi di accumulo": sistemi_formattato,
                
            "prezzo": prezzo_formattato,
            "piu' iva": totale_formattato,
            "chiavi in mano": totale_simbolo_formattato,
            "note": note_aggiuntive
        }
                
        nome_modello = tipo_preventivo.replace(" ", "_")
        nome_cliente = nome_cognome.replace(" ", "_") if nome_cognome else ""
        nome_file_finale = f"MASTER_{nome_modello}_{nome_cliente}.pdf"
        
        cartella_output = "cartella output"
        if not os.path.exists(cartella_output):
            os.makedirs(cartella_output)
                
        # NOME DEL FILE VUOTO (controlla che si chiami esattamente così nella cartella assets!)
        pdf_input = "assets/MASTER HUAWEI MONOFASE.pdf" 
        pdf_output_path = f"{cartella_output}/{nome_file_finale}"
            
        try:
            compila_pdf(pdf_input, dati_inseriti, coordinate_HUAWEI_MONOFASE, pdf_output_path)
            st.success("✅ Preventivo HUAWEI MONOFASE generato con successo!")
                
            with open(pdf_output_path, "rb") as pdf_file:
                st.download_button(
                    label="⬇️ SCARICA IL PREVENTIVO HUAWEI MONOFASE",
                    data=pdf_file,
                    file_name=nome_file_finale,
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Errore durante la creazione del PDF. Assicurati che il file '{pdf_input}' esista! Dettaglio: {e}")

elif tipo_preventivo == "SUNGROW MONOFASE":
    
    data_offerta = st.text_input("Data dell'offerta (es. 04/03/2026):")
    referente = st.text_input("Referente commerciale:", value="Tognon Maurizio")
    telefono = st.text_input("Telefono referente:", value="348 581 3791")
        
    nome_cognome = st.text_input("Nome e Cognome del cliente:")
    indirizzo_residenza = st.text_input("Indirizzo di residenza:")
    telefono_cliente = st.text_input("Telefono del cliente:")
    email_cliente = st.text_input("E-mail del cliente:")
    indirizzo_installazione = st.text_input("Indirizzo installazione (se diverso dalla residenza):")
    
    st.markdown("---")

    potenza_nominale = st.number_input("Potenza Nominale (kW):", min_value=0.0, value=None, step=0.5)
    capacita_accumulo = st.number_input("Capacità accumulo totale in kWh:", min_value=0.0, value=None, step=0.5)
    moduli = st.number_input("Numero di moduli:", min_value=1, value=None, step=1)
    sistemi_accumulo = st.number_input("Numero di sistemi di accumulo:", min_value=1, value=None, step=1)

    prezzo_base = st.number_input("Prezzo Base senza IVA €:", min_value=0.0, value=None, step=100.00)
    prezzo_finale =st.number_input("Prezzo finale con IVA €:", min_value=0.0, value=None, step=100.00)
    
    st.markdown("---")
    st.markdown("**Eventuali Integrazioni**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**TIGO**")
        n_tigo = st.number_input("Numero Ottimizzatori Tigo:", min_value=0, value=None, step=1)
        prezzo_tigo = st.number_input("Prezzo Tigo (Senza IVA) €:", min_value=0.0, value=None, step=50.0)
        prezzo_tigo_iva_input = st.number_input("Prezzo Tigo (IVA Inclusa) €:", min_value=0.0, value=None, step=50.0)
        
    with col2:
        st.markdown("**SUNGROW**")
        n_sungrow = st.number_input("Numero Ottimizzatori Sungrow:", min_value=0, value=None, step=1)
        prezzo_sungrow = st.number_input("Prezzo Sungrow (Senza IVA) €:", min_value=0.0, value=None, step=50.0)
        prezzo_sungrow_iva_input = st.number_input("Prezzo Sungrow (IVA Inclusa) €:", min_value=0.0, value=None, step=50.0)

    st.markdown("---")
    
    totale_finale = st.number_input("Totale Chiavi in Mano (con iva e ottimizzatori) €:", min_value=0.0, value=None, step=100.00)
    
    note_aggiuntive = st.text_area("Note aggiuntive:")
                
    if st.button("Genera Preventivo SUNGROW"):
            
        # Formattiamo i numeri principali
        potenza_formattata = f"{potenza_nominale:.2f}".replace('.', ',') if potenza_nominale is not None else ""
        kwh_formattato = f"{capacita_accumulo:.2f}".replace('.', ',') if capacita_accumulo is not None else ""
        moduli_formattato = str(moduli) if moduli is not None else ""
        sistemi_formattato = str(sistemi_accumulo) if sistemi_accumulo is not None else ""
        
        # Formattiamo gli Ottimizzatori
        tigo_n_formattato = str(n_tigo) if n_tigo is not None else ""
        sungrow_n_formattato = str(n_sungrow) if n_sungrow is not None else ""
        
        prezzo_tigo_formattato = f"{prezzo_tigo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_tigo is not None else ""
        prezzo_tigo_iva = f"{prezzo_tigo_iva_input:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_tigo is not None else "" # Calcola automaticamente l'IVA al 10%
        
        prezzo_sungrow_formattato = f"{prezzo_sungrow:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_sungrow is not None else ""
        prezzo_sungrow_iva = f"{prezzo_sungrow_iva_input:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_sungrow is not None else "" # Calcola automaticamente l'IVA al 10%

        # PREZZO E TOTALE (Trucco del numero vs Euro)
        prezzo_solo_numero = f"{prezzo_base:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_base is not None else ""
        finale_solo_numero = f"{prezzo_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if prezzo_finale is not None else ""
        chiavi_in_mano = f"{totale_finale:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if totale_finale is not None else ""
            
        dati_inseriti = {
            "data": data_offerta,
            "referente": referente,
            "telefono": telefono,
            "cliente": nome_cognome,
            "indirizzo": indirizzo_residenza,
            "telefono_cliente": telefono_cliente,
            "email_cliente": email_cliente,
            "indirizzo_installazione": indirizzo_installazione,
                
            # Variabili specifiche
            "potenza_nominale": potenza_formattata,
            "kwh_totali": kwh_formattato,
            "moduli": moduli_formattato,
            "sistemi di accumulo": sistemi_formattato,
            
            # Ottimizzatori (le chiavi combaciano ESATTAMENTE con coordinate.py)
            "Ottimizzazione Tigo": tigo_n_formattato,
            "Prezzo Tigo": prezzo_tigo_formattato,
            "Prezzo Tigo piu' iva": prezzo_tigo_iva,
            
            "Ottimizzatore Sungrow": sungrow_n_formattato,
            "Prezzo Sungrow": prezzo_sungrow_formattato,
            "Prezzo Sungrow piu' iva": prezzo_sungrow_iva,
                
            # Prezzi e Totali
            "prezzo": prezzo_solo_numero,
            "piu' iva": finale_solo_numero,
            "chiavi in mano": chiavi_in_mano,
            "note": note_aggiuntive
        }
                
        nome_modello = tipo_preventivo.replace(" ", "_")
        nome_cliente = nome_cognome.replace(" ", "_") if nome_cognome else ""
        nome_file_finale = f"MASTER_{nome_modello}_{nome_cliente}.pdf"
        
        cartella_output = "cartella output"
        if not os.path.exists(cartella_output):
            os.makedirs(cartella_output)
                
        # ATTENZIONE: Assicurati che il nome file vuoto in assets sia esatto
        pdf_input = "assets/MASTER SUNGROW MONOFASE.pdf" 
        pdf_output_path = f"{cartella_output}/{nome_file_finale}"
            
        try:
            compila_pdf(pdf_input, dati_inseriti, coordinate_SUNGROW_MONOFASE, pdf_output_path)
            st.success("✅ Preventivo SUNGROW generato con successo!")
                
            with open(pdf_output_path, "rb") as pdf_file:
                st.download_button(
                    label="⬇️ SCARICA IL PREVENTIVO SUNGROW",
                    data=pdf_file,
                    file_name=nome_file_finale,
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Errore durante la creazione del PDF. Assicurati che il file '{pdf_input}' esista! Dettaglio: {e}")
