import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# 1. Caricamento configurazioni
# 1. Prova a caricare dal file .env (Locale)
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

# 2. Se non lo trova nel .env, prova nei Secrets di Streamlit (Cloud)
if not GROQ_KEY:
    try:
        # Usiamo .get per evitare il crash se la chiave manca,
        # ma avvolgiamo tutto in un try/except per sicurezza estrema
        if "GROQ_API_KEY" in st.secrets:
            GROQ_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        # Se anche i secrets danno errore o non esistono, GROQ_KEY resta None
        GROQ_KEY = None

# 3. Controllo finale
if not GROQ_KEY:
    st.error(
        "⚠️ Chiave API non trovata! Assicurati che il file .env contenga GROQ_API_KEY=tuachiave")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- SIDEBAR: CONFIGURAZIONE AVANZATA ---
with st.sidebar:
    st.header("Configurazione")

    # SUGGERIMENTO 2: Selezione dinamica del modello
    model_option = st.selectbox(
        "Scegli il modello:",
        ("Llama 3.3 70B (Architetto)", "Qwen 3 32B (Chirurgo del Codice)"),
        help="Llama è meglio per spiegazioni, Qwen è più preciso nel coding puro."
    )

    selected_model = "llama-3.3-70b-versatile" if "Llama" in model_option else "qwen/qwen3-32b"

    st.subheader("Parametri AI")
    temp = st.slider("Temperatura (Creatività)", 0.0, 1.0, 0.2, 0.05)

    if st.button("🗑️ Reset Conversazione"):
        st.session_state["messages"] = []
        st.rerun()

# --- LOGICA SYSTEM PROMPT ---
java_system_prompt = (
    "Sei un esperto Senior Java Developer e Software Architect. "
    "Il tuo compito è generare codice Java moderno (Java 17+), robusto e ben strutturato. "
    "Per ogni richiesta: 1. Fornisci il codice completo e pronto alla compilazione. "
    "2. Spiega brevemente il pattern di design o la logica utilizzata. "
    "3. Includi sempre esempi di test (JUnit) o una classe Main per il test. "
    "Rispondi sempre in italiano e usa commenti chiari nel codice."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": java_system_prompt}]

# Mostra cronologia
for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- GESTIONE INPUT E RISPOSTA ---
if prompt := st.chat_input("Chiedi qualcosa su Java..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # SUGGERIMENTO 1: Gestione Errori API (Try-Except)
        try:
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

            # SUGGERIMENTO 3: Pulsante di Download del codice
            st.download_button(
                label="📥 Scarica Codice/Risposta",
                data=full_response,
                file_name="risposta_java.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Si è verificato un errore con le API di Groq: {e}")
