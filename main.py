import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image
import io
import base64

# Parámetros de membresía: porcentaje de Bono de Equipo y profundidad de Bono Élite
MEMBERSHIP = {
    'Pre-Junior': {'team_pct': 0.05, 'elite_depth': 0, 'color': '#90CAF9'},  # Light Blue
    'Junior':     {'team_pct': 0.07, 'elite_depth': 0, 'color': '#81C784'},  # Light Green
    'Senior':     {'team_pct': 0.08, 'elite_depth': 3, 'color': '#FFB74D'},  # Light Orange
    'Master':     {'team_pct': 0.10, 'elite_depth': 6, 'color': '#F06292'},  # Light Pink
}

def get_downline_counts(gen_count: int, bv_per_person: float, first_gen_default: int = 5, other_gen_default: int = 3) -> list[tuple[int, float]]:
    """
    Genera una lista de tuplas con el número de afiliados y su BV por cada generación.

    Esta función facilita la simulación al asumir un mismo BV por afiliado en todas las generaciones.

    Args:
        gen_count (int): Número de generaciones a generar.
        bv_per_person (float): Valor BV generado por cada afiliado.
        first_gen_default (int): Afiliados en primera generación.
        other_gen_default (int): Afiliados en siguientes generaciones.

    Returns:
        list[tuple[int, float]]: Lista de tuplas (cantidad_afiliados, bv_por_afiliado) por generación.
    """
    counts = []
    for i in range(gen_count):
        count = first_gen_default if i == 0 else other_gen_default
        counts.append((count, bv_per_person))
    return counts

def calculate_team_bonus(bv_private: float, bv_public: float, membership_level: str) -> dict:
    """
    Calcula el Bono de Equipo (Team Bonus) en función de los BV de ambas líneas y la membresía.

    Args:
        bv_private (float): Puntos (BV) generados en tu línea privada.
        bv_public (float): Puntos (BV) generados en tu línea pública (patrocinador).
        membership_level (str): Nivel de membresía del usuario.

    Returns:
        dict: Incluye base BV, porcentaje de bono aplicado y monto calculado.
    """
    bv_base = min(bv_private, bv_public)
    rate = MEMBERSHIP[membership_level]['team_pct']
    bonus_amount = bv_base * rate
    return {
        'bv_base': bv_base,
        'bonus_pct': rate,
        'bonus_amount': bonus_amount
    }

def calculate_elite_bonus(downline_data: list[tuple[int, float]], membership_level: str) -> dict:
    """
    Calcula el Bono Élite con datos personalizados por generación.

    Args:
        downline_data (list[tuple[int, float]]): Lista con (afiliados, BV por persona) por generación.
        membership_level (str): Nivel de membresía.

    Returns:
        dict: Bonos por generación y total.
    """
    max_depth = MEMBERSHIP[membership_level]['elite_depth']
    rate = 0.04
    bonuses = []

    for count, bv in downline_data[:max_depth]:
        gen_bonus = count * bv * rate
        bonuses.append(gen_bonus)

    total_elite = sum(bonuses)
    return {
        'generational_bonuses': bonuses,
        'total_elite_bonus': total_elite
    }

# --- Interfaz de Usuario con Streamlit ---

