import streamlit as st
import pandas as pd
import re
import google.generativeai as genai

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Buscador de Diamantes con IA 💎", page_icon="💎")

# --- Gestión de API Key con Session State (evita perderla en recargas) ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ Configuración de IA")
    api_input = st.text_input("Google API Key:", type="password", value=st.session_state.api_key)
    if api_input != st.session_state.api_key:
        st.session_state.api_key = api_input
        if api_input:
            try:
                genai.configure(api_key=api_input)
                st.session_state.model = genai.GenerativeModel('gemini-2.0-flash')
                st.success("✅ Gemini conectado correctamente")
            except Exception as e:
                st.error(f"❌ Error al configurar Gemini: {e}")
                st.session_state.model = None

# --- Función de Extracción Optimizada ---
@st.cache_data(ttl=3600)
def extraer_datos_inteligente(file):
    file.seek(0)
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(file, encoding=enc, on_bad_lines='skip')
            break
        except Exception:
            file.seek(0)
            
    if df is None:
        st.error("❌ No se pudo leer el archivo. Verifica el formato CSV/TXT.")
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]
    
    # Si las cabeceras son puramente numéricas, asumimos que no hay header
    if df.columns.str.isdigit().sum() >= 3:
        file.seek(0)
        df = pd.read_csv(file, header=None, encoding='utf-8-sig', on_bad_lines='skip')

    resultados = []
    col_puntuacion = next((c for c in df.columns if "puntua" in str(c).lower()), None)

    for _, row in df.iterrows():
        row_str = " ".join(str(v) for v in row.dropna())
        match = re.search(r'(?:\d{1,3}\s*-\s*){3,}\d{1,3}', row_str)
        
        if match:
            nums = sorted(map(int, re.findall(r'\d+', match.group())))
        else:
            nums = sorted(pd.to_numeric(row, errors='coerce').dropna().astype(int).tolist())
            nums = [n for n in nums if 0 <= n <= 60000]
            
        if len(nums) >= 4:
            tupla = tuple(nums)
            puntuacion = row[col_puntuacion] if col_puntuacion and pd.notna(row[col_puntuacion]) else "N/A"
            resultados.append({
                "Tupla": tupla,
                "Combinación": " - ".join(map(str, tupla)),
                "Puntuación Original (App 2)": puntuacion
            })
            
    return pd.DataFrame(resultados)

# --- Función IA Optimizada ---
def analizar_con_ia(resumen_coincidencias, total_puros):
    model = st.session_state.get("model")
    if not model:
        return "⚠️ Configura una API Key válida en la barra lateral para activar el análisis."
    
    prompt = f"""
    Eres un experto en análisis probabilístico y loterías. 
    He cruzado dos algoritmos de predicción y estos son los resultados:
    
    - Diamantes Puros (100% coincidencia): {total_puros}
    - Resumen de coincidencias parciales:
    {resumen_coincidencias}
    
    Por favor:
    1. Indica cuántas combinaciones hay con 5 aciertos y cuántas con 4.
    2. Explica qué significa esto en términos de confianza estadística.
    3. Dame un consejo estratégico breve sobre qué combinaciones priorizar.
    
    Sé directo, profesional y usa emojis para resaltar lo importante. Máximo 150 palabras.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error en la API: {e}"

# --- Interfaz Principal ---
st.title("💎 Buscador Diamante + IA Gemini 2.0")

col1, col2 = st.columns(2)
with col1:
    file_app1 = st.file_uploader("📂 App 1 (Base)", type=["csv", "txt"], key="app1")
with col2:
    file_app2 = st.file_uploader("📂 App 2 (Candidatos)", type=["csv", "txt"], key="app2")

if file_app1 and file_app2:
    with st.spinner("🔄 Procesando archivos..."):
        df1 = extraer_datos_inteligente(file_app1)
        df2 = extraer_datos_inteligente(file_app2)

    if df1.empty or df2.empty:
        st.warning("⚠️ No se extrajeron datos válidos. Revisa el formato de los archivos.")
        st.stop()

    set1 = set(df1['Tupla'])
    set2 = set(df2['Tupla'])
    diamantes_puros = set1.intersection(set2)

    # Cálculo eficiente de coincidencias parciales
    cercanos_data = []
    conteo_niveles = {5: 0, 4: 0, 3: 0}
    set1_list = [set(t) for t in set1]

    for t2 in set2:
        t2_set = set(t2)
        mejores_comunes = 0
        for s1 in set1_list:
            comunes = len(t2_set & s1)
            if comunes > mejores_comunes:
                mejores_comunes = comunes
                if mejores_comunes >= 5: break # Optimización: no puede ser mayor que 5
        
        if 3 <= mejores_comunes <= 5:
            conteo_niveles[mejores_comunes] += 1
            if mejores_comunes >= 4:
                info = df2[df2['Tupla'] == t2].iloc[0]
                cercanos_data.append({
                    "Coincidencias": mejores_comunes,
                    "Combinación": info["Combinación"],
                    "Puntuación": info["Puntuación Original (App 2)"]
                })

    # --- Sección IA ---
    st.divider()
    st.header("🤖 Análisis Estratégico con Gemini 2.0 Flash")
    
    resumen_para_ia = f"- Con 5 números iguales: {conteo_niveles[5]}\n- Con 4 números iguales: {conteo_niveles[4]}\n- Con 3 números iguales: {conteo_niveles[3]}"
    
    if st.button("🧠 Generar Informe de IA", type="primary"):
        with st.spinner("Gemini está analizando las tendencias..."):
            informe = analizar_con_ia(resumen_para_ia, len(diamantes_puros))
            st.markdown(informe)

    # --- Mostrar Tablas ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("💎 Diamantes Puros (100%)")
        st.metric("Total", len(diamantes_puros))
        if diamantes_puros:
            df_puros = df2[df2['Tupla'].isin(diamantes_puros)][['Combinación', 'Puntuación Original (App 2)']].copy()
            st.dataframe(df_puros, use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("🔍 Coincidencias de 4 y 5 números")
        if cercanos_data:
            df_c = pd.DataFrame(cercanos_data).sort_values(by="Coincidencias", ascending=False)
            st.dataframe(df_c, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ No se encontraron coincidencias de 4 o 5 números.")
