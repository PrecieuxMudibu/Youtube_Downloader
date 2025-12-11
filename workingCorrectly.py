import streamlit as st
import yt_dlp
import os
import time

# Configuration de la page
st.set_page_config(page_title="Téléchargeur YouTube (Fichier Complet)", layout="centered")

def progress_hook(d):
    """Fonction pour afficher la progression via yt-dlp"""
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%').replace('%','')
            st.session_state['progress_bar'].progress(float(p)/100)
            st.session_state['status_text'].text(f"Téléchargement en cours... {d.get('_percent_str')} - Temps restant: {d.get('_eta_str')}")
        except:
            pass
    elif d['status'] == 'finished':
        st.session_state['status_text'].text("Téléchargement terminé. Préparation du fichier...")
        st.session_state['progress_bar'].progress(1.0)

def download_video_local(url, quality_choice):
    # Création d'un dossier temporaire pour stocker le fichier
    output_folder = "downloads_temp"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Nettoyage préalable du dossier (pour éviter d'encombrer)
    for f in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, f))

    # Configuration de la hauteur max
    if "Best" in quality_choice:
        height_limit = 2160
    else:
        height_limit = int(quality_choice.replace('p', ''))

    # Configuration de yt-dlp pour TÉLÉCHARGER RÉELLEMENT sur le disque
    # On force 'mp4' pour assurer la compatibilité hors ligne
    ydl_opts = {
        'format': f'best[ext=mp4][height<={height_limit}]/best[ext=mp4]/best',
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s', # Chemin de sortie
        'noplaylist': True,
        'progress_hooks': [progress_hook], # Connecte la barre de progression
        'quiet': True,
        'overwrites': True,
    }

    try:
        # Initialisation des éléments d'interface pour la progression
        if 'progress_bar' not in st.session_state:
            st.session_state['progress_bar'] = st.progress(0)
        if 'status_text' not in st.session_state:
            st.session_state['status_text'] = st.empty()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Téléchargement réel sur le disque
            info = ydl.extract_info(url, download=True)
            
            # 2. Retrouver le nom du fichier téléchargé
            filename = ydl.prepare_filename(info)
            
            # Correction si l'extension a changé pendant le téléchargement
            if not os.path.exists(filename):
                # Parfois yt-dlp change l'extension (ex: .mkv vers .mp4), on cherche le fichier
                base_name = os.path.splitext(filename)[0]
                possible_files = [f for f in os.listdir(output_folder) if base_name in os.path.join(output_folder, f)]
                if possible_files:
                    filename = os.path.join(output_folder, possible_files[0])
            
            return filename, os.path.basename(filename)

    except Exception as e:
        st.error(f"Erreur lors du téléchargement : {e}")
        return None, None

# --- Interface Utilisateur ---
st.title("📦 Téléchargeur YouTube (Mode Hors-Ligne)")
st.info("Ce mode télécharge la vidéo complète sur le serveur avant de vous la donner. Cela garantit que le fichier fonctionnera sans internet.")

url = st.text_input("URL YouTube :")
quality = st.selectbox("Qualité souhaitée :", ["720p", "360p", "Best"])

if st.button("Lancer le téléchargement"):
    if url:
        with st.spinner("Traitement en cours..."):
            # Initialisation des états
            st.session_state['progress_bar'] = st.progress(0)
            st.session_state['status_text'] = st.empty()
            
            file_path, file_name = download_video_local(url, quality)
            
            if file_path and os.path.exists(file_path):
                st.success("Vidéo prête !")
                
                # Lecture du fichier en mode binaire pour le bouton de téléchargement
                with open(file_path, "rb") as file:
                    file_bytes = file.read()
                    
                st.download_button(
                    label=f"💾 Enregistrer {file_name}",
                    data=file_bytes,
                    file_name=file_name,
                    mime="video/mp4"
                )
                
                # Nettoyage (Optionnel : supprime le fichier après lecture pour gagner de la place)
                # os.remove(file_path) 
            else:
                st.error("Le fichier n'a pas pu être créé.")
    else:
        st.warning("Veuillez coller un lien.")