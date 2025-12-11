# app.py - Téléchargeur Vidéo YouTube avec Streamlit et yt-dlp

import streamlit as st
import io
import re
import yt_dlp # Le téléchargeur robuste
import requests # Pour télécharger l'URL directe dans la mémoire
import os

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Téléchargeur Vidéo YouTube (yt-dlp)",
    layout="centered"
)

def download_video(url):
    """
    Utilise yt-dlp pour extraire l'URL de téléchargement directe de la meilleure qualité MP4,
    puis utilise requests pour télécharger le contenu dans un buffer in-memory.
    """
    
    # 1. LOGIQUE DE NETTOYAGE D'URL (Essentiel pour enlever les paramètres de playlist)
    video_id_match = re.search(r'(?<=v=)[^&]+', url)
    if video_id_match:
        # Reconstruit l'URL avec uniquement le paramètre 'v'
        cleaned_url = f"https://www.youtube.com/watch?v={video_id_match.group(0)}"
        url = cleaned_url
        st.info(f"URL nettoyée utilisée : `{url}`")
    
    try:
        # Configuration de yt-dlp pour obtenir les informations sans télécharger
        ydl_opts = {
            # Préfère le meilleur format vidéo + audio, puis la meilleure qualité MP4.
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
            'noplaylist': True, # Ne traite pas les playlists
            'quiet': True,       # Supprime la sortie de yt-dlp
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extrait les métadonnées et les liens de téléchargement SANS télécharger le fichier
            info_dict = ydl.extract_info(url, download=False)
            
            # --- 2. TROUVER L'URL DIRECTE ET LE NOM DE FICHIER ---
            
            # Le format de yt-dlp peut varier. On cherche le meilleur flux téléchargeable.
            best_format = None
            if 'formats' in info_dict:
                # Cherche spécifiquement un format MP4
                for f in info_dict['formats']:
                    # S'assure qu'il s'agit d'un flux vidéo (vcodec != 'none') et d'un MP4
                    if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                        best_format = f
                        break
            
            # Si aucun MP4 trouvé directement (cela peut arriver), on prend le meilleur lien principal
            if best_format is None:
                video_url_direct = info_dict.get('url')
            else:
                video_url_direct = best_format.get('url')

            if not video_url_direct:
                st.error("Impossible de trouver un lien de téléchargement direct. Vidéo restreinte ?")
                return None, None
            
            # Définition du nom de fichier propre
            filename = f"{info_dict.get('title', 'video').replace('/', '_').replace(':', ' -')}.mp4"
            
            st.info(f"Préparation au téléchargement de : **{info_dict.get('title')}**")

            # --- 3. TÉLÉCHARGEMENT DANS LA MÉMOIRE AVEC REQUESTS ---
            st.warning("Téléchargement en cours. Cela peut prendre du temps pour les gros fichiers...")
            
            # Télécharge le contenu du lien direct dans la mémoire
            response = requests.get(video_url_direct, stream=True, timeout=300) # 5 min de timeout
            print (f"{response}")
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
            
            # Utilise io.BytesIO pour créer un buffer en mémoire
            buffer = io.BytesIO(response.content)
            buffer.seek(0)
            
            return buffer.getvalue(), filename
            
    except Exception as e:
        st.error(f"Une erreur s'est produite avec yt-dlp : {e}")
        st.error("Veuillez vérifier l'URL ou vous assurer que la vidéo n'est pas privée/géobloquée.")
        return None, None


# --- Interface Utilisateur Streamlit ---
st.title("⬇️ Téléchargeur de Vidéos YouTube")
st.markdown("Collez l'URL de la vidéo YouTube que vous souhaitez télécharger (propulsé par `yt-dlp`).")

# Champ de saisie pour l'URL
youtube_url = st.text_input("URL YouTube", placeholder="Ex: https://www.youtube.com/watch?v=vMOh4oBD8VQ")

if youtube_url:
    # Bouton de téléchargement
    if st.button("Obtenir la Vidéo"):
        # Ajout d'une vérification basique du format de l'URL
        if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            st.error("Veuillez entrer une URL YouTube valide.")
        else:
            with st.spinner('Extraction des liens et téléchargement en cours...'):
                video_bytes, filename = download_video(youtube_url)
                
                # ... à l'intérieur de 'if st.button("Obtenir la Vidéo"):'

                if video_bytes:
                    st.success("Vidéo téléchargée avec succès !")
                    
                    # Bouton Streamlit pour déclencher le téléchargement côté client
                    st.download_button(
                        label=f"Télécharger le fichier : {filename}",
                        data=video_bytes,
                        file_name=filename,
                        mime="video/mp4" 
                    )

                    st.balloons()
                else:
                    # Ce bloc s'exécute si video_bytes est None (téléchargement échoué)
                    pass
                    
                    # Bouton

