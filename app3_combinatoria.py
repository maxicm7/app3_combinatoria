import streamlit as st
import pandas as pd

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Buscador de Diamantes 💎", page_icon="💎")

# --- Funciones Auxiliares ---
def parse_combinacion(combo_str):
    """
    Toma un string de combinación como "5 - 12 - 24 - 35 - 40 - 45" 
    y lo convierte en una tupla ordenada de enteros: (5, 12, 24, 35, 40, 45)
    Esto permite comparar combinaciones de forma matemáticamente exacta.
    """
    try:
        # Reemplazar posibles comas o separadores raros por guiones si es necesario
        combo_str = str(combo_str).replace(',', ' - ')
        numeros = [int(n.strip()) for n in combo_str.split('-') if n.strip().isdigit()]
        if len(numeros) >= 5: # Asume juegos de 5 o 6 números
            return tuple(sorted(numeros))
        return None
    except:
        return None

# --- Interfaz Principal ---
st.title("💎 El Buscador de Combinaciones Diamante")
st.markdown("""
Esta herramienta cruza los resultados de tus dos algoritmos para encontrar la **perfección probabilística**.
*   **App 1 (Estructura):** Aporta la viabilidad histórica a largo plazo.
*   **App 2 (Dinámica):** Aporta la inercia térmica y dependencia del momento actual.
""")

st.header("1. Sube tus Resultados")
col1, col2 = st.columns(2)

with col1:
    st.info("📦 **Paso 1:** Sube el CSV descargado de la **App 1** (Simulación en Cascada/Genético).")
    file_app1 = st.file_uploader("Resultados App 1 (CSV)", type="csv", key="app1")

with col2:
    st.success("🔥 **Paso 2:** Sube el CSV descargado de la **App 2** (Agente Dinámico / Top Ranking).")
    file_app2 = st.file_uploader("Resultados App 2 (CSV)", type="csv", key="app2")

if file_app1 is not None and file_app2 is not None:
    try:
        # Cargar los dataframes
        df1 = pd.read_csv(file_app1)
        df2 = pd.read_csv(file_app2)

        # Buscar la columna que contenga la palabra "Combinaci" (por si hay tildes)
        col_combo_1 = [c for c in df1.columns if "combinaci" in c.lower()][0]
        col_combo_2 = [c for c in df2.columns if "combinaci" in c.lower()][0]

        # Normalizar las combinaciones a tuplas matemáticas
        df1['Tupla'] = df1[col_combo_1].apply(parse_combinacion)
        df2['Tupla'] = df2[col_combo_2].apply(parse_combinacion)

        # Limpiar filas inválidas
        df1 = df1.dropna(subset=['Tupla'])
        df2 = df2.dropna(subset=['Tupla'])

        # Convertir a conjuntos (Sets) para búsqueda ultrarrápida
        set1 = set(df1['Tupla'])
        set2 = set(df2['Tupla'])

        st.divider()
        st.header("2. Análisis de Intersección")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Combos Analizados (App 1)", len(set1))
        c2.metric("Combos Analizados (App 2)", len(set2))
        
        # --- 1. BUSCAR DIAMANTES PUROS (COINCIDENCIA EXACTA) ---
        diamantes_puros = set1.intersection(set2)
        c3.metric("💎 Diamantes Puros Encontrados", len(diamantes_puros))

        if len(diamantes_puros) > 0:
            st.balloons()
            st.subheader("💎 Diamantes Puros (Coincidencia 100%)")
            st.markdown("Estas combinaciones pasaron los estrictos filtros estructurales de la App 1 y tienen la alta puntuación Gaussiana de la App 2. **¡Estas son tus mejores jugadas!**")
            
            # Recuperar datos de puntuación de la App 2 para mostrarlos
            df_diamantes = df2[df2['Tupla'].isin(diamantes_puros)].copy()
            df_diamantes = df_diamantes.drop(columns=['Tupla']) # Limpiar vista
            st.dataframe(df_diamantes, use_container_width=True)
            
            # Botón de descarga
            csv_diamantes = df_diamantes.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Diamantes Puros",
                data=csv_diamantes,
                file_name='diamantes_puros.csv',
                mime='text/csv',
            )
        else:
            st.warning("No hubo coincidencias exactas del 100%. Esto es normal si generaste pocas combinaciones en alguna de las apps. Revisa los 'Diamantes Cercanos' abajo.")

        st.divider()

        # --- 2. BUSCAR DIAMANTES CERCANOS (SIMILITUD) ---
        st.subheader("🔍 Diamantes Cercanos (Alta Similitud)")
        st.markdown("Si no hay coincidencias exactas, aquí buscamos combinaciones de la **App 2 (Top Ranking)** que sean casi idénticas a las de la **App 1 (Estructura)**.")
        
        n_numeros = len(list(set1)[0]) if len(set1) > 0 else 6
        umbral_similitud = st.slider(f"¿Cuántos números en común quieres exigir? (Max {n_numeros})", 
                                     min_value=int(n_numeros/2), max_value=n_numeros, value=n_numeros-1)

        cercanos_data = []
        with st.spinner("Comparando sinergias..."):
            for t2 in set2:
                if t2 in diamantes_puros:
                    continue # Ya lo mostramos arriba
                
                # Buscar contra todos los de la App 1
                for t1 in set1:
                    numeros_en_comun = len(set(t2).intersection(set(t1)))
                    if numeros_en_comun >= umbral_similitud:
                        # Extraer info de la App 2
                        info_app2 = df2[df2['Tupla'] == t2].iloc[0]
                        
                        cercanos_data.append({
                            "Combinación Recomendada (App 2)": info_app2[col_combo_2],
                            "Aciertos en común": numeros_en_comun,
                            "Se parece a (App 1)": " - ".join(map(str, t1)),
                            "Puntuación Original": info_app2.get('Puntuación', 'N/A')
                        })
                        break # Con que se parezca a uno de la App 1 es suficiente para recomendarla

        if cercanos_data:
            df_cercanos = pd.DataFrame(cercanos_data)
            # Ordenar por Puntuación Original si existe, y luego por Aciertos en común
            if 'Puntuación Original' in df_cercanos.columns and df_cercanos['Puntuación Original'].dtype in ['float64', 'int64']:
                df_cercanos = df_cercanos.sort_values(by=['Aciertos en común', 'Puntuación Original'], ascending=[False, False])
            else:
                df_cercanos = df_cercanos.sort_values(by=['Aciertos en común'], ascending=[False])

            st.success(f"Se encontraron **{len(df_cercanos)}** combinaciones altamente viables.")
            st.dataframe(df_cercanos.reset_index(drop=True), use_container_width=True)
            
            # Botón de descarga
            csv_cercanos = df_cercanos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Diamantes Cercanos",
                data=csv_cercanos,
                file_name='diamantes_cercanos.csv',
                mime='text/csv',
            )
        else:
            st.error("No se encontraron combinaciones similares con este umbral. Intenta bajar la cantidad de números en común exigidos.")

    except Exception as e:
        st.error(f"Ocurrió un error procesando los archivos. Verifica que sean los CSV correctos. Error técnico: {e}")
