# 📦 Bloc 1 : Importations et Fonctions Historique
import streamlit as st
import yt_dlp
import os
import imageio_ffmpeg
import re
import subprocess
import sys
from datetime import datetime

FICHIER_HISTORIQUE = ".historique_telechargements.txt"

def enregistrer_dans_historique(titre, url, format_type, chemin_fichier=""):
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    titre_propre = re.sub(r'[\[\]]', '', str(titre))
    ligne = f"{date_str} | {format_type} | [{titre_propre}]({url}) | {chemin_fichier}\n"
    with open(FICHIER_HISTORIQUE, "a", encoding="utf-8") as f:
        f.write(ligne)

def lire_historique():
    if not os.path.exists(FICHIER_HISTORIQUE):
        return []
    with open(FICHIER_HISTORIQUE, "r", encoding="utf-8") as f:
        lignes = f.readlines()
    return lignes

def supprimer_element_historique(index_a_supprimer):
    if os.path.exists(FICHIER_HISTORIQUE):
        with open(FICHIER_HISTORIQUE, "r", encoding="utf-8") as f:
            lignes = f.readlines()
        with open(FICHIER_HISTORIQUE, "w", encoding="utf-8") as f:
            for idx, ligne in enumerate(lignes):
                if idx != index_a_supprimer:
                    f.write(ligne)

def effacer_historique():
    if os.path.exists(FICHIER_HISTORIQUE):
        os.remove(FICHIER_HISTORIQUE)




# 🎨 Bloc 2 : Interface et File d'Attente
st.set_page_config(page_title="Téléchargeur Multimédia Universel", page_icon="👑", layout="centered")

st.title("👑 Téléchargeur Multimédia Universel")
st.write("YouTube, TikTok, Vimeo, FB... | Gestion de file d'attente | Tags MP3 automatiques")

if "file_attente" not in st.session_state:
    st.session_state.file_attente = []

with st.sidebar:
    st.header("⚙️ Maintenance Système")
    if st.button("🔄 Mettre à jour yt-dlp", use_container_width=True):
        with st.spinner("Mise à jour..."):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
                st.success("Moteur universel mis à jour !")
            except Exception as e:
                st.error(f"Erreur : {e}")

st.write("---")
st.subheader("⏳ Gestionnaire de File d'Attente")

col_url_input, col_btn_add = st.columns(2)
with col_url_input:
    nouvel_url = st.text_input("Ajouter un lien :", placeholder="https://...", key="url_input", label_visibility="collapsed")
with col_btn_add:
    if st.button("➕ Ajouter à la file", use_container_width=True):
        if nouvel_url:
            if nouvel_url not in st.session_state.file_attente:
                st.session_state.file_attente.append(nouvel_url)
                st.toast("Lien ajouté !")
            else:
                st.warning("Déjà dans la file.")
        else:
            st.error("Lien vide.")

if st.session_state.file_attente:
    with st.expander(f"📋 Voir la file ({len(st.session_state.file_attente)} liens)", expanded=True):
        for index, l in enumerate(st.session_state.file_attente):
            c_link, c_action = st.columns(2)
            c_link.caption(l)
            if c_action.button("Retirer", key=f"rem_q_{index}"):
                st.session_state.file_attente.pop(index)
                st.rerun()
        if st.button("🧹 Vider la file", type="secondary"):
            st.session_state.file_attente = []
            st.rerun()
else:
    st.info("La file d'attente est vide.")



# 📂 Bloc 3 : Options et Moteur de Progression
st.write("---")
st.subheader("⚙️ Options de téléchargement")
col1, col2 = st.columns(2)

with col1:
    format_choisi = st.radio("Format de sortie :", ("Vidéo (MP4)", "Audio uniquement (MP3)"))
with col2:
    if format_choisi == "Vidéo (MP4)":
        resolution = st.selectbox("Résolution maximale :", ("1080p (Full HD)", "720p (HD)", "Meilleure qualité disponible"))
    else:
        resolution = st.selectbox("Qualité audio :", ("192 kbps (Standard)", "320 kbps (Haute qualité)"))

st.write("---")
st.subheader("✂️ Découpage (Optionnel)")
activer_decoupage = st.checkbox("Télécharger une plage horaire", disabled=len(st.session_state.file_attente) > 1)

col_debut, col_fin = st.columns(2)
with col_debut:
    temps_debut = st.text_input("Début (HH:MM:SS ou MM:SS) :", value="00:00", disabled=not activer_decoupage)
with col_fin:
    temps_fin = st.text_input("Fin (HH:MM:SS ou MM:SS) :", value="01:00", disabled=not activer_decoupage)

dossier_final = "/tmp" if os.path.exists("/tmp") else "."

zone_titre_actuel = st.empty()
barre_progression = st.empty()
zone_statut = st.empty()

