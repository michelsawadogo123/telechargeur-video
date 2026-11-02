# 📦 Bloc 1 : Importations et Gestion de l'historique (Spécial Web Cloud)
# Version allégée sans Tkinter pour fonctionner sur les serveurs Linux de Streamlit Cloud.

import streamlit as st
import yt_dlp
import os
import imageio_ffmpeg
import re
import subprocess
import sys
from datetime import datetime

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



# 🎨 Bloc 2 : Interface, Gestion de la File d'Attente et Options
# Ce bloc gère l'affichage général, la file d'attente et les configurations multimédias.

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
    st.write(" ") 
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



# 📂 Bloc 3 : Emplacement Serveur et Progression
# Gestion simplifiée du stockage temporaire sur le serveur distant et barre de progression.

st.write("---")
# Sur le serveur cloud, on force l'utilisation du stockage temporaire système
dossier_final = "/tmp" if os.path.exists("/tmp") else "."

# Initialisation d'une variable de stockage globale du dernier fichier téléchargé pour le bouton de téléchargement web
if "dernier_fichier_telecharge" not in st.session_state:
    st.session_state.dernier_fichier_telecharge = None
if "nom_affichage_fichier" not in st.session_state:
    st.session_state.nom_affichage_fichier = "fichier"

# GESTIONNAIRE DE PROGRESSION INTERACTIVE DYNAMIQUE
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
            zone_statut.text(f"📥 Extraction sur le serveur : {pourcentage_str.strip()} | {vitesse.strip()}")
    elif d['status'] == 'finished':
        zone_statut.text("🎬 Traitement, assemblage ou injection de métadonnées FFmpeg en cours...")



# 🚀 Bloc 4 : Traitement par Lot et Historique avec Téléchargement Web Intégré
# Ce dernier bloc boucle sur l'ensemble de votre file d'attente et génère des boutons de téléchargement permanents directement dans l'historique.

# 6. ACTION DU BOUTON PRINCIPAL DE TRAITEMENT
if st.button("🚀 Lancer l'extraction sur le serveur", type="primary", use_container_width=True):
    # Sécurité au cas où l'utilisateur oublie de cliquer sur "+ Ajouter"
    liens_a_traiter = list(st.session_state.file_attente)
    if not liens_a_traiter and url:
        liens_a_traiter.append(url)
        
    if not liens_a_traiter:
        st.error("Votre file d'attente est vide ! Ajoutez un lien avec le bouton '+ Ajouter' avant de démarrer.")
    else:
        chemin_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        total_liens = len(liens_a_traiter)
        
        for idx_lien, cible_url in enumerate(liens_a_traiter):
            st.toast(f"Traitement du lien {idx_lien + 1}/{total_liens}...")
            
            ydl_opts = {
                'outtmpl': os.path.join(dossier_final, '%(title)s.%(ext)s'),
                'ffmpeg_location': chemin_ffmpeg,
                'progress_hooks': [avancement_hook],
                'ignoreerrors': True,
            }

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
                    'format': filtro_format if 'filtro_format' in locals() else filtre_format,
                    'merge_output_format': 'mp4',
                })

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    zone_statut.text(f"🔍 Analyse de la source ({idx_lien+1}/{total_liens})...")
                    info_dict = ydl.extract_info(cible_url, download=True)
                    
                    if info_dict:
                        if 'entries' in info_dict:
                            for entry in info_dict['entries']:
                                if entry:
                                    titre = entry.get('title', 'Médias Playlist')
                                    ext_finale = "mp3" if format_choisi == "Audio uniquement (MP3)" else "mp4"
                                    chemin_final_propre = os.path.join(dossier_final, f"{titre}.{ext_finale}")
                                    enregistrer_dans_historique(titre, entry.get('webpage_url', cible_url), format_choisi, chemin_final_propre)
                        else:
                            titre = info_dict.get('title', 'Média Unique')
                            ext_finale = "mp3" if format_choisi == "Audio uniquement (MP3)" else "mp4"
                            chemin_final_propre = os.path.join(dossier_final, f"{titre}.{ext_finale}")
                            enregistrer_dans_historique(titre, cible_url, format_choisi, chemin_final_propre)
                
                if cible_url in st.session_state.file_attente:
                    st.session_state.file_attente.remove(cible_url)
            except Exception as e:
                st.error(f"Une erreur est survenue sur le lien {cible_url} : {e}")
        
        barre_progression.empty()
        zone_statut.empty()
        st.success(f"🎉 Extraction terminée avec succès !")
        st.rerun()

# 7. SECTION HISTORIQUE ET BOUTONS DE SAUVEGARDE WEB DIRECTS
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
            # Séparation propre de l'affichage sur 3 colonnes : Infos | Sauvegarder | Supprimer
            col_texte, col_recup, col_suppr = st.columns([6, 3, 1])
            
            with col_texte:
                st.markdown(f"• {parties} | {parties} | {parties}")
            
            # AMÉLIORATION : Bouton de téléchargement web permanent s'adaptant à chaque ligne
            chemin_fic_media = str(parties).strip() if len(parties) == 4 else ""
            
            with col_recup:
                if chemin_fic_media and not chemin_fic_media.startswith("[") and os.path.exists(chemin_fic_media):
                    nom_fic = os.path.basename(chemin_fic_media)
                    try:
                        with open(chemin_fic_media, "rb") as file_data:
                            st.download_button(
                                label="📥 Sauvegarder",
                                data=file_data.read(),
                                file_name=nom_fic,
                                mime="video/mp4" if nom_fic.endswith(".mp4") else "audio/mp3",
                                key=f"dl_btn_{i}"
                            )
                    except:
                        st.caption("Fichier expiré")
                else:
                    st.caption("Fichier non trouvé sur le serveur")
            
            with col_suppr:
                if st.button("❌", key=f"del_{i}", help="Supprimer cette ligne"):
                    supprimer_element_historique(i)
                    st.rerun()
            st.write("---")


