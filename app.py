# 📦 Bloc 1 : Importations et Gestion de l'historique
# Ce bloc contient toutes les bibliothèques requises et la logique avancée de réécriture pour la suppression individuelle.

import streamlit as st
import yt_dlp
import os
import imageio_ffmpeg
import re
import subprocess
import sys
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Configuration de la page principale
st.set_page_config(page_title="Téléchargeur Multimédia Universel", page_icon="👑", layout="centered")

FICHIER_HISTORIQUE = ".historique_telechargements.txt"

# --- GESTION DE L'HISTORIQUE DE TÉLÉCHARGEMENT ---
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

# --- SÉLECTIONNEUR DE DOSSIER GRAPHIQUE (TKINTER) ---
def selectionner_dossier_fenetre():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    dossier_choisi = filedialog.askdirectory(initialdir=st.session_state.dossier_actuel)
    root.destroy()
    if dossier_choisi:
        st.session_state.dossier_actuel = os.path.abspath(dossier_choisi)


# 🎨 Bloc 2 : Interface, Barre latérale et Formulaires d'options
# Ce bloc gère l'affichage des titres, du bouton de mise à jour de secours, des sélecteurs de formats/résolutions et du découpage de plage horaire.

st.title("👑 Téléchargeur Multimédia Universel")
st.write("YouTube, TikTok, Vimeo, FB... | Gestion de file d'attente | Tags MP3 automatiques")

# Initialisation de la file d'attente dans l'état de la session
if "file_attente" not in st.session_state:
    st.session_state.file_attente = []

# BARRE LATÉRALE : MAINTENANCE ET INFOS SYSTEME
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

# Configuration à 2 colonnes pour l'ajout de lien
col_url_input, col_btn_add = st.columns(2)
with col_url_input:
    nouvel_url = st.text_input("Ajouter un lien (YouTube, TikTok, Vimeo, etc.) :", placeholder="https://...", key="url_input")
with col_btn_add:
    st.write(" ") # Alignement vertical
    if st.button("➕ Ajouter", use_container_width=True):
        if nouvel_url:
            if nouvel_url not in st.session_state.file_attente:
                st.session_state.file_attente.append(nouvel_url)
                st.toast("Lien ajouté à la file d'attente !")
            else:
                st.warning("Ce lien est déjà dans la file.")
        else:
            st.error("Veuillez entrer un lien.")

# Affichage visuel de la file d'attente actuelle
if st.session_state.file_attente:
    with st.expander(f"📋 Voir la file d'attente ({len(st.session_state.file_attente)} liens en attente)", expanded=True):
        for index, l in enumerate(st.session_state.file_attente):
            c_link, c_action = st.columns(2)
            c_link.caption(l)
            if c_action.button("Retirer", key=f"remove_queue_{index}", help="Retirer ce lien"):
                st.session_state.file_attente.pop(index)
                st.rerun()
        if st.button("🧹 Vider complètement la file d'attente", type="secondary"):
            st.session_state.file_attente = []
            st.rerun()
else:
    st.info("La file d'attente est vide. Ajoutez un ou plusieurs liens ci-dessus.")

# Options globales applicables à toute la file
st.write("---")
st.subheader("⚙️ Options de téléchargement")
col1, col2 = st.columns(2)

with col1:
    format_choisi = st.radio("Sélectionnez le format de sortie :", ("Vidéo (MP4)", "Audio uniquement (MP3)"))

with col2:
    if format_choisi == "Vidéo (MP4)":
        resolution = st.selectbox("Choisissez la résolution maximale :", ("1080p (Full HD)", "720p (HD)", "Meilleure qualité disponible"))
    else:
        resolution = st.selectbox("Qualité audio :", ("192 kbps (Standard)", "320 kbps (Haute qualité)"))

# Découpage horaire
st.write("---")
st.subheader("✂️ Découpage (Optionnel - Désactivé si traitement par lot)")
activer_decoupage = st.checkbox("Télécharger une plage horaire spécifique", disabled=len(st.session_state.file_attente) > 1)