def avancement_hook(d):
    if d['status'] == 'downloading':
        pourcentage_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%'))
        match = re.search(r'([0-9.]+)%', pourcentage_str)
        if match:
            valeur_progression = float(match.group(1)) / 100.0
            valeur_progression = max(0.0, min(1.0, valeur_progression))
            barre_progression.progress(valeur_progression)
            vitesse = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'Vitesse...'))
            zone_statut.text(f"📥 Extraction : {pourcentage_str.strip()} | {vitesse.strip()}")
    elif d['status'] == 'finished':
        zone_statut.text("🎬 Traitement et fusion par FFmpeg...")


# 🚀 Bloc 4 : Traitement et Affichage Historique Sécurisé
if "fichiers_memoire" not in st.session_state:
    st.session_state.fichiers_memoire = {}

if st.button("🚀 Lancer l'extraction sur le serveur", type="primary", use_container_width=True):
    liens_a_traiter = list(st.session_state.file_attente)
    
    if not liens_a_traiter:
        st.error("Votre file d'attente est vide ! Ajoutez un lien avec le bouton '+ Ajouter à la file' avant de démarrer.")
    else:
        chemin_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        total_liens = len(liens_a_traiter)
        
        for idx_lien, cible_url in enumerate(liens_a_traiter):
            st.toast(f"Lien {idx_lien + 1}/{total_liens}...")
            ydl_opts = {
                'outtmpl': os.path.join(dossier_final, '%(title)s.%(ext)s'),
                'ffmpeg_location': chemin_ffmpeg,
                'progress_hooks': [avancement_hook],
                'ignoreerrors': True,
            }

            if activer_decoupage and total_liens == 1:
                ydl_opts.update({
                    'force_keyframes_at_cuts': True,
                    'postprocessor_args': {'ffmpeg': ['-ss', temps_debut, '-to', temps_fin]}
                })

            if format_choisi == "Audio uniquement (MP3)":
                qualite_audio = '192' if "192" in resolution else '320'
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'writethumbnail': True,
                    'postprocessors': [
                        {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': qualite_audio},
                        {'key': 'FFmpegMetadata', 'add_metadata': True},
                        {'key': 'EmbedThumbnail'}
                    ],
                })
            else:
                filtre_format = 'bestvideo[height<=1080]+bestaudio/best' if "1080p" in resolution else ('bestvideo[height<=720]+bestaudio/best' if "720p" in resolution else 'bestvideo+bestaudio/best')
                ydl_opts.update({'format': filtre_format, 'merge_output_format': 'mp4'})

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(cible_url, download=True)
                    if info_dict:
                        titre = info_dict.get('title', 'Média')
                        ext_finale = "mp3" if format_choisi == "Audio uniquement (MP3)" else "mp4"
                        chemin_temporaire = ydl.prepare_filename(info_dict)
                        nom_base, _ = os.path.splitext(chemin_temporaire)
                        chemin_réel = nom_base + f".{ext_finale}"
                        
                        if os.path.exists(chemin_réel):
                            titre_nettoye = re.sub(r'\W+', '', titre)
                            cle_cle = f"{titre_nettoye}_{datetime.now().strftime('%M%S')}"
                            with open(chemin_réel, "rb") as f_bytes:
                                st.session_state.fichiers_memoire[cle_cle] = f_bytes.read()
                            enregistrer_dans_historique(titre, cible_url, format_choisi, cle_cle)
                if cible_url in st.session_state.file_attente:
                    st.session_state.file_attente.remove(cible_url)
            except Exception as e:
                st.error(f"Erreur : {e}")
        st.rerun()

st.write("---")
st.subheader("📜 Historique et Lecteur Multimédia")
lignes_historique = lire_historique()

if not lignes_historique:
    st.info("Votre historique est vide.")
else:
    if st.button("🗑️ Effacer TOUT l'historique", type="secondary", use_container_width=True):
        effacer_historique()
        st.session_state.fichiers_memoire = {}
        st.rerun()
        
    for i in reversed(range(len(lignes_historique))):
        item = lignes_historique[i]
        parties = item.strip().split(" | ")
        if len(parties) >= 3:
            col_texte, col_recup, col_suppr = st.columns(3)
            with col_texte:
                st.markdown(f"• {parties} | {parties} | {parties}")
            
            cle_stockage = parties.strip() if len(parties) == 4 else ""
            with col_recup:
                if cle_stockage in st.session_state.fichiers_memoire:
                    ext = "mp3" if "MP3" in parties else "mp4"
                    st.download_button(
                        label="📥 Sauvegarder",
                        data=st.session_state.fichiers_memoire[cle_stockage],
                        file_name=f"telechargement.{ext}",
                        mime="audio/mp3" if ext == "mp3" else "video/mp4",
                        key=f"dl_m_{i}"
                    )
                else:
                    st.caption("Absent")
            with col_suppr:
                if st.button("❌", key=f"del_{i}"):
                    if cle_stockage in st.session_state.fichiers_memoire:
                        del st.session_state.fichiers_memoire[cle_stockage]
                    supprimer_element_historique(i)
                    st.rerun()
