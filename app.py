import streamlit as st
import pandas as pd
import uuid
from fpdf import FPDF
from PIL import Image
import os
from datetime import datetime

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(page_title="Simulateur de devis", layout="centered")

def clear_form():
    st.session_state["form_id"] = str(uuid.uuid4())
    st.rerun()

if "form_id" not in st.session_state:
    st.session_state["form_id"] = str(uuid.uuid4())

# =========================
# LOGO
# =========================
try:
    logo = Image.open("logo.png")
    st.image(logo, width=140)
except:
    st.title("SIMULATEUR DE DEVIS")

# =========================
# CHARGEMENT DES DONNÉES
# =========================
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")
df = load_data()

# =========================
# SECTION 1 : CLIENT
# =========================
st.divider()
st.subheader("👤 Informations client")
col_c1, col_c2 = st.columns(2)
nom = col_c1.text_input("Nom du client", key=f"n_{st.session_state['form_id']}")
email = col_c2.text_input("Email", key=f"e_{st.session_state['form_id']}")
ref = st.text_input("Référence devis", value=str(uuid.uuid4())[:8], key=f"r_{st.session_state['form_id']}")

# =========================
# SECTION 2 : EXCURSION
# =========================
st.divider()
st.subheader("🧭 Excursion")
type_exc = st.selectbox("Type", [""] + sorted(df["Type"].unique().tolist()), key=f"t_{st.session_state['form_id']}")

circuit = None
formule = ""
transport = ""

if type_exc:
    df_f = df[df["Type"] == type_exc]
    formule = st.selectbox("Formule", [""] + sorted(df_f["Formule"].unique().tolist()), key=f"f_{st.session_state['form_id']}")
    if formule:
        df_f = df_f[df_f["Formule"] == formule]
        transport = st.selectbox("Transport", [""] + sorted(df_f["Transport"].unique().tolist()), key=f"tr_{st.session_state['form_id']}")
        if transport:
            df_f = df_f[df_f["Transport"] == transport]
            circuit = st.selectbox("Circuit", [""] + sorted(df_f["Circuit"].unique().tolist()), key=f"c_{st.session_state['form_id']}")

row = None
if circuit:
    row = df_f[df_f["Circuit"] == circuit].iloc[0]
    st.info(f"⏱ Durée : {row['Durée']}")

# =========================
# SECTION 3 : BESOINS SPÉCIFIQUES
# =========================
st.divider()
st.subheader("📝 Besoins spécifiques")
notes = st.text_area("Régime alimentaire, allergies ou demandes particulières", key=f"nt_{st.session_state['form_id']}")

# =========================
# SECTION 4 : OPTIONS & PARTICIPANTS
# =========================
st.divider()
st.subheader("➕ Options & Participants")
c1, c2 = st.columns(2)
with c1:
    repas = st.checkbox("🍽 Repas (+10 €/pers.)", key=f"rp_{st.session_state['form_id']}")
    guide = st.checkbox("🧭 Guide (+15 €/pers.)", key=f"gd_{st.session_state['form_id']}")
    visite = st.checkbox("🎫 Visites (+5 €/pers.)", key=f"vs_{st.session_state['form_id']}")
with c2:
    nb = st.number_input("Nombre de personnes (Pax)", min_value=1, value=1, key=f"nb_{st.session_state['form_id']}")
    marge = st.number_input("Marge (%)", min_value=0, value=20, key=f"m_{st.session_state['form_id']}")

