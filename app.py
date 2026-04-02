import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# --- 1. CARICAMENTO CHIAVE API (LOGICA UNIVERSALE) ---
load_dotenv()  # Cerca il file .env in locale

GROQ_KEY = None

# Tentativo A: Cerca nei Secrets di Streamlit (Cloud)
try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    # Se st.secrets non è disponibile (siamo in locale), non fare nulla
    pass

# Tentativo B: Se non trovata, cerca nelle variabili d'ambiente/file .env (Locale)
if not GROQ_KEY:
    GROQ_KEY = os.getenv("GROQ_API_KEY")

# --- 2. CONFIGURAZIONE PAGINA E CONTROLLO CHIAVE ---
st.set_page_config(page_title="Java Expert Assistant", layout="wide", page_icon="☕")
st.title("☕ Java Expert Pro")

if not GROQ_KEY:
    st.error("⚠️ Chiave API non trovata! \n\n"
             "Locale: Assicurati che il file .env contenga GROQ_API_KEY=tua_chiave\n\n"
             "Online: Inserisci GROQ_API_KEY nei Secrets di Streamlit Cloud.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 3. SIDEBAR: CONFIGURAZIONE MODELLO E AI ---
with st.sidebar:
    st.header("Configurazione")
    
    # Selezione tra i due modelli top del 2026
    model_option = st.selectbox(
        "Scegli il modello:",
        ("Llama 3.3 70B (Architetto)", "Qwen 3 32B (Chirurgo del Codice)"),
        help="Llama è ottimo per spiegazioni, Qwen è precisissimo nel coding puro."
    )
    
    selected_model = "llama-3.3-70b-versatile" if "Llama" in model_option else "qwen/qwen3-32b"
    
    st.subheader("Parametri AI")
    temp = st.slider("Precisione (Temperatura)", 0.0, 1.0, 0.2, 0.05)
    
    if st.button("🗑️ Nuova Sessione Java"):
        st.session_state["messages"] = []
        st.rerun()

# --- 4. GESTIONE CHAT E SYSTEM PROMPT ---
java_system_prompt = (
        "Sei un esperto Senior Java Developer e Software Architect. "
        "Il tuo compito è generare codice Java moderno (Java 17+), robusto e ben strutturato. "
        "Per ogni richiesta: 1. Fornisci il codice completo e pronto alla compilazione. "
        "2. Spiega brevemente il pattern di design o la logica utilizzata. "
        "3. Includi sempre esempi di test (JUnit) o una classe Main per il test. "
        "Rispondi sempre in italiano e usa commenti chiari nel codice."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": java_system_prompt}]

# Visualizza i messaggi della conversazione (escluso il system prompt)
for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 5. INTERAZIONE UTENTE E GENERAZIONE RISPOSTA ---
if prompt := st.chat_input("Esempio: Chiedi qualcosa su Java..."):
    # Aggiungi messaggio utente alla sessione
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generazione risposta dell'assistente
    with st.chat_message("assistant"):
        try:
            # Funzione generatrice per lo streaming
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

            # Visualizzazione streaming e salvataggio
            full_response = st.write_stream(response_generator())
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            
            # Pulsante per scaricare la risposta come file di testo
            st.download_button(
                label="📥 Scarica Codice",
                data=full_response,
                file_name="soluzione_java.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"Si è verificato un errore con le API di Groq: {e}")


