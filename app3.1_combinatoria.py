import streamlit as st
import pandas as pd
import re
import google.generativeai as genai  # <--- Nueva librería

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Buscador de Diamantes con IA 💎", page_icon="💎")

# --- Configuración de Gemini ---
st.sidebar.header("Configuración de IA")
api_key = st.sidebar.text_input("Introduce tu Google API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Usamos gemini-2.0-flash (la versión más rápida y capaz disponible)
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- Función de Extracción Inteligente ---
@st.cache_data
def extraer_datos_inteligente(file):
    file.seek(0)
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
        if len(df.columns) < 2:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig')
    except:
        file.seek(0)
        df = pd.read_csv(file, sep=';', encoding='latin1')

    columnas_str = [str(c).strip() for c in df.columns]
    cabeceras_numericas = sum(c.isdigit() for c in columnas_str)
    
    if cabeceras_numericas >= 3:
        file.seek(0)
        df = pd.read_csv(file, header=None, encoding='utf-8-sig')

    resultados = []
    for index, row in df.iterrows():
        tupla = None
        puntuacion = "N/A"
        row_dict = row.to_dict()
        row_str = " ".join(str(v) for v in row_dict.values() if pd.notna(v))
        
        match = re.search(r'(\d{1,3}\s*-\s*){3,}\d{1,3}', row_str)
        if match:
            nums = [int(x.strip()) for x in match.group().split('-')]
            tupla = tuple(sorted(nums))
            for col_name, val in row_dict.items():
                if "puntua" in str(col_name).lower():
                    puntuacion = val
        else:
            nums = pd.to_numeric(row, errors='coerce').dropna().astype(int).tolist()
            nums_validos = sorted(list(set([n for n in nums if 0 <= n <= 60000])))
            if len(nums_validos) >= 4:
                tupla = tuple(nums_validos)
                
        if tupla:
            resultados.append({
                "Tupla": tupla,
                "Combinación": " - ".join(map(str, tupla)),
                "Puntuación Original (App 2)": puntuacion
            })
            
    return pd.DataFrame(resultados)

# --- Función para que Gemini analice los resultados ---
def analizar_con_ia(resumen_coincidencias, total_puros):
    if not api_key:
        return "⚠️ Por favor, introduce tu API Key en la barra lateral para activar el análisis de IA."
    
    prompt = f"""
    Eres un experto en análisis probabilístico y loterías. 
    He cruzado dos algoritmos de predicción y estos son los resultados:
    
    - Diamantes Puros (100% coincidencia): {total_puros}
    - Resumen de coincidencias parciales:
    {resumen_coincidencias}
    
    Por favor:
    1. Indica cuántas combinaciones hay con 5 aciertos y cuántas con 4 (si las hay).
    2. Explica qué significa esto en términos de confianza (si ambos algoritmos coinciden en 5 números, ¿es una señal fuerte?).
    3. Dame un consejo estratégico breve sobre qué combinaciones priorizar.
    
    Sé directo, profesional y usa emojis para resaltar lo importante.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al contactar con Gemini: {e}"

# --- Interfaz Principal ---
st.title("💎 Buscador Diamante + IA Gemini 2.0")

col1, col2 = st.columns(2)
with col1:
    file_app1 = st.file_uploader("App 1 (Base)", type=["csv", "txt"], key="app1")
with col2:
    file_app2 = st.file_uploader("App 2 (Candidatos)", type=["csv", "txt"], key="app2")

if file_app1 and file_app2:
    df1 = extraer_datos_inteligente(file_app1)
    df2 = extraer_datos_inteligente(file_app2)

    set1 = set(df1['Tupla'])
    set2 = set(df2['Tupla'])
    diamantes_puros = set1.intersection(set2)

    # --- Cálculo de Similitudes para la IA ---
    cercanos_data = []
    conteo_niveles = {5: 0, 4: 0, 3: 0} # Para el resumen de la IA
    
    for t2 in set2:
        for t1 in set1:
            comunes = len(set(t2).intersection(set(t1)))
            if comunes >= 3:
                if t2 not in diamantes_puros:
                    if comunes in conteo_niveles:
                        conteo_niveles[comunes] += 1
                    
                    if comunes >= 4: # Solo guardamos en tabla si es 4 o más
                        info = df2[df2['Tupla'] == t2].iloc[0]
                        cercanos_data.append({
                            "Coincidencias": comunes,
                            "Combinación": info["Combinación"],
                            "Puntuación": info["Puntuación Original (App 2)"]
                        })
                break

    # --- Sección de IA ---
    st.divider()
    st.header("🤖 Análisis Estratégico con Gemini 2.0 Flash")
    
    resumen_para_ia = f"- Con 5 números iguales: {conteo_niveles[5]}\n- Con 4 números iguales: {conteo_niveles[4]}\n- Con 3 números iguales: {conteo_niveles[3]}"
    
    if st.button("Generar Informe de IA"):
        with st.spinner("Gemini está analizando las tendencias..."):
            informe = analizar_con_ia(resumen_para_ia, len(diamantes_puros))
            st.markdown(informe)

    # --- Mostrar Tablas ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("💎 Diamantes Puros (100%)")
        st.write(f"Total: {len(diamantes_puros)}")
        if diamantes_puros:
            df_puros = df2[df2['Tupla'].isin(diamantes_puros)][['Combinación', 'Puntuación Original (App 2)']]
            st.dataframe(df_puros)

    with col_b:
        st.subheader("🔍 Coincidencias de 4 y 5 números")
        if cercanos_data:
            df_c = pd.DataFrame(cercanos_data).sort_values(by="Coincidencias", ascending=False)
            st.dataframe(df_c)
        else:
            st.write("No se encontraron coincidencias de 4 o 5 números.")