# =========================
# CALCULS ET PDF
# =========================
if row is not None:
    p_base = row["Prix"]
    supps = (10 if repas else 0) + (15 if guide else 0) + (5 if visite else 0)
    total_unit = p_base + supps
    total_devis = (total_unit * nb) * (1 + marge / 100)

    st.divider()
    st.metric("TOTAL DEVIS CLIENT", f"{total_devis:.2f} €")

    if st.button("📄 Générer le devis détaillé"):
        if not nom:
            st.error("Le nom du client est requis.")
        else:
            pdf = FPDF()
            pdf.add_page()
            
            try:
                pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                font_f = "DejaVu"
            except:
                font_f = "Arial"

            # En-tête
            pdf.set_font(font_f, size=18)
            pdf.cell(0, 15, "DEVIS PRESTATION TOURISTIQUE", ln=True, align='C')
            pdf.set_font(font_f, size=10)
            pdf.cell(0, 5, f"Référence : {ref} | Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
            pdf.ln(10)

            # Infos Client & Détails Excursion
            pdf.set_font(font_f, size=11)
            pdf.cell(0, 7, f"Client : {nom}", ln=True)
            pdf.cell(0, 7, f"Formule choisie : {formule}", ln=True)
            pdf.cell(0, 7, f"Transport : {transport}", ln=True)
            pdf.cell(0, 7, f"Nombre de participants : {nb} personne(s)", ln=True)
            pdf.ln(5)

            # Tableau des prix
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font(font_f, size=10)
            pdf.cell(90, 10, "Description de la prestation", 1, 0, 'C', True)
            pdf.cell(30, 10, "Quantité", 1, 0, 'C', True)
            pdf.cell(30, 10, "Prix Unitaire", 1, 0, 'C', True)
            pdf.cell(35, 10, "Total (€)", 1, 1, 'C', True)
            
            # Ligne de base (Circuit)
            pdf.cell(90, 8, f"Circuit : {circuit}", 1)
            pdf.cell(30, 8, f"{nb}", 1, 0, 'C')
            pdf.cell(30, 8, f"{p_base:.2f}", 1, 0, 'C')
            pdf.cell(35, 8, f"{p_base * nb:.2f}", 1, 1, 'C')
            
            # Options
            if repas:
                pdf.cell(90, 8, "Option : Repas", 1)
                pdf.cell(30, 8, f"{nb}", 1, 0, 'C')
                pdf.cell(30, 8, "10.00", 1, 0, 'C')
                pdf.cell(35, 8, f"{10 * nb:.2f}", 1, 1, 'C')
            if guide:
                pdf.cell(90, 8, "Option : Guide", 1)
                pdf.cell(30, 8, f"{nb}", 1, 0, 'C')
                pdf.cell(30, 8, "15.00", 1, 0, 'C')
                pdf.cell(35, 8, f"{15 * nb:.2f}", 1, 1, 'C')
            if visite:
                pdf.cell(90, 8, "Option : Droits de visite", 1)
                pdf.cell(30, 8, f"{nb}", 1, 0, 'C')
                pdf.cell(30, 8, "5.00", 1, 0, 'C')
                pdf.cell(35, 8, f"{5 * nb:.2f}", 1, 1, 'C')

            # Ligne Total
            pdf.set_font(font_f, size=11)
            pdf.cell(150, 10, "TOTAL TTC À PAYER", 1, 0, 'R', True)
            pdf.cell(35, 10, f"{total_devis:.2f} EUR", 1, 1, 'C', True)

            # Notes / Besoins spécifiques
            if notes:
                pdf.ln(5)
                pdf.set_text_color(200, 0, 0)
                pdf.multi_cell(0, 6, f"Demandes particulières : {notes}", border=1)
                pdf.set_text_color(0, 0, 0)

            pdf_bytes = bytes(pdf.output())
            st.download_button("⬇️ Télécharger le PDF", pdf_bytes, f"devis_{nom}.pdf", "application/pdf")
            
            # Enregistrement historique
            new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Client": nom, "Formule": formule, "Circuit": circuit, "Pax": nb, "Total": round(total_devis, 2)}
            pd.DataFrame([new_row]).to_csv("historique_devis.csv", mode='a', header=not os.path.exists("historique_devis.csv"), index=False, encoding='utf-8-sig')

    st.button("🔄 Nouveau devis", on_click=clear_form)


# =========================
# HISTORIQUE RAPIDE (CORRIGÉ)
# =========================
st.divider()
with st.expander("📊 Voir l'historique des devis"):
    hist_file = "historique_devis.csv"
    
    if os.path.exists(hist_file):
        try:
            # On vérifie si le fichier n'est pas vide avant de lire
            if os.path.getsize(hist_file) > 0:
                df_history = pd.read_csv(hist_file)
                st.dataframe(df_history, use_container_width=True)
                
                # Option pour télécharger l'historique complet en Excel/CSV
                st.download_button(
                    label="📥 Exporter l'historique CSV",
                    data=df_history.to_csv(index=False).encode('utf-8-sig'),
                    file_name="historique_complet.csv",
                    mime="text/csv"
                )
            else:
                st.info("L'historique est actuellement vide.")
        except Exception as e:
            st.error(f"Erreur lors de la lecture de l'historique : {e}")
            if st.button("Réinitialiser le fichier historique"):
                os.remove(hist_file)
                st.rerun()
    else:
        st.write("Aucun historique pour le moment. Générez votre premier devis !")
