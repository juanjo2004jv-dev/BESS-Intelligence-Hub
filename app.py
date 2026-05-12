import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from fpdf import FPDF
from duckduckgo_search import DDGS
import google.generativeai as genai

# ==========================================
# CONFIGURACIÓN
# ==========================================
GEMINI_API_KEY = "TU_CLAVE_GRATUITA_AQUI"
genai.configure(api_key=GEMINI_API_KEY)
DB_NAME = "bess_intelligence.db"

st.set_page_config(page_title="BESS-PV SPAIN INTELLIGENCE HUB", layout="wide")
st.markdown("<style>.reportview-container { background-color: #121212; color: #E0E0E0; }</style>", unsafe_allow_html=True)

# ==========================================
# BASE DE DATOS
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS insights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, title TEXT, analysis TEXT)''')
    conn.commit()
    conn.close()

def get_recent_insights():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM insights ORDER BY date DESC", conn)
    conn.close()
    return df

# ==========================================
# MOTOR DE INTELIGENCIA GRATUITO (DDGS + GEMINI)
# ==========================================
def fetch_free_intelligence(topic):
    if GEMINI_API_KEY == "TU_CLAVE_GRATUITA_AQUI":
        return "⚠️ Error: Necesitas poner tu clave gratuita de Gemini en el código."
    
    # 1. Buscar noticias recientes gratis
    resultados_busqueda = ""
    with DDGS() as ddgs:
        for r in ddgs.text(f"Noticias España {topic} fotovoltaica almacenamiento BESS", max_results=5):
            resultados_busqueda += f"Título: {r['title']}\nResumen: {r['body']}\n\n"
            
    # 2. Analizar con IA gratis
    prompt = f"""
    Eres un Ingeniero Senior experto en el sector eléctrico español. Analiza estas noticias recientes sobre {topic}:
    {resultados_busqueda}
    
    Redacta un informe técnico, directo y neutral. Incluye un 'Módulo de Analogía Internacional' comparando la situación con Australia o Alemania.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        respuesta = model.generate_content(prompt)
        return respuesta.text
    except Exception as e:
        return f"Error al generar el análisis: {e}"

# ==========================================
# INTERFAZ
# ==========================================
init_db()
st.title("🔋 BESS-PV SPAIN INTELLIGENCE HUB")

action = st.sidebar.radio("Navegación", ["Dashboard Principal", "Generar Nueva Inteligencia"])

if action == "Dashboard Principal":
    st.subheader("Últimos Informes")
    df_insights = get_recent_insights()
    
    if not df_insights.empty:
        for index, row in df_insights.iterrows():
            st.markdown(f"### {row['title']} ({row['date']})")
            st.write(row['analysis'])
            st.markdown("---")
    else:
        st.info("No hay datos. Ve a 'Generar Nueva Inteligencia'.")

elif action == "Generar Nueva Inteligencia":
    topic = st.selectbox("Foco de análisis:", ["Cambios Regulatorios (BOE/CNMC)", "Mercado Mayorista (OMIE/ESIOS)"])
    if st.button("Ejecutar Análisis y Guardar"):
        with st.spinner("Buscando noticias y analizando..."):
            resultado = fetch_free_intelligence(topic)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO insights (date, category, title, analysis) VALUES (?, ?, ?, ?)",
                      (datetime.now().strftime('%Y-%m-%d'), topic, f"Reporte: {topic}", resultado))
            conn.commit()
            conn.close()
            st.success("Guardado correctamente.")