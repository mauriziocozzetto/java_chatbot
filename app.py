import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# --- 1. CONFIGURAZIONE INIZIALE ---
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    try:
        if "GROQ_API_KEY" in st.secrets:
            GROQ_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        GROQ_KEY = None

if not GROQ_KEY:
    st.error("⚠️ Chiave API non trovata! Controlla il file .env o i Secrets.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 2. LOGICA DI ROUTING AUTOMATICO ---
def get_automatic_model(user_query):
    """Analizza il prompt e restituisce l'ID del modello più adatto."""
    query = user_query.lower()
    # Se la richiesta riguarda correzioni o ottimizzazioni
    if any(word in query for word in ["debug", "errore", "fix", "ottimizza", "correggi"]):
        return "groq/compound"
    # Se la richiesta riguarda esplicitamente il mondo dei dati
    if any(word in query for word in ["python", "data", "ml", "deep", "pandas", "sklearn", "torch", "tensorflow"]):
        return "qwen/qwen3-32b"
    # Default per architetture e logica generale (Java)
    return "openai/gpt-oss-120b"

# --- 3. SYSTEM PROMPT IBRIDO ---
# Questo assicura che il modello sappia QUALE linguaggio usare in base al contesto
hybrid_system_prompt = (
    "Sei un assistente tecnico Senior. Il tuo comportamento varia in base al dominio:\n"
    "1. DATA SCIENCE/ML: Se la richiesta riguarda dati, analisi o Machine Learning, usa PYTHON. "
    "Spiega la logica matematica e le metriche.\n"
    "2. ALTRI PROGETTI: Per software engineering, algoritmi o backend, usa JAVA 17+. "
    "Segui i principi SOLID e i design pattern.\n"
    "Rispondi sempre in italiano e usa commenti chiari nel codice."
)

# --- 4. SIDEBAR E INTERFACCIA ---
st.set_page_config(page_title="AI Smart Orchestrator", page_icon="🤖")

with st.sidebar:
    st.header("⚙️ Configurazione")
    
    model_map = {
        "Auto-Select (Intelligente)": "auto",
        "GPT-OSS 120B (Architetto)": "openai/gpt-oss-120b",
        "Groq Compound (Validatore)": "groq/compound",
        "Qwen 3 32B (Specialista Coding)": "qwen/qwen3-32b",
        "Llama 3.3 70B (Versatile)": "llama-3.3-70b-versatile"
    }
    
    selected_option = st.selectbox("Scegli il modello:", list(model_map.keys()))
    user_choice = model_map[selected_option]
    
    temp = st.slider("Temperatura (Creatività)", 0.0, 1.0, 0.2, 0.05)
    
    if st.button("🗑️ Reset Conversazione"):
        st.session_state["messages"] = [{"role": "system", "content": hybrid_system_prompt}]
        st.rerun()

st.title("🤖 AI Smart Orchestrator")
st.info("L'AI sceglierà automaticamente tra Java e Python in base alla tua richiesta.")

# Inizializzazione cronologia
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": hybrid_system_prompt}]

# Mostra i messaggi precedenti
for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 5. GESTIONE INPUT E RISPOSTA ---
if prompt := st.chat_input("Chiedi un algoritmo, un fix o un'analisi dati..."):
    
    # Determinazione del modello da usare
    if user_choice == "auto":
        actual_model = get_automatic_model(prompt)
        model_label = f"Auto-selected: {actual_model}"
    else:
        actual_model = user_choice
        model_label = f"Manuale: {actual_model}"

    # Aggiunta messaggio utente
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generazione risposta dell'assistente
    with st.chat_message("assistant"):
        st.caption(f"🚀 Modello in uso: `{actual_model}`")
        
        try:
            def response_generator():
                stream = client.chat.completions.create(
                    model=actual_model,
                    messages=st.session_state["messages"],
                    temperature=temp,
                    stream=True,
                )
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content

            full_response = st.write_stream(response_generator())
            st.session_state["messages"].append({"role": "assistant", "content": full_response})

            # Bottone di download per il codice generato
            st.download_button(
                label="📥 Scarica Codice",
                data=full_response,
                file_name="soluzione_tecnica.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Errore durante la chiamata a Groq: {e}")
