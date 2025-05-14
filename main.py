import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

# Parámetros de membresía: porcentaje de Bono de Equipo y profundidad de Bono Élite
MEMBERSHIP = {
    'Pre-Junior': {'team_pct': 0.05, 'elite_depth': 0},
    'Junior':     {'team_pct': 0.07, 'elite_depth': 0},
    'Senior':     {'team_pct': 0.08, 'elite_depth': 3},
    'Master':     {'team_pct': 0.10, 'elite_depth': 6},
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

def main():
    st.set_page_config(page_title="Simulador de Bonos HGW", layout="wide")
    st.title("📊 Simulador de Bonos - HGW Health Green World")
    st.markdown("""
    Esta herramienta te permite simular el **Bono de Equipo** y el **Bono Élite** según tu red de afiliados,
    para ayudarte a entender mejor cómo maximizar tus ingresos en HGW.
    """)

    st.sidebar.header("🔧 Parámetros Generales")
    membership = st.sidebar.selectbox("Nivel de membresía", list(MEMBERSHIP.keys()),
                                      help="Selecciona tu categoría actual para aplicar el porcentaje de bono y profundidad del Bono Élite.")
    bv_default = st.sidebar.number_input("BV por afiliado (valor estimado)", min_value=0.0, value=200.0,
                                         help="Cada afiliado genera este valor en puntos de bono (BV), basado en sus compras/ventas.")

    st.header("💰 Simulación del Bono de Equipo")
    st.markdown("Calcula cuánto puedes ganar de tu red, comparando los puntos entre tus dos líneas (privada y pública).")
    col1, col2 = st.columns(2)
    with col1:
        bv_private = st.number_input("BV Línea Privada", min_value=0.0, value=0.0,
                                     help="Puntos generados por tus afiliados directos y su red.")
        bv_public = st.number_input("BV Línea Pública", min_value=0.0, value=0.0,
                                    help="Puntos generados por la línea que construye tu patrocinador.")
    with col2:
        team_result = calculate_team_bonus(bv_private, bv_public, membership)
        st.metric("📌 BV Base de Pago", team_result['bv_base'])
        st.metric("📈 Porcentaje de Bono", f"{team_result['bonus_pct']*100:.1f}%")
        st.metric("💵 Monto del Bono de Equipo", f"${team_result['bonus_amount']:.2f}")

    st.header("🏅 Simulación del Bono Élite")
    st.markdown("Gana un porcentaje del bono de tus afiliados por cada generación permitida según tu membresía.")
    gen_count = st.number_input("Número de generaciones a simular", min_value=1, max_value=6, value=3,
                                help="Cantidad de niveles de afiliados que deseas incluir en la simulación.")
    custom_counts = st.checkbox("Personalizar afiliados y BV por generación",
                                help="Activa esta opción si deseas definir valores distintos por generación.")
    downline_data = []

    if custom_counts:
        st.markdown("Define cuántos afiliados tienes por generación y cuánto generan en BV.")
        for i in range(1, gen_count+1):
            col1, col2 = st.columns(2)
            with col1:
                count = st.number_input(f"Afiliados Gen {i}", min_value=0, value=5 if i == 1 else 3, key=f"c{i}")
            with col2:
                bv = st.number_input(f"BV por afiliado Gen {i}", min_value=0.0, value=bv_default, key=f"bv{i}")
            downline_data.append((count, bv))
    else:
        downline_data = get_downline_counts(gen_count, bv_default)

    elite_result = calculate_elite_bonus(downline_data, membership)
    st.write("### 📊 Resultados por generación")
    for idx, val in enumerate(elite_result['generational_bonuses'], start=1):
        st.write(f"Gen {idx}: ${val:.2f}")
    st.metric("🏁 Total Bono Élite", f"${elite_result['total_elite_bonus']:.2f}")

    st.header("🌐 Visualización de la Red de Afiliación")
    st.markdown("Visualiza cómo se estructura tu equipo con base en la cantidad de generaciones y afiliados definidos.")
    graph = nx.DiGraph()
    graph.add_node("Tú")
    for gen_idx, (cnt, _) in enumerate(downline_data, start=1):
        for j in range(cnt):
            label = f"G{gen_idx}-{j+1}"
            parent = "Tú" if gen_idx == 1 else f"G{gen_idx-1}-{(j % downline_data[gen_idx-2][0])+1}"
            graph.add_node(label)
            graph.add_edge(parent, label)

    pos = nx.spring_layout(graph, seed=42)
    fig, ax = plt.subplots()
    nx.draw(graph, pos, with_labels=True, node_color="skyblue", edge_color="gray", node_size=1200, ax=ax)
    st.pyplot(fig)

    st.caption("""
    Esta simulación es una herramienta educativa. Las cifras estimadas pueden variar dependiendo del comportamiento real
    de tu red, las compras mensuales y promociones vigentes de HGW.
    """)

if __name__ == '__main__':
    main()