col_debut, col_fin = st.columns(2)
with col_debut:
    temps_debut = st.text_input("Début (HH:MM:SS ou MM:SS) :", value="00:00", disabled=not activer_decoupage)
with col_fin:
    temps_fin = st.text_input("Fin (HH:MM:SS ou MM:SS) :", value="01:00", disabled=not activer_decoupage)


# 📂 Bloc 3 : Raccourcis Dossiers et Hook de Progression Interactif
# Ce bloc configure l'accès direct aux répertoires de votre PC et gère l'affichage dynamique de la barre de progression.

st.write("---")
st.subheader("📁 Dossier d'enregistrement")

chemin_home = os.path.expanduser("~")
dossiers_raccourcis = {
    "📥 Téléchargements": os.path.join(chemin_home, "Downloads"),
    "🖥️ Bureau": os.path.join(chemin_home, "Desktop"),
    "🎬 Vidéos": os.path.join(chemin_home, "Videos"),
    "🎵 Musique": os.path.join(chemin_home, "Music")
}

if "dossier_actuel" not in st.session_state:
    st.session_state.dossier_actuel = dossiers_raccourcis["📥 Téléchargements"]

cols_dossiers = st.columns(4)
for i, (nom_dossier, chemin_dossier) in enumerate(dossiers_raccourcis.items()):
    with cols_dossiers[i]:
        if st.button(nom_dossier, use_container_width=True):
            st.session_state.dossier_actuel = chemin_dossier

# Alignement explicite à 2 colonnes
col_chemin, col_parcourir = st.columns(2)

with col_chemin:
    dossier_personnalise = st.text_input("Chemin sélectionné :", value=st.session_state.dossier_actuel, label_visibility="collapsed")

with col_parcourir:
    if st.button("🔍 Parcourir...", use_container_width=True):
        selectionner_dossier_fenetre()
        st.rerun()

if not os.path.exists(dossier_personnalise):
    try:
        os.makedirs(dossier_personnalise, exist_ok=True)
        dossier_final = dossier_personnalise
    except:
        dossier_final = dossiers_raccourcis["📥 Téléchargements"]
else:
    dossier_final = dossier_personnalise

# GESTIONNAIRE DE PROGRESSION INTERACTIVE DYNAMIQUE
st.write("---")
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
            vitesse = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'Vitesse inconnue'))
            temps_restant = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_eta_str', '--:--'))
            zone_statut.text(f"📥 Téléchargement : {pourcentage_str.strip()} | {vitesse.strip()} | Restant : {temps_restant.strip()}")
    elif d['status'] == 'finished':
        zone_statut.text("🎬 Traitement, assemblage ou injection de métadonnées FFmpeg en cours...")


# 

# 🚀 Bloc 4 : Traitement par Lot et Historique avec Sécurité Renforcée
# Ce dernier bloc boucle sur l'ensemble de votre file d'attente, force le découpage FFmpeg et n'enregistre le fichier qu'une fois validé et assemblé sur le disque.

