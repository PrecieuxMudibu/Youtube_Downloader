import streamlit as st
import yt_dlp
import os
import re

# Configuration de la page
st.set_page_config(page_title="Téléchargeur YouTube (Pro)", layout="centered")

def download_video_local(url, quality_choice):
    # Création du dossier temporaire
    output_folder = "downloads_temp"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Nettoyage du dossier temporaire
    for f in os.listdir(output_folder):
        try:
            os.remove(os.path.join(output_folder, f))
        except:
            pass

    # Configuration de la hauteur max
    if "Best" in quality_choice:
        height_limit = 2160
    else:
        height_limit = int(quality_choice.replace('p', ''))

    # --- ÉLÉMENTS D'INTERFACE POUR LA PROGRESSION ---
    # On crée ces éléments AVANT le téléchargement pour pouvoir les mettre à jour
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    # --- FONCTION DE RAPPEL (HOOK) ---
    # Cette fonction est appelée par yt-dlp à chaque étape du téléchargement
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                # 1. Calcul du pourcentage
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes:
                    percentage = downloaded_bytes / total_bytes
                else:
                    percentage = 0
                
                # 2. Mise à jour de la barre (entre 0.0 et 1.0)
                progress_bar.progress(min(percentage, 1.0))
                
                # 3. Mise à jour du texte (ex: "45.2% ...")
                # On nettoie les codes couleurs ANSI que yt-dlp met parfois dans les strings
                percent_str = f"{percentage:.1%}"
                eta = d.get('_eta_str', '??')
                speed = d.get('_speed_str', '??')
                
                progress_text.markdown(f"**Téléchargement en cours...** `{percent_str}` | Vitesse: `{speed}` | Restant: `{eta}`")
                
            except Exception as e:
                # En cas d'erreur d'affichage, on continue le téléchargement sans planter
                pass
                
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)
            progress_text.success("✅ Téléchargement terminé ! Traitement final en cours...")

    # Configuration de yt-dlp
    ydl_opts = {
        'format': f'best[ext=mp4][height<={height_limit}]/best[ext=mp4]/best',
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s', 
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': True,
        'overwrites': True,
        
        # --- AJOUT CRITIQUE POUR CONTOURNER LE BLOCAGE YOUTUBE ---
        # 1. Forcer l'utilisation d'IPv4 (souvent nécessaire en cloud)
        'force_ipv4': True,
        # 2. Contourner les restrictions géographiques via un pays non bloqué (ex: DE)
        'geo_bypass_country': 'DE', 
        # --------------------------------------------------------
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Téléchargement
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Vérification du fichier final (au cas où l'extension change)
            if not os.path.exists(filename):
                base_name = os.path.splitext(filename)[0]
                for f in os.listdir(output_folder):
                    if base_name in os.path.join(output_folder, f):
                        filename = os.path.join(output_folder, f)
                        break
            
            return filename, os.path.basename(filename)

    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return None, None

# --- Interface Utilisateur ---
st.title("🚀 Téléchargeur YouTube")
st.markdown("Téléchargez des vidéos complètes (Video + Audio) prêtes à être lues hors ligne.")

url = st.text_input("Collez l'URL YouTube ici :", placeholder="https://www.youtube.com/watch?v=...")
col1, col2 = st.columns([1, 2])
with col1:
    quality = st.selectbox("Qualité :", ["1080p","720p", "360p", "Best"])
with col2:
    st.write("") # Espacement

if st.button("Lancer le téléchargement", type="primary"):
    if url:
        # On n'utilise pas st.spinner ici car on a notre propre barre de progression
        file_path, file_name = download_video_local(url, quality)
        
        if file_path and os.path.exists(file_path):
            
            # Lecture du fichier pour le bouton
            with open(file_path, "rb") as file:
                file_bytes = file.read()
                
            st.download_button(
                label=f"💾 Cliquez ici pour enregistrer la vidéo ({len(file_bytes)/(1024*1024):.1f} Mo)",
                data=file_bytes,
                file_name=file_name,
                mime="video/mp4"
            )
            st.balloons()
    else:
        st.warning("Veuillez entrer une URL.")