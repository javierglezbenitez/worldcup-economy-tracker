import streamlit as st
import requests

import streamlit as st
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Analista IA — World Cup Economy Tracker",
    page_icon="🤖",
    layout="wide",
)

COLORS = {
    "gold": "#E8C84A",
    "green": "#2EA043",
    "red": "#F85149",
    "gray": "#8B949E",
    "bg": "#0D1117",
    "card": "#161B22",
}

st.markdown("# 🤖 Analista Económico IA")
st.markdown(
    "Pregúntame cualquier cosa sobre el impacto económico del Mundial 2026. "
    "Tengo acceso a datos en tiempo real de partidos, sponsors, noticias y correlaciones."
)
st.divider()

# ─────────────────────────────────────────
# PREGUNTAS SUGERIDAS
# ─────────────────────────────────────────
st.markdown("#### 💡 Preguntas sugeridas")

suggested = [
    "¿Cómo están cotizando los sponsors hoy?",
    "¿Qué correlaciones económicas se han detectado?",
    "¿Cuál es el sentimiento económico del Mundial?",
    "¿Qué equipos han generado más impacto en bolsa?",
    "¿Cómo afecta un gol al precio de las acciones de los sponsors?",
    "¿Qué sponsor se está beneficiando más del Mundial?",
]

cols = st.columns(3)
for i, question in enumerate(suggested):
    with cols[i % 3]:
        if st.button(question, key=f"suggested_{i}", use_container_width=True):
            st.session_state.pending_question = question

st.divider()

# ─────────────────────────────────────────
# INICIALIZAR HISTORIAL
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "¡Hola! Soy tu analista económico del Mundial 2026. 📊\n\n"
            "Puedo ayudarte a entender cómo el fútbol impacta en la economía: "
            "desde las cotizaciones de Adidas y Nike hasta el sentimiento de las "
            "noticias financieras y las correlaciones entre goles y mercados.\n\n"
            "¿Qué quieres analizar?"
        )
    })

# ─────────────────────────────────────────
# MOSTRAR HISTORIAL
# ─────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])

# ─────────────────────────────────────────
# INPUT DEL USUARIO
# ─────────────────────────────────────────
# Manejar pregunta sugerida
if "pending_question" in st.session_state:
    prompt = st.session_state.pending_question
    del st.session_state.pending_question
else:
    prompt = None

user_input = st.chat_input("Pregunta algo sobre la economía del Mundial...")

# Usar input del usuario o pregunta sugerida
final_prompt = user_input or prompt

if final_prompt:
    # Mostrar mensaje del usuario
    st.session_state.messages.append({
        "role": "user",
        "content": final_prompt
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(final_prompt)

    # Llamar al backend
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analizando datos del Mundial..."):
            try:
                # Historial sin el mensaje de bienvenida para no confundir al LLM
                history = [
                    m for m in st.session_state.messages[1:-1]
                    if m["role"] in ["user", "assistant"]
                ]

                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": final_prompt,
                        "history": history
                    },
                    timeout=30
                )
                answer = response.json()["response"]

            except requests.exceptions.Timeout:
                answer = "⏱️ La consulta tardó demasiado. Inténtalo de nuevo."
            except Exception as e:
                answer = f"❌ Error al conectar con el analista: {e}"

        st.markdown(answer)

    # Guardar respuesta en historial
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# ─────────────────────────────────────────
# SIDEBAR — INFO Y CONTROLES
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 Analista IA")
    st.divider()

    st.markdown("### 📊 Datos disponibles")
    try:
        health = requests.get(f"{API_URL}/health", timeout=3).json()
        st.markdown(f"- ⚽ **{health['matches_count']}** partidos")
        st.markdown(f"- 🎯 **{health['events_count']}** eventos")
        st.markdown(f"- 📈 **{health['snapshots_count']}** snapshots")
        st.markdown(f"- 📰 **{health['news_count']}** noticias")
    except Exception:
        st.warning("Backend no disponible")

    st.divider()

    st.markdown("### ⚙️ Controles")
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown("### 🧠 Modelo")
    st.markdown("""
    <div style="font-size: 13px; color: #8B949E;">
        <b style="color: white;">LLaMA 3.3 70B</b><br>
        via Groq API<br><br>
        Contexto actualizado con datos<br>
        en tiempo real del Mundial
    </div>
    """, unsafe_allow_html=True)