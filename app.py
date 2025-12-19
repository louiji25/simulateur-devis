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
st.set_page_config(
    page_title="Simulateur de devis",
    layout="centered"
)

# Fonction pour réinitialiser
def clear_form():
    st.session_state["form_id"] = str(uuid.uuid4())
    st.rerun()

if "form_id" not in st.session_state:
    st.session_state["form_id"] = str(uuid.uuid4())

# =========================
# LOGO (SÉCURISÉ)
# =========================
try:
    logo = Image.open("logo.png")
    st.image(logo, width=140)
except Exception:
    st.title("SIMULATEUR DE DEVIS")

st.subheader("Simulateur de devis")

# =========================
# CHARGEMENT DONNÉES
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
nom = col_c1.text_input("Nom du client", key=f"nom_{st.session_state['form_id']}")
email = col_c2.text_input("Email", key=f"email_{st.session_state['form_id']}")
ref = st.text_input("Référence devis", value=str(uuid.uuid4())[:8], key=f"ref_{st.session_state['form_id']}")

# =========================
# SECTION 2 : EXCURSION
# =========================
st.divider()
st.subheader("🧭 Excursion")

type_exc = st.selectbox("Type d’excursion", [""] + sorted(df["Type"].unique().tolist()), key=f"type_{st.session_state['form_id']}")

if type_exc:
    df_f1 = df[df["Type"] == type_exc]
    formule = st.selectbox("Formule", [""] + sorted(df_f1["Formule"].unique().tolist()), key=f"formule_{st.session_state['form_id']}")
else:
    formule = st.selectbox("Formule", [""], key=f"formule_empty")

if formule:
    df_f2 = df_f1[df_f1["Formule"] == formule]
    transport = st.selectbox("Transport", [""] + sorted(df_f2["Transport"].unique().tolist()), key=f"transp_{st.session_state['form_id']}")
else:
    transport = st.selectbox("Transport", [""], key=f"transp_empty")

if transport:
    df_f3 = df_f2[df_f2["Transport"] == transport]
    circuit = st.selectbox("Circuit", [""] + sorted(df_f3["Circuit"].unique().tolist()), key=f"circ_{st.session_state['form_id']}")
else:
    circuit = st.selectbox("Circuit", [""], key=f"circ_empty")

row = None
if circuit:
    row = df_f3[df_f3["Circuit"] == circuit].iloc[0]
    st.info(f"⏱ Durée : {row['Durée']}")

# =========================
# SECTION 3 : RÉGIME ET NOTES
# =========================
st.divider()
st.subheader("📝 Besoins spécifiques")
notes = st.text_area("Régime alimentaire, allergies ou demandes particulières", 
                     placeholder="Ex: 1 végétarien, allergie aux arachides...",
                     key=f"notes_{st.session_state['form_id']}")

# =========================
# SECTION 4 : OPTIONS & PERSONNES
# =========================
st.divider()
st.subheader("➕ Options & Participants")

c_opt1, c_opt2 = st.columns(2)
with c_opt1:
    repas = st.checkbox("🍽 Repas (+10 €/pers.)", key=f"repas_{st.session_state['form_id']}")
    guide = st.checkbox("🧭 Guide (+15 €/pers.)", key=f"guide_{st.session_state['form_id']}")
    visite = st.checkbox("🎫 Droit de visite (+5 €/pers.)", key=f"visite_{st.session_state['form_id']}")

with c_opt2:
    nb = st.number_input("Nombre de personnes", min_value=1, value=1, key=f"nb_{st.session_state['form_id']}")
    marge = st.number_input("Marge (%)", min_value=0, value=20, key=f"marge_{st.session_state['form_id']}")

# =========================
# CALCULS ET RÉSULTATS
# =========================
if row is not None:
    prix_base = row["Prix"]
    supps = (10 if repas else 0) + (15 if guide else 0) + (5 if visite else 0)
    total_achat = (prix_base + supps) * nb
    total_devis = total_achat * (1 + marge / 100)

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Prix / pers", f"{prix_base} €")
    res2.metric("Total Achat", f"{total_achat} €")
    res3.metric("Total Devis", f"{total_devis:.2f} €")

    # BOUTONS ACTIONS
    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("📄 Générer le devis PDF", use_container_width=True):
        if not nom:
            st.error("⚠️ Nom du client obligatoire.")
        else:
            pdf = FPDF()
            pdf.add_page()
            try:
                pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                pdf.set_font("DejaVu", "", 12)
            except:
                pdf.set_font("Arial", "", 12)

            pdf.set_font_size(16)
            pdf.cell(0, 10, "DEVIS PRESTATION TOURISTIQUE", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font_size(11)
            pdf.cell(0, 7, f"Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True)
            pdf.cell(0, 7, f"Client : {nom}", ln=True)
            pdf.ln(5)
            pdf.cell(0, 7, f"Circuit : {circuit} | Pax : {nb}", ln=True)
            if notes:
                pdf.set_text_color(200, 0, 0)
                pdf.multi_cell(0, 7, f"Notes : {notes}")
                pdf.set_text_color(0, 0, 0)
            pdf.ln(10)
            pdf.cell(0, 10, f"TOTAL : {total_devis:.2f} EUR", ln=True, align='R')

            # Sauvegarde Historique
            nouveau_devis = {"Date": datetime.now().strftime("%Y-%m-%d"), "Client": nom, "Circuit": circuit, "Total": round(total_devis, 2)}
            pd.DataFrame([nouveau_devis]).to_csv("historique_devis.csv", mode='a', header=not os.path.exists("historique_devis.csv"), index=False, encoding='utf-8-sig')
            
            st.download_button("⬇️ Télécharger maintenant", data=bytes(pdf.output()), file_name=f"devis_{nom}.pdf", mime="application/pdf")

    if col_btn2.button("🔄 Nouveau devis (Vider)", use_container_width=True):
        clear_form()

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