def setup_page():
    """Configura la página y aplica estilos CSS."""
    st.set_page_config(
        page_title="Simulador de Bonos HGW", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS para mejorar la apariencia
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .highlight-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 20px;
    }
    .result-box {
        background-color: #f1f8e9;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #43A047;
        margin-top: 10px;
    }
    .info-box {
        background-color: #fff8e1;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #FFB300;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    .membership-card {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def show_header_and_intro():
    """Muestra el encabezado principal y la sección de introducción."""
    # Encabezado principal
    st.markdown('<h1 class="main-header">📊 Simulador de Bonos - HGW Health Green World</h1>', unsafe_allow_html=True)

    # Introducción y explicación
    with st.expander("📚 ¿Qué es este simulador y cómo usarlo?", expanded=False):
        st.markdown("""
        ### Bienvenido al Simulador de Bonos HGW

        Esta herramienta te ayuda a entender y calcular tus posibles ganancias en HGW Health Green World, 
        basadas en tu red de afiliados y tu nivel de membresía.

        #### ¿Qué puedes hacer con este simulador?

        1. **Calcular tu Bono de Equipo**: Descubre cuánto puedes ganar según los puntos generados por tus dos líneas.
        2. **Simular tu Bono Élite**: Visualiza tus ganancias por cada generación de afiliados.
        3. **Ver tu Red de Afiliación**: Observa cómo crece tu equipo y cómo se estructura.

        #### Conceptos Clave:

        - **BV (Valor de Bono)**: Puntos que se generan por las compras y ventas de productos.
        - **Línea Privada**: Tus afiliados directos y la red que ellos construyen.
        - **Línea Pública**: La red que construye tu patrocinador y de la que tú formas parte.
        - **Generaciones**: Niveles de profundidad en tu red de afiliados.
        """)

def setup_sidebar():
    """Configura la barra lateral con selección de membresía y parámetros."""
    st.sidebar.markdown('<div class="section-header">🔧 Parámetros Generales</div>', unsafe_allow_html=True)

    # Sección de membresía con tarjetas visuales
    st.sidebar.markdown("### 🌟 Selecciona tu Nivel de Membresía")

    # Mostrar tarjetas de membresía
    cols = st.sidebar.columns(2)
    membership_options = list(MEMBERSHIP.keys())
    selected_membership = None

    for i, (level, data) in enumerate(MEMBERSHIP.items()):
        col = cols[i % 2]
        card_html = f"""
        <div class="membership-card" style="background-color: {data['color']}40; border: 2px solid {data['color']};">
            <h4>{level}</h4>
            <p>Bono Equipo: {int(data['team_pct']*100)}%</p>
            <p>Generaciones: {data['elite_depth']}</p>
        </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)
        if col.button(f"Seleccionar {level}", key=f"btn_{level}"):
            selected_membership = level

    # Si no se seleccionó ninguna membresía mediante botones, usar un selectbox como respaldo
    if not selected_membership:
        selected_membership = membership_options[0]  # Valor predeterminado
        membership = st.sidebar.selectbox(
            "O selecciona desde la lista:",
            membership_options,
            index=0,
            help="Tu nivel de membresía determina los porcentajes de bonos y la profundidad de generaciones."
        )
    else:
        membership = selected_membership
        st.sidebar.success(f"✅ Has seleccionado: {membership}")

    # Información sobre la membresía seleccionada
    st.sidebar.markdown(f"""
    <div class="info-box">
        <strong>Membresía {membership}:</strong><br>
        • Bono de Equipo: {int(MEMBERSHIP[membership]['team_pct']*100)}%<br>
        • Generaciones Élite: {MEMBERSHIP[membership]['elite_depth']}<br>
    </div>
    """, unsafe_allow_html=True)

    # Valor BV por afiliado
    st.sidebar.markdown("### 💎 Valor de Puntos")
    bv_default = st.sidebar.number_input(
        "BV por afiliado (valor estimado)", 
        min_value=0.0, 
        value=200.0,
        help="Cada afiliado genera este valor en puntos de bono (BV), basado en sus compras/ventas."
    )

    # Agregar explicación sobre BV
    st.sidebar.markdown("""
    <div class="info-box">
        <strong>¿Qué es BV?</strong><br>
        BV (Valor de Bono) son los puntos que se generan por las compras y ventas de productos en HGW. 
        Cada producto tiene un valor BV asignado.
    </div>
    """, unsafe_allow_html=True)

    return membership, bv_default

def show_network_visualization(membership, bv_default, downline_data, gen_count):
    """Muestra la visualización de la red de afiliación."""
    st.markdown('<div class="section-header">🌐 Visualización de tu Red de Afiliación</div>', unsafe_allow_html=True)

    # Explicación de la visualización
    with st.expander("ℹ️ ¿Cómo interpretar esta visualización?", expanded=False):
        st.markdown("""
        Esta visualización te muestra cómo se estructura tu red de afiliados según la configuración que has definido.

        **Elementos de la visualización:**
        - **Tú**: El nodo central representa tu posición en la red.
        - **G1, G2, etc.**: Representan las generaciones de afiliados.
        - **Conexiones**: Las líneas muestran quién patrocinó a quién.

        **¿Por qué es importante?**
        Entender la estructura de tu red te ayuda a identificar dónde necesitas fortalecer tu equipo
        y cómo se distribuyen tus ingresos por generación.
        """)

    # Crear columnas para controles y visualización
    viz_col1, viz_col2 = st.columns([1, 3])

    with viz_col1:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.subheader("Opciones de visualización")

        # Opciones para personalizar la visualización
        show_labels = st.checkbox("Mostrar etiquetas", value=True, 
                                 help="Muestra los nombres de cada nodo en el gráfico")

        node_size = st.slider("Tamaño de los nodos", min_value=300, max_value=2000, value=1200,
                             help="Ajusta el tamaño de los círculos que representan a los afiliados")

        # Selector de colores por generación
        color_by_gen = st.checkbox("Colorear por generación", value=True,
                                  help="Asigna diferentes colores a cada generación para distinguirlas mejor")

        # Selector de layout
        layout_type = st.radio("Tipo de visualización",
                              ["Radial", "Árbol", "Circular"],
                              help="Cambia la forma en que se organizan los nodos")

        st.markdown('</div>', unsafe_allow_html=True)

    with viz_col2:
        # Crear el grafo
        graph = nx.DiGraph()
        graph.add_node("Tú")

        # Definir colores para las generaciones
        generation_colors = ["#1E88E5", "#43A047", "#FB8C00", "#E53935", "#5E35B1", "#00ACC1"]

        # Agregar nodos y conexiones
        node_colors = ["#FF5252"]  # Color para el nodo "Tú"
        node_sizes = [node_size * 1.2]  # Tamaño para el nodo "Tú"

        for gen_idx, (cnt, _) in enumerate(downline_data, start=1):
            for j in range(cnt):
                label = f"G{gen_idx}-{j+1}"
                parent = "Tú" if gen_idx == 1 else f"G{gen_idx-1}-{(j % downline_data[gen_idx-2][0])+1}"
                graph.add_node(label)
                graph.add_edge(parent, label)

                # Asignar color según la generación
                if color_by_gen:
                    node_colors.append(generation_colors[(gen_idx-1) % len(generation_colors)])
                else:
                    node_colors.append(MEMBERSHIP[membership]['color'])

                # Asignar tamaño según la generación (decreciente)
                node_sizes.append(node_size * (0.9 ** (gen_idx-1)))

        # Determinar el layout según la selección
        if layout_type == "Árbol":
            pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
        elif layout_type == "Radial":
            pos = nx.spring_layout(graph, seed=42)
        else:  # Circular
            pos = nx.circular_layout(graph)

        # Crear la figura
        fig, ax = plt.subplots(figsize=(10, 8))

        # Dibujar el grafo
        nx.draw(
            graph, pos, 
            with_labels=show_labels,
            node_color=node_colors,
            node_size=node_sizes,
            edge_color="#BDBDBD",
            width=1.5,
            alpha=0.9,
            font_size=10,
            font_weight="bold",
            ax=ax
        )

        # Agregar título
        plt.title(f"Tu Red de Afiliación - {membership}", fontsize=16)

        # Mostrar la visualización
        st.pyplot(fig)

        # Leyenda de colores por generación
        if color_by_gen:
            st.markdown("#### Leyenda de colores:")
            legend_cols = st.columns(min(6, gen_count))
            for i in range(min(gen_count, 6)):
                with legend_cols[i]:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <div style="width: 15px; height: 15px; background-color: {generation_colors[i]}; border-radius: 50%; margin-right: 5px;"></div>
                        <div>Generación {i+1}</div>
                    </div>
                    """, unsafe_allow_html=True)

