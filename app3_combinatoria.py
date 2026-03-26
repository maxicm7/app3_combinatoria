import streamlit as st
import pandas as pd
import re

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Buscador de Diamantes 💎", page_icon="💎")

# --- Función de Extracción Mágica (Anti-Errores) ---
@st.cache_data
def extraer_datos_inteligente(file):
    """Lee el archivo sin importar cómo se guardó (sin cabeceras, en columnas o con guiones)."""
    file.seek(0)
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
        if len(df.columns) < 2:
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig')
    except:
        file.seek(0)
        df = pd.read_csv(file, sep=';', encoding='latin1')

    # Detectar si la primera fila (las cabeceras) son en realidad números (Tu error)
    columnas_str = [str(c).strip() for c in df.columns]
    cabeceras_numericas = sum(c.isdigit() for c in columnas_str)
    
    # Si detecta que los títulos son números, recarga el archivo asumiendo que NO hay títulos
    if cabeceras_numericas >= 3:
        file.seek(0)
        df = pd.read_csv(file, header=None, encoding='utf-8-sig')
        if len(df.columns) < 2:
            file.seek(0)
            df = pd.read_csv(file, sep=';', header=None, encoding='utf-8-sig')

    resultados = []
    
    for index, row in df.iterrows():
        tupla = None
        puntuacion = "N/A"
        
        row_dict = row.to_dict()
        # Unir toda la fila en un solo texto gigante para buscar
        row_str = " ".join(str(v) for v in row_dict.values() if pd.notna(v))
        
        # 1er Intento: Buscar si la combinación viene con guiones (Ej: "7 - 15 - 16 - 24")
        match = re.search(r'(\d{1,3}\s*-\s*){3,}\d{1,3}', row_str)
        if match:
            nums = [int(x.strip()) for x in match.group().split('-')]
            tupla = tuple(sorted(nums))
            
            # Intentar rescatar la Puntuación de la App 2 si existe
            for col_name, val in row_dict.items():
                if "puntua" in str(col_name).lower():
                    puntuacion = val
        else:
            # 2do Intento: Si no hay guiones, asumir que están en diferentes columnas (Tu archivo)
            nums = pd.to_numeric(row, errors='coerce').dropna().astype(int).tolist()
            # Filtrar números válidos de lotería (evitar años o decimales)
            nums_validos = sorted(list(set([n for n in nums if 0 <= n <= 60000)))
            
            if len(nums_validos) >= 4:
                tupla = tuple(nums_validos)
                
        if tupla:
            resultados.append({
                "Tupla": tupla,
                "Combinación": " - ".join(map(str, tupla)),
                "Puntuación Original (App 2)": puntuacion
            })
            
    return pd.DataFrame(resultados)

# --- Interfaz Principal ---
st.title("💎 El Buscador de Combinaciones Diamante")
st.markdown("Cruza los resultados de tus dos algoritmos para encontrar la **perfección probabilística**.")

st.header("1. Sube tus Resultados")
col1, col2 = st.columns(2)

with col1:
    st.info("📦 **Paso 1:** Sube el CSV de resultados de la **App 1**.")
    file_app1 = st.file_uploader("Resultados App 1", type=["csv", "txt", "xlsx"], key="app1")

with col2:
    st.success("🔥 **Paso 2:** Sube el CSV de resultados de la **App 2**.")
    file_app2 = st.file_uploader("Resultados App 2", type=["csv", "txt", "xlsx"], key="app2")

if file_app1 is not None and file_app2 is not None:
    with st.spinner("Analizando archivos mágicamente..."):
        df1 = extraer_datos_inteligente(file_app1)
        df2 = extraer_datos_inteligente(file_app2)

    if df1.empty:
        st.error("No se detectaron combinaciones numéricas en el archivo de la App 1.")
        st.stop()
    if df2.empty:
        st.error("No se detectaron combinaciones numéricas en el archivo de la App 2.")
        st.stop()

    set1 = set(df1['Tupla'])
    set2 = set(df2['Tupla'])

    st.divider()
    st.header("2. Análisis de Intersección")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Combos Válidos Extraídos (App 1)", len(set1))
    c2.metric("Combos Válidos Extraídos (App 2)", len(set2))
    
    diamantes_puros = set1.intersection(set2)
    c3.metric("💎 Diamantes Puros", len(diamantes_puros))

    # --- MOSTRAR DIAMANTES PUROS ---
    if len(diamantes_puros) > 0:
        st.balloons()
        st.subheader("💎 Diamantes Puros (Coincidencia 100%)")
        df_diamantes = df2[df2['Tupla'].isin(diamantes_puros)].copy()
        df_diamantes = df_diamantes.drop(columns=['Tupla'])
        st.dataframe(df_diamantes, use_container_width=True)
    else:
        st.warning("No hubo coincidencias exactas del 100%. Busca similitudes abajo.")

    st.divider()

    # --- MOSTRAR DIAMANTES CERCANOS ---
    st.subheader("🔍 Diamantes Cercanos (Alta Similitud)")
    st.markdown("Busca combinaciones recomendadas (App 2) que se parezcan casi al 100% a la estructura matriz (App 1).")
    
    n_numeros = len(list(set1)[0]) if len(set1) > 0 else 6
    umbral = st.slider(f"¿Cuántos números en común quieres exigir? (Max {n_numeros})", 3, n_numeros, n_numeros-1)

    cercanos_data = []
    with st.spinner("Cruzando datos..."):
        for t2 in set2:
            if t2 in diamantes_puros: continue
            for t1 in set1:
                comunes = len(set(t2).intersection(set(t1)))
                if comunes >= umbral:
                    # Extraer info de df2
                    info = df2[df2['Tupla'] == t2].iloc[0]
                    cercanos_data.append({
                        "Recomendada (App 2)": info["Combinación"],
                        "Números en Común": comunes,
                        "Base Estructural (App 1)": " - ".join(map(str, t1)),
                        "Puntuación": info["Puntuación Original (App 2)"]
                    })
                    break # Pasamos al siguiente t2

    if cercanos_data:
        df_cercanos = pd.DataFrame(cercanos_data)
        if 'Puntuación' in df_cercanos.columns and pd.api.types.is_numeric_dtype(df_cercanos['Puntuación']):
            df_cercanos = df_cercanos.sort_values(by=['Números en Común', 'Puntuación'], ascending=[False, False])
        else:
            df_cercanos = df_cercanos.sort_values(by=['Números en Común'], ascending=[False])

        st.success(f"Se encontraron **{len(df_cercanos)}** combinaciones similares.")
        st.dataframe(df_cercanos.reset_index(drop=True), use_container_width=True)
    else:
        st.error("No se encontraron combinaciones similares. Intenta bajar el umbral del slider.")
