import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()

# Recupera la chiave dalle variabili di sistema
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Configurazione della pagina
st.set_page_config(page_title="Java Expert Assistant",
                   layout="wide", page_icon="☕")
st.title("☕ Java Expert: Llama-3.3-70b")

# Inizializzazione Client Groq con gestione errore chiave mancante
if not GROQ_KEY:
    st.error("Errore: GROQ_API_KEY non trovata nel file .env!")
    st.stop()

client = Groq(api_key=GROQ_KEY)

with st.sidebar:
    st.header("Configurazione Java")

    selected_model = "llama-3.3-70b-versatile"
    st.info(f"Modello in uso: \n{selected_model}")

    st.subheader("Configurazione AI")
    java_system_prompt = (
        "Sei un esperto Senior Java Developer e Software Architect. "
        "Il tuo compito è generare codice Java moderno (Java 17+), robusto e ben strutturato. "
        "Per ogni richiesta: 1. Fornisci il codice completo e pronto alla compilazione. "
        "2. Spiega brevemente il pattern di design o la logica utilizzata. "
        "3. Includi sempre esempi di test (JUnit) o una classe Main per il test. "
        "Rispondi sempre in italiano e usa commenti chiari nel codice."
    )

    temp = st.slider("Precisione (Temperatura)", 0.0, 1.0, 0.2, 0.05)

    if st.button("🗑️ Nuova Sessione Java"):
        st.session_state["messages"] = []
        st.rerun()

# Inizializzazione cronologia messaggi
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": java_system_prompt}]

# Visualizzazione messaggi precedenti
for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Gestione Input Utente
if prompt := st.chat_input("Esempio: Implementa la classe OrologioDigitale con una Enum per gli stati"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        def response_generator():
            stream = client.chat.completions.create(
                model=selected_model,
                messages=st.session_state["messages"],
                temperature=temp,
                stream=True,
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        full_response = st.write_stream(response_generator())
        st.session_state["messages"].append(
            {"role": "assistant", "content": full_response})