def show_monetary_summary(bv_private, bv_public, membership, downline_data):
    """Muestra el resumen monetario de los bonos."""
    st.markdown('<div class="section-header">💵 Resumen de Ganancias</div>', unsafe_allow_html=True)

    # Calcular los bonos
    team_result = calculate_team_bonus(bv_private, bv_public, membership)
    elite_result = calculate_elite_bonus(downline_data, membership) if MEMBERSHIP[membership]['elite_depth'] > 0 else {'total_elite_bonus': 0}

    # Total de ganancias
    total_earnings = team_result['bonus_amount'] + elite_result['total_elite_bonus']

    # Mostrar el resumen
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💰 Bono de Equipo", f"${team_result['bonus_amount']:.2f}")

    with col2:
        st.metric("🏅 Bono Élite", f"${elite_result['total_elite_bonus']:.2f}")

    with col3:
        st.metric("💵 Total Ganancias", f"${total_earnings:.2f}", delta=f"{total_earnings:.2f}")

    return team_result, elite_result, total_earnings

def simulate_team_bonus(membership):
    """Simula el cálculo del Bono de Equipo."""
    st.markdown('<div class="section-header">💰 Simulación del Bono de Equipo</div>', unsafe_allow_html=True)

    # Explicación del Bono de Equipo
    with st.expander("ℹ️ ¿Cómo funciona el Bono de Equipo?", expanded=False):
        st.markdown("""
        ## 🔷 BONO DE EQUIPO – ¿Cómo se calcula?

        **¿Qué es?**
        Es un bono por el volumen generado entre tus dos líneas (una construida por tu patrocinador y otra por ti).

        ### ✅ Requisitos:

        * Tener **membresía activa** (mínimo 10 BV mensuales).
        * Tener **volumen en ambas líneas** (pública y privada).
        * Estar dentro del **tope diario** de tu membresía.

        ### 💰 Cálculo:

        1. **Identifica el volumen (BV) de la pierna más débil** (la que tenga menos puntos).
        2. Aplica el **% correspondiente a tu membresía**:

           * Pre-Junior → 5% (tope $50/día)
           * Junior → 7% (tope $120/día)
           * Senior → 8% (tope $360/día)
           * Master → 10% (tope $720/día)
        3. **Resultado = % × BV de la pierna menor** (limitado por tu tope diario).

        #### 📌 Ejemplo:

        * Línea pública: 3,000 BV
        * Línea privada: 2,000 BV
        * Eres Master (10%)
          → 2,000 × 10% = **200 USD** (dentro del tope de $720 → se paga completo).
        """)

    # Valores de ejemplo para ayudar a los usuarios
    example_values = {
        'Pre-Junior': {'private': 500, 'public': 300},
        'Junior': {'private': 800, 'public': 600},
        'Senior': {'private': 1500, 'public': 1200},
        'Master': {'private': 3000, 'public': 2500},
    }

    # Columnas para entrada y resultados
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.subheader("Ingresa los valores de tus líneas:")

        # Inicializar valores en session_state si no existen
        if 'bv_private' not in st.session_state:
            st.session_state.bv_private = 0.0
        if 'bv_public' not in st.session_state:
            st.session_state.bv_public = 0.0
        if 'example_loaded' not in st.session_state:
            st.session_state.example_loaded = False

        # Botón para cargar ejemplo
        if st.button(f"📝 Cargar ejemplo para {membership}", key="load_example_team"):
            st.session_state.bv_private = example_values[membership]['private']
            st.session_state.bv_public = example_values[membership]['public']
            st.session_state.example_loaded = True

        # Campos de entrada con valores de session_state
        bv_private = st.number_input(
            "BV Línea Privada", 
            min_value=0.0, 
            value=float(st.session_state.bv_private),
            help="Puntos generados por tus afiliados directos y su red.",
            key="bv_private_input"
        )
        # Actualizar session_state con el nuevo valor
        st.session_state.bv_private = bv_private

        bv_public = st.number_input(
            "BV Línea Pública", 
            min_value=0.0, 
            value=float(st.session_state.bv_public),
            help="Puntos generados por la línea que construye tu patrocinador.",
            key="bv_public_input"
        )
        # Actualizar session_state con el nuevo valor
        st.session_state.bv_public = bv_public

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Cálculo del bono
        team_result = calculate_team_bonus(bv_private, bv_public, membership)

        # Mostrar resultados en un formato más atractivo
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("Resultados:")

        # Visualización de la base de pago
        st.markdown(f"""
        📊 **Base de cálculo**: 
        <span style="font-size: 1.2rem; color: #1E88E5;">${team_result['bv_base']:.2f} BV</span>
        <br><small>(El menor valor entre tus dos líneas)</small>
        """, unsafe_allow_html=True)

        # Visualización del porcentaje aplicado
        st.markdown(f"""
        📈 **Porcentaje aplicado**: 
        <span style="font-size: 1.2rem; color: #43A047;">{team_result['bonus_pct']*100:.1f}%</span>
        <br><small>(Según tu nivel de membresía {membership})</small>
        """, unsafe_allow_html=True)

        # Visualización del resultado final
        st.markdown(f"""
        💵 **Tu Bono de Equipo**: 
        <span style="font-size: 1.5rem; font-weight: bold; color: #E53935;">${team_result['bonus_amount']:.2f}</span>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    return bv_private, bv_public

def simulate_elite_bonus(membership, bv_default):
    """Simula el cálculo del Bono Élite."""
    st.markdown('<div class="section-header">🏅 Simulación del Bono Élite</div>', unsafe_allow_html=True)

    # Explicación del Bono Élite
    with st.expander("ℹ️ ¿Cómo funciona el Bono Élite?", expanded=False):
        st.markdown("""
        ## 🔷 BONO ÉLITE – ¿Cómo se calcula?

        **¿Qué es?**
        Es un bono de liderazgo: ganas un **4% del Bono de Equipo** que cobran tus afiliados, por generación.

        ### ✅ Requisitos:

        * Ser **Senior** (cobras hasta 3 generaciones) o **Master** (hasta 6 generaciones).
        * Mantenerte **activo (10 BV mensuales)**.

        ### 💰 Cálculo:

        1. Identifica las **ganancias de Bono de Equipo** de tus afiliados por generación.
        2. Aplica el **4% sobre lo que cobró cada uno**, por generación calificada.
        3. Suma los valores.

        #### 📌 Ejemplo:

        * Tu directo ganó $200 → tú ganas **$8** (4%).
        * Otro afiliado en 2ª generación ganó $100 → tú ganas **$4**.
        * En total, si tu red generó $2,000 en Bonos de Equipo, tú ganas **$80 de Bono Élite** (4% promedio).
        """)

        # Tabla comparativa de membresías
        st.markdown("#### Comparativa de Generaciones por Membresía")
        membership_table = """
        | Membresía | Generaciones | Potencial de Ganancia |
        |-----------|--------------|------------------------|
        | Pre-Junior | 0 | No aplica |
        | Junior | 0 | No aplica |
        | Senior | 3 | Gana de 3 niveles de profundidad |
        | Master | 6 | Gana de 6 niveles de profundidad |
        """
        st.markdown(membership_table)

        # Tabla resumen de bonos
        st.markdown("## 🎯 En resumen:")
        summary_table = """
        | Bono       | Fórmula Principal                                  | Clave para maximizar                    |
        | ---------- | -------------------------------------------------- | --------------------------------------- |
        | **Equipo** | `% membresía × BV pierna débil`                    | Tener alta membresía y balancear líneas |
        | **Élite**  | `4% × Bono de Equipo cobrado por tus generaciones` | Patrocinar y ayudar a que ganen         |
        """
        st.markdown(summary_table)

    # Valores de ejemplo para cada membresía
    example_gen_counts = {
        'Pre-Junior': 0,
        'Junior': 0,
        'Senior': 3,
        'Master': 6
    }

    # Determinar cuántas generaciones mostrar según la membresía
    max_gen = example_gen_counts[membership]
    if max_gen == 0:
        st.warning(f"⚠️ Tu nivel de membresía ({membership}) no te permite acceder al Bono Élite. Considera actualizar a Senior o Master para desbloquear este beneficio.")

    # Columnas para configuración y resultados
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.subheader("Configura tu red de afiliados:")

        # Inicializar valores en session_state si no existen
        if 'gen_count' not in st.session_state:
            st.session_state.gen_count = min(3, max(1, max_gen))

        if 'custom_counts' not in st.session_state:
            st.session_state.custom_counts = False

        if 'downline_data' not in st.session_state:
            st.session_state.downline_data = get_downline_counts(st.session_state.gen_count, bv_default)

        # Número de generaciones a simular (limitado por la membresía)
        gen_count = st.number_input(
            "Número de generaciones a simular", 
            min_value=1, 
            max_value=max(6, max_gen), 
            value=st.session_state.gen_count,
            help="Cantidad de niveles de afiliados que deseas incluir en la simulación.",
            disabled=max_gen == 0,
            key="gen_count_input"
        )

        # Actualizar session_state con el nuevo valor
        st.session_state.gen_count = gen_count

        # Opción para personalizar
        custom_counts = st.checkbox(
            "Personalizar afiliados y BV por generación",
            value=st.session_state.custom_counts,
            help="Activa esta opción si deseas definir valores distintos por generación.",
            disabled=max_gen == 0,
            key="custom_counts_checkbox"
        )

        # Actualizar session_state con el nuevo valor
        st.session_state.custom_counts = custom_counts

        downline_data = []

        if custom_counts:
            st.markdown("Define cuántos afiliados tienes por generación y cuánto generan en BV:")

            # Crear columnas para cada generación
            if gen_count <= 3:
                gen_cols = st.columns(gen_count)
                for i in range(1, gen_count+1):
                    # Inicializar valores en session_state si no existen
                    if f'count_{i}' not in st.session_state:
                        st.session_state[f'count_{i}'] = 5 if i == 1 else 3
                    if f'bv_{i}' not in st.session_state:
                        st.session_state[f'bv_{i}'] = bv_default

                    with gen_cols[i-1]:
                        st.markdown(f"**Generación {i}**")
                        count = st.number_input(
                            f"Afiliados", 
                            min_value=0, 
                            value=st.session_state[f'count_{i}'], 
                            key=f"c{i}"
                        )
                        # Actualizar session_state con el nuevo valor
                        st.session_state[f'count_{i}'] = count

                        bv = st.number_input(
                            f"BV por afiliado", 
                            min_value=0.0, 
                            value=st.session_state[f'bv_{i}'], 
                            key=f"bv{i}"
                        )
                        # Actualizar session_state con el nuevo valor
                        st.session_state[f'bv_{i}'] = bv

                        downline_data.append((count, bv))
            else:
                # Si hay muchas generaciones, usar un formato vertical
                for i in range(1, gen_count+1):
                    # Inicializar valores en session_state si no existen
                    if f'count_{i}' not in st.session_state:
                        st.session_state[f'count_{i}'] = 5 if i == 1 else 3
                    if f'bv_{i}' not in st.session_state:
                        st.session_state[f'bv_{i}'] = bv_default

                    st.markdown(f"**Generación {i}**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        count = st.number_input(
                            f"Afiliados Gen {i}", 
                            min_value=0, 
                            value=st.session_state[f'count_{i}'], 
                            key=f"c{i}"
                        )
                        # Actualizar session_state con el nuevo valor
                        st.session_state[f'count_{i}'] = count
                    with col_b:
                        bv = st.number_input(
                            f"BV por afiliado Gen {i}", 
                            min_value=0.0, 
                            value=st.session_state[f'bv_{i}'], 
                            key=f"bv{i}"
                        )
                        # Actualizar session_state con el nuevo valor
                        st.session_state[f'bv_{i}'] = bv
                    downline_data.append((count, bv))
        else:
            # Usar valores predeterminados o los guardados en session_state
            if 'optimized' not in st.session_state:
                st.session_state.optimized = False

            if st.session_state.optimized:
                # Usar valores optimizados guardados en session_state
                downline_data = st.session_state.downline_data
            else:
                # Usar valores predeterminados
                downline_data = get_downline_counts(gen_count, bv_default)

            # Mostrar resumen de la configuración
            st.markdown("**Configuración actual:**")
            st.markdown(f"- Primera generación: **5 afiliados** con **{bv_default} BV** cada uno")
            st.markdown(f"- Siguientes generaciones: **3 afiliados** con **{bv_default} BV** cada uno")

            # Botón para cargar ejemplo optimizado
            if st.button("📝 Optimizar para mi membresía", disabled=max_gen == 0, key="optimize_button"):
                # Ajustar los valores según la membresía
                if membership == 'Master':
                    # Para Master, optimizamos para 6 generaciones
                    optimized_data = get_downline_counts(6, bv_default, 7, 5)
                elif membership == 'Senior':
                    # Para Senior, optimizamos para 3 generaciones
                    optimized_data = get_downline_counts(3, bv_default, 6, 4)
                else:
                    # Para otros niveles, usamos valores predeterminados
                    optimized_data = get_downline_counts(gen_count, bv_default)

                # Guardar los valores optimizados en session_state
                st.session_state.downline_data = optimized_data
                st.session_state.optimized = True
                downline_data = optimized_data

                st.success(f"✅ Configuración optimizada para {membership}")

        # Guardar downline_data en session_state para uso futuro
        st.session_state.downline_data = downline_data

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if max_gen > 0:
            # Cálculo del bono
            elite_result = calculate_elite_bonus(downline_data, membership)

            # Mostrar resultados en un formato más atractivo
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.subheader("Resultados del Bono Élite:")

            # Mostrar resultados por generación con barras de progreso
            st.markdown("#### 📊 Ganancias por generación:")

            # Encontrar el valor máximo para escalar las barras
            max_bonus = max(elite_result['generational_bonuses']) if elite_result['generational_bonuses'] else 0

            for idx, val in enumerate(elite_result['generational_bonuses'], start=1):
                # Calcular el porcentaje para la barra de progreso (mínimo 5% para visibilidad)
                percentage = max(5, (val / max_bonus * 100)) if max_bonus > 0 else 5

                # Crear una barra de progreso personalizada
                st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <div style="width: 100px; font-weight: bold;">Gen {idx}:</div>
                        <div style="font-size: 1.1rem; color: #1E88E5;">${val:.2f}</div>
                    </div>
                    <div style="background-color: #e0e0e0; border-radius: 10px; height: 10px; width: 100%;">
                        <div style="background-color: {MEMBERSHIP[membership]['color']}; width: {percentage}%; height: 10px; border-radius: 10px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Mostrar el total
            st.markdown(f"""
            <div style="margin-top: 20px; padding: 10px; background-color: #f5f5f5; border-radius: 5px; text-align: center;">
                <div style="font-size: 0.9rem; color: #616161;">TOTAL BONO ÉLITE</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #E53935;">
                    ${elite_result['total_elite_bonus']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    return downline_data, gen_count

def show_tips_and_footer():
    """Muestra consejos y el pie de página."""
    # Sección de consejos y optimización
    st.markdown('<div class="section-header">💡 Consejos para Optimizar tus Ganancias</div>', unsafe_allow_html=True)

    with st.expander("📈 Estrategias para maximizar tus bonos", expanded=False):
        st.markdown("""
        ### Consejos para el Bono de Equipo:

        1. **Equilibra tus líneas**: Intenta mantener un volumen similar en ambas líneas para maximizar tu base de pago.
        2. **Enfócate en la línea más débil**: Identifica cuál de tus líneas genera menos volumen y trabaja en fortalecerla.
        3. **Aumenta tu nivel de membresía**: A mayor nivel, mayor porcentaje de ganancia sobre el mismo volumen.

        ### Consejos para el Bono Élite:

        1. **Ayuda a tus afiliados a ganar**: Cuanto más ganen ellos en Bono de Equipo, más ganarás tú.
        2. **Desarrolla líderes en cada generación**: Enfócate en tener afiliados fuertes en cada nivel.
        3. **Alcanza el nivel Master**: Te permite ganar de 6 generaciones en lugar de 3 (Senior).
        """)

    # Botones de acción (placeholders para futuras funcionalidades)
    st.markdown("### 🚀 Acciones")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Descargar resumen de simulación", disabled=True):
            st.info("Funcionalidad en desarrollo. Próximamente podrás descargar un PDF con el resumen de tu simulación.")

    with col2:
        if st.button("🔗 Compartir esta simulación", disabled=True):
            st.info("Funcionalidad en desarrollo. Próximamente podrás compartir un enlace a esta simulación específica.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>Simulador de Bonos HGW Health Green World | Desarrollado con ❤️ para la comunidad HGW</p>
        <p>Este simulador es una herramienta educativa y los resultados pueden variar según las condiciones reales del mercado.</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Función principal que coordina la ejecución de todas las secciones de la aplicación."""
    # Configurar la página y aplicar estilos CSS
    setup_page()

    # Mostrar encabezado e introducción
    show_header_and_intro()

    # Configurar la barra lateral y obtener parámetros
    membership, bv_default = setup_sidebar()

    # Simular el Bono Élite para obtener los datos de la red
    downline_data, gen_count = simulate_elite_bonus(membership, bv_default)

    # Mostrar la visualización de la red
    show_network_visualization(membership, bv_default, downline_data, gen_count)

    # Simular el Bono de Equipo
    bv_private, bv_public = simulate_team_bonus(membership)

    # Mostrar el resumen monetario
    team_result, elite_result, total_earnings = show_monetary_summary(bv_private, bv_public, membership, downline_data)

    # Mostrar consejos y pie de página
    show_tips_and_footer()

if __name__ == '__main__':
    main()
