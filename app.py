import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# --- 1. CARICAMENTO CHIAVE API ---
load_dotenv()

GROQ_KEY = None
try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not GROQ_KEY:
    GROQ_KEY = os.getenv("GROQ_API_KEY")

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Java Expert Assistant", layout="wide", page_icon="☕")
st.title("☕ Java Expert Pro")

if not GROQ_KEY:
    st.error("⚠️ Chiave API non trovata!")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 3. SIDEBAR: AGGIUNTA DEEPSEEK-R1 ---
with st.sidebar:
    st.header("Configurazione")
    
    # Abbiamo aggiunto DeepSeek-R1 alla lista
    model_option = st.selectbox(
        "Scegli il modello:",
        (
            "DeepSeek-R1 (Ragionamento Puro)", 
            "Llama 3.3 70B (Architetto)", 
            "Qwen 3 32B (Chirurgo del Codice)"
        ),
        help="DeepSeek-R1 è ideale per risolvere bug complessi e problemi di logica."
    )
    
    # Mappatura degli ID modelli corretti per Groq
    model_map = {
        "DeepSeek-R1 (Ragionamento Puro)": "deepseek-r1-distill-llama-70b",
        "Llama 3.3 70B (Architetto)": "llama-3.3-70b-versatile",
        "Qwen 3 32B (Chirurgo del Codice)": "qwen-2.5-72b" # Nota: ID aggiornato per Qwen su Groq
    }
    
    selected_model = model_map[model_option]
    
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

for message in st.session_state["messages"]:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 5. INTERAZIONE E GENERAZIONE ---
if prompt := st.chat_input("Chiedi qualcosa su Java..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
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
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            
            st.download_button(
                label="📥 Scarica Codice",
                data=full_response,
                file_name="soluzione_java.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"Si è verificato un errore con le API di Groq: {e}")
