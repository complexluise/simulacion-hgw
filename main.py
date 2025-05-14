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

# --- Streamlit UI ---

def main():
    st.title("Simulador de Bonos - HGW Health Green World")

    st.sidebar.header("Parámetros Generales")
    membership = st.sidebar.selectbox("Membresía", list(MEMBERSHIP.keys()))
    bv_default = st.sidebar.number_input("BV por afiliado (default)", min_value=0.0, value=200.0)

    st.header("Bono de Equipo")
    col1, col2 = st.columns(2)
    with col1:
        bv_private = st.number_input("BV Línea Privada", min_value=0.0, value=0.0)
        bv_public = st.number_input("BV Línea Pública", min_value=0.0, value=0.0)
    with col2:
        team_result = calculate_team_bonus(bv_private, bv_public, membership)
        st.metric("BV Base de Pago", team_result['bv_base'])
        st.metric("Porcentaje de Bono", f"{team_result['bonus_pct']*100:.1f}%")
        st.metric("Monto Bono Equipo", f"{team_result['bonus_amount']:.2f}")

    st.header("Bono Élite")
    gen_count = st.number_input("Generaciones a simular (hasta 6)", min_value=1, max_value=6, value=3)
    custom_counts = st.checkbox("Personalizar afiliados y BV por generación")
    downline_data = []

    if custom_counts:
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
    st.write("Bonos por generación:", elite_result['generational_bonuses'])
    st.metric("Total Bono Élite", f"{elite_result['total_elite_bonus']:.2f}")

    st.header("Visualización de la Red")
    graph = nx.DiGraph()
    graph.add_node("Tú")
    for gen_idx, (cnt, _) in enumerate(downline_data, start=1):
        for j in range(cnt):
            label = f"G{gen_idx}-{j+1}"
            parent = "Tú" if gen_idx == 1 else f"G{gen_idx-1}-{(j % downline_data[gen_idx-2][0])+1}"
            graph.add_node(label)
            graph.add_edge(parent, label)

    pos = nx.spring_layout(graph)
    fig, ax = plt.subplots()
    nx.draw(graph, pos, with_labels=True, node_color="skyblue", edge_color="gray", ax=ax)
    st.pyplot(fig)

if __name__ == '__main__':
    main()