# 6. ACTION DU BOUTON PRINCIPAL DE TRAITEMENT
if st.button("🚀 Lancer le téléchargement de la file d'attente", type="primary", use_container_width=True):
    if not st.session_state.file_attente:
        st.error("Votre file d'attente est vide ! Ajoutez au moins un lien avant de démarrer.")
    else:
        chemin_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        total_liens = len(st.session_state.file_attente)
        liens_a_traiter = list(st.session_state.file_attente)
        
        for idx_lien, cible_url in enumerate(liens_a_traiter):
            st.toast(f"Traitement du lien {idx_lien + 1}/{total_liens}...")
            
            ydl_opts = {
                'outtmpl': os.path.join(dossier_final, '%(title)s.%(ext)s'),
                'ffmpeg_location': chemin_ffmpeg,
                'progress_hooks': [avancement_hook],
                'ignoreerrors': True,
            }

            # DÉCOUPAGE HORAIRE STRICT
            if activer_decoupage and total_liens == 1:
                ydl_opts.update({
                    'force_keyframes_at_cuts': True,
                    'postprocessor_args': {
                        'ffmpeg': ['-ss', temps_debut, '-to', temps_fin]
                    }
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
                if "1080p" in resolution:
                    filtre_format = 'bestvideo[height<=1080]+bestaudio/best'
                elif "720p" in resolution:
                    filtre_format = 'bestvideo[height<=720]+bestaudio/best'
                else:
                    filtre_format = 'bestvideo+bestaudio/best'
                ydl_opts.update({
                    'format': filtre_format,
                    'merge_output_format': 'mp4',
                })

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    zone_statut.text(f"🔍 Analyse de la source ({idx_lien+1}/{total_liens})...")
                    
                    # On extrait d'abord les infos
                    info_dict = ydl.extract_info(cible_url, download=True)
                    
                    if info_dict:
                        if 'entries' in info_dict:
                            for entry in info_dict['entries']:
                                if entry:
                                    # Correction : Récupération du titre et construction du chemin final propre après traitement
                                    titre = entry.get('title', 'Médias Playlist')
                                    ext_finale = "mp3" if format_choisi == "Audio uniquement (MP3)" else "mp4"
                                    chemin_final_propre = os.path.join(dossier_final, f"{titre}.{ext_finale}")
                                    enregistrer_dans_historique(titre, entry.get('webpage_url', cible_url), format_choisi, chemin_final_propre)
                        else:
                            titre = info_dict.get('title', 'Média Unique')
                            ext_finale = "mp3" if format_choisi == "Audio uniquement (MP3)" else "mp4"
                            chemin_final_propre = os.path.join(dossier_final, f"{titre}.{ext_finale}")
                            enregistrer_dans_historique(titre, cible_url, format_choisi, chemin_final_propre)
                
                st.session_state.file_attente.remove(cible_url)
            except Exception as e:
                st.error(f"Une erreur est survenue sur le lien {cible_url} : {e}")
        
        barre_progression.empty()
        zone_statut.empty()
        st.success(f"🎉 Tous les traitements ont été complétés !")
        st.rerun()

# 7. SECTION HISTORIQUE DE VUE ET SUPPRESSION INDIVIDUELLE SÉCURISÉE
st.write("---")
st.subheader("📜 Historique et Lecteur Multimédia")

lignes_historique = lire_historique()

if not lignes_historique:
    st.info("Votre historique est actuellement vide.")
else:
    if st.button("🗑️ Effacer TOUT l'historique", type="secondary", use_container_width=True):
        effacer_historique()
        st.rerun()
    
    st.write("")
    
    for i in reversed(range(len(lignes_historique))):
        item = lignes_historique[i]
        parties = item.strip().split(" | ")
        
        if len(parties) >= 3:
            col_texte, col_suppr = st.columns(2)
            
            with col_texte:
                st.markdown(f"• {parties} | {parties} | {parties}")
            
            with col_suppr:
                if st.button("❌", key=f"del_{i}", help="Supprimer cette ligne"):
                    supprimer_element_historique(i)
                    st.rerun()
            
            if len(parties) == 4:
                chemin_cible_brut = str(parties).strip()
                
                if chemin_cible_brut and not chemin_cible_brut.startswith("[") and os.path.exists(chemin_cible_brut):
                    ext_media = os.path.splitext(chemin_cible_brut).lower()
                    
                    with st.expander(f"▶️ Visionner / Écouter l'enregistrement local"):
                        try:
                            with open(chemin_cible_brut, "rb") as media_file:
                                bytes_data = media_file.read()
                                if ext_media == ".mp3":
                                    st.audio(bytes_data, format="audio/mp3")
                                else:
                                    st.video(bytes_data, format="video/mp4")
                        except Exception as media_err:
                            st.caption("Lecture locale temporairement verrouillée par le système de stockage.")
            st.write("---")



