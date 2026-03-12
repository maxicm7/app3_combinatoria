import streamlit as st
import pandas as pd

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Buscador de Diamantes 💎", page_icon="💎")

# --- Funciones Auxiliares Robustas ---
def parse_combinacion(combo_str):
    """Convierte un string '5 - 12 - 24' en una tupla (5, 12, 24)"""
    try:
        combo_str = str(combo_str).replace(',', ' - ')
        numeros = [int(n.strip()) for n in combo_str.split('-') if n.strip().isdigit()]
        if len(numeros) >= 4: 
            return tuple(sorted(numeros))
        return None
    except:
        return None

def cargar_csv_seguro(file):
    """Carga el CSV detectando automáticamente si usa coma o punto y coma."""
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
        if len(df.columns) < 2: # Si solo hay 1 columna, probablemente usa punto y coma
            file.seek(0)
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig')
        return df
    except Exception:
        file.seek(0)
        return pd.read_csv(file, sep=';', encoding='latin1')

def encontrar_columna_combinacion(df):
    """Busca la columna correcta inteligente, incluso si cambia de nombre."""
    # 1. Buscar por nombre
    for col in df.columns:
        if "combinaci" in str(col).lower() or "tupla" in str(col).lower() or "jugada" in str(col).lower():
            return col
    # 2. Buscar por contenido (Ej: si una celda tiene "1 - 5 - 14")
    for col in df.columns:
        if len(df) > 0:
            muestra = str(df[col].iloc[0])
            if "-" in muestra and any(c.isdigit() for c in muestra):
                return col
    return None

# --- Interfaz Principal ---
st.title("💎 El Buscador de Combinaciones Diamante")
st.markdown("Cruza los resultados de tus dos algoritmos para encontrar la **perfección probabilística**.")

st.header("1. Sube tus Resultados")
col1, col2 = st.columns(2)

with col1:
    st.info("📦 **Paso 1:** Sube el CSV de resultados de la **App 1** (Cascada/Genético).")
    file_app1 = st.file_uploader("Resultados App 1", type=["csv", "txt"], key="app1")

with col2:
    st.success("🔥 **Paso 2:** Sube el CSV de resultados de la **App 2** (Agente Dinámico / Top).")
    file_app2 = st.file_uploader("Resultados App 2", type=["csv", "txt"], key="app2")

if file_app1 is not None and file_app2 is not None:
    try:
        # Cargar con función segura anti-errores
        df1 = cargar_csv_seguro(file_app1)
        df2 = cargar_csv_seguro(file_app2)

        # Encontrar columnas dinámicamente
        col_combo_1 = encontrar_columna_combinacion(df1)
        col_combo_2 = encontrar_columna_combinacion(df2)

        if not col_combo_1:
            st.error(f"❌ No se encontró la columna de combinaciones en el archivo de la App 1. Columnas detectadas: {list(df1.columns)}")
            st.stop()
        if not col_combo_2:
            st.error(f"❌ No se encontró la columna de combinaciones en el archivo de la App 2. Columnas detectadas: {list(df2.columns)}")
            st.stop()

        # Normalizar a tuplas
        df1['Tupla_Normalizada'] = df1[col_combo_1].apply(parse_combinacion)
        df2['Tupla_Normalizada'] = df2[col_combo_2].apply(parse_combinacion)

        # Limpiar inválidos
        df1 = df1.dropna(subset=['Tupla_Normalizada'])
        df2 = df2.dropna(subset=['Tupla_Normalizada'])

        set1 = set(df1['Tupla_Normalizada'])
        set2 = set(df2['Tupla_Normalizada'])

        st.divider()
        st.header("2. Análisis de Intersección")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Combos Válidos (App 1)", len(set1))
        c2.metric("Combos Válidos (App 2)", len(set2))
        
        diamantes_puros = set1.intersection(set2)
        c3.metric("💎 Diamantes Puros", len(diamantes_puros))

        # --- MOSTRAR DIAMANTES PUROS ---
        if len(diamantes_puros) > 0:
            st.balloons()
            st.subheader("💎 Diamantes Puros (Coincidencia 100%)")
            df_diamantes = df2[df2['Tupla_Normalizada'].isin(diamantes_puros)].copy()
            df_diamantes = df_diamantes.drop(columns=['Tupla_Normalizada'])
            st.dataframe(df_diamantes, use_container_width=True)
        else:
            st.warning("No hubo coincidencias exactas del 100%. Busca similitudes abajo.")

        st.divider()

        # --- MOSTRAR DIAMANTES CERCANOS ---
        st.subheader("🔍 Diamantes Cercanos (Alta Similitud)")
        n_numeros = len(list(set1)[0]) if len(set1) > 0 else 6
        umbral = st.slider(f"¿Cuántos números en común quieres exigir? (Max {n_numeros})", 3, n_numeros, n_numeros-1)

        cercanos_data = []
        with st.spinner("Comparando..."):
            for t2 in set2:
                if t2 in diamantes_puros: continue
                for t1 in set1:
                    comunes = len(set(t2).intersection(set(t1)))
                    if comunes >= umbral:
                        info = df2[df2['Tupla_Normalizada'] == t2].iloc[0]
                        # Extraer Puntuación si existe
                        puntos = info.get('Puntuación', info.get('Puntuacion', 'N/A'))
                        cercanos_data.append({
                            "Combinación App 2": info[col_combo_2],
                            "Aciertos en común": comunes,
                            "Se parece a (App 1)": " - ".join(map(str, t1)),
                            "Puntuación": puntos
                        })
                        break # Pasa al siguiente t2

        if cercanos_data:
            df_cercanos = pd.DataFrame(cercanos_data)
            # Ordenar
            if 'Puntuación' in df_cercanos.columns and pd.api.types.is_numeric_dtype(df_cercanos['Puntuación']):
                df_cercanos = df_cercanos.sort_values(by=['Aciertos en común', 'Puntuación'], ascending=[False, False])
            else:
                df_cercanos = df_cercanos.sort_values(by=['Aciertos en común'], ascending=[False])

            st.success(f"Se encontraron **{len(df_cercanos)}** combinaciones similares.")
            st.dataframe(df_cercanos.reset_index(drop=True), use_container_width=True)
        else:
            st.error("No se encontraron combinaciones similares. Baja el umbral del slider.")

    except Exception as e:
        st.error(f"Error técnico inesperado: {e}")
