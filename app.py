import streamlit as st
from groq import Groq
import os
import base64
from PIL import Image
from io import BytesIO
from streamlit_paste_button import paste_image_button

# Configurazione della pagina
st.set_page_config(page_title="AI Coding Assistant", layout="wide")
st.title("🖥️ Il tuo Assistente Programmer ibrido (Text & Vision)")

# --- Configurazione Sidebar ---
with st.sidebar:
    st.header("Configurazione")
    # Puoi dinamizzare anche qui la lingua/ruolo runtime
    ruolo_esperto = st.selectbox("L'AI è un esperto in:", ["Python & Debugging", "Web Development", "DevOps"])
    api_key = st.text_input("Inserisci Groq API Key:", type="password")
    
    st.markdown("---")
    st.warning("⚠️ Per le immagini verrà usato Llama-3.2-Vision (velocissimo), per il testo puro Llama-3.3-70B.")

# --- Helper function: Codifica immagine per l'API ---
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG") # Assicuriamoci sia PNG per compatibilità
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- Inizializzazione Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_to_process" not in st.session_state:
    st.session_state.image_to_process = None

# Mostra lo storico della chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], caption="Screenshot allegato")

# --- UI per Input (Tasto Incolla & Chat Input) ---

# Area per incollare l'immagine (in alto)
paste_result = paste_image_button(
    label="📋 Premi CTRL+V qui per incollare uno Screenshot",
    errors="ignore"
)

# Se l'utente ha incollato qualcosa, lo memorizziamo temporaneamente
if paste_result.image_data is not None:
    st.session_state.image_to_process = paste_result.image_data
    st.image(st.session_state.image_to_process, caption="Immagine pronta", width=200)

# Chat input classico (sempre visibile)
prompt = st.chat_input("Fai la tua domanda sul codice...")

# --- Logica di Processing ---
if prompt and api_key:
    client = Groq(api_key=api_key)
    system_msg = f"Sei un esperto in {ruolo_esperto}. Rispondi sempre in Italiano."
    
    # 1. Recuperiamo l'eventuale immagine memorizzata
    pasted_img = st.session_state.image_to_process
    
    # 2. Mostriamo il messaggio dell'utente nella UI
    with st.chat_message("user"):
        st.markdown(prompt)
        if pasted_img:
            st.image(pasted_img, caption="Screenshot allegato")
    
    # Aggiungiamo alla session state
    user_msg_for_state = {"role": "user", "content": prompt}
    if pasted_img:
        user_msg_for_state["image"] = pasted_img # Salviamo PIL image per UI locale
    st.session_state.messages.append(user_msg_for_state)

    # 3. ROUTING: Chiamata API Groq
    with st.chat_message("assistant"):
        with st.spinner("Analizzando..."):
            
            try:
                # --- CASO A: C'è un'immagine (Usiamo Llama Vision) ---
                if pasted_img:
                    base64_image = encode_image(pasted_img)
                    model_to_use = "llama-3.2-11b-vision-preview" # Ottimo per debugging su screenshot
                    
                    messages = [
                        {"role": "system", "content": system_msg},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ]
                
                # --- CASO B: Testo Puro (Usiamo Llama 3.3 70B) ---
                else:
                    model_to_use = "llama-3.3-70b-versatile"
                    # Qui dovresti passare anche lo storico (saltato per brevità)
                    messages = [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt}
                    ]

                # Chiamata API unica
                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.1
                )
                
                # Gestione risposta
                full_response = response.choices[0].message.content
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Reset dell'immagine dopo l'uso
                st.session_state.image_to_process = None
                
            except Exception as e:
                st.error(f"Errore API Groq: {e}")

elif prompt and not api_key:
    st.warning("Per favore inserisci la tua API Key nella sidebar.")
