import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from streamlit_option_menu import option_menu
import re

# Fonction pour charger et traiter un fichier CSV
def load_csv(file_path):
    df = pd.read_csv(file_path, header=2)
    df['Seconds_per_50m'] = df['Pace/50'].apply(lambda x: 
        sum(float(part) * 60**i for i, part in enumerate(reversed(str(x).split(':')))) if pd.notna(x) else None)
        
        
    def convert_rest_time_to_seconds(rest_time):
        try:
            # Gérer le cas où le format est hh:mm:ss
            parts = rest_time.split(':')
            if len(parts) == 3:  # Format hh:mm:ss
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:  # Format mm:ss (si une heure est omise)
                return int(parts[0]) * 60 + float(parts[1])
            else:
                # Cas où la valeur est incorrecte ou sous forme '00.00'
                return 0
        except ValueError:
            # Si une erreur de conversion se produit (ex: '00.00')
            return 0

    # Appliquer la fonction de conversion sur la colonne 'Rest Time'
    df['Rest Time (s)'] = df['Rest Time'].apply(lambda x: convert_rest_time_to_seconds(str(x)) if pd.notna(x) else 0)


    return df

# Fonction pour combiner les fichiers CSV d'un dossier en un DataFrame unique
def combine_csv_files(folder_path):
    csv_files = list(Path(folder_path).glob("*.csv"))
    dataframes = [load_csv(file) for file in csv_files]
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()


            
# Fonction pour récupérer le dernier fichier CSV en fonction de la date
def get_latest_csv_file(folder_path):
    csv_files = sorted(Path(folder_path).glob("*.csv"), reverse=True)
    date_pattern = re.compile(r"FORM_(\d{4}-\d{2}-\d{2})_\d{6}\.csv")
    
    latest_files = []
    for file in csv_files:
        match = date_pattern.search(file.name)
        if match:
            latest_files.append(file)
        if len(latest_files) == 2:
            break

    latest_dataframes = [load_csv(file) for file in latest_files]
    return latest_dataframes if len(latest_dataframes) == 2 else [latest_dataframes[0], None]


# Fonction pour calculer les moyennes par style de nage et distance cumulée
def calculate_mean(df, group_by_cols, mean_cols):
    return df.groupby(group_by_cols, as_index=False)[mean_cols].mean()

# Fonction pour afficher un graphique de type line plot
def plot_line_chart(df, x_col, y_col, color_col, title, labels):
    fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title, labels=labels)
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, use_container_width=True)

# Fonction pour afficher un graphique de type box plot
def plot_box_chart(df, x_col, y_col, title):
    fig = px.box(df, x=x_col, y=y_col, title=title)
    st.plotly_chart(fig, use_container_width=True)

# Fonction pour afficher les métriques de performance
def display_kpi_metrics(df):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Distance Totale", f"{df['Dist (m)'].sum()}m")
    with col2:
        avg_hr = df[df['Avg BPM (moving)'] > 0]['Avg BPM (moving)'].mean()
        st.metric("FC Moyenne", f"{avg_hr:.0f} bpm")
    with col3:
        st.metric("FC Max", f"{df['Max BPM'].max()} bpm")
    with col4:
        avg_swolf = df[df['SWOLF'] > 0]['SWOLF'].mean()
        st.metric("SWOLF Moyen", f"{avg_swolf:.1f}")

# Fonction pour afficher la page d'accueil
def display_home_page():
    st.header("Bienvenue sur l'outil d'analyse de sessions de natation")
    st.write("Utilisez le menu pour naviguer entre les pages.")

# Fonction pour afficher la page de visualisation de l'évolution du temps par distance cumulée
def display_evolution_chart(df):
    df = df[df['Dist (m)'] > 0].copy()
    mean_df = calculate_mean(df, group_by_cols=['Strk', 'Cumul Dist (m)'], mean_cols=['Seconds_per_50m', 'Dist (m)'])
    plot_line_chart(mean_df, 
                    x_col='Cumul Dist (m)', 
                    y_col='Seconds_per_50m', 
                    color_col='Strk', 
                    title="Temps par 50m vs Distance cumulée (moyenne)",
                    labels={
                        'Cumul Dist (m)': 'Distance cumulée (m)',
                        'Seconds_per_50m': 'Temps par 50m (secondes)',
                        'Strk': 'Style de nage'
                    })

# Fonction pour afficher la page KPI
def display_kpi_page(df_latest,df_second_latest):
    st.header("Indicateurs Clés de Performance (KPI)")

    # KPIs pour la dernière session
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.subheader("Dernière Session")
        st.metric("Distance Totale", f"{df_latest['Dist (m)'].sum()}m")
        avg_hr_latest = df_latest[df_latest['Avg BPM (moving)'] > 0]['Avg BPM (moving)'].mean()
        st.metric("FC Moyenne", f"{avg_hr_latest:.0f} bpm")
        st.metric("FC Max", f"{df_latest['Max BPM'].max()} bpm")
        avg_swolf_latest = df_latest[df_latest['SWOLF'] > 0]['SWOLF'].mean()
        st.metric("SWOLF Moyen", f"{avg_swolf_latest:.1f}")

    # Calcul du temps total de repos pour la dernière session
    rest_time_latest = df_latest['Rest Time (s)'].sum()

    # KPIs pour l'avant-dernière session (si disponible)
    if df_second_latest is not None:
        with col2:
            st.subheader("Avant-dernière Session")
            st.metric("Distance Totale", f"{df_second_latest['Dist (m)'].sum()}m")
            avg_hr_second = df_second_latest[df_second_latest['Avg BPM (moving)'] > 0]['Avg BPM (moving)'].mean()
            st.metric("FC Moyenne", f"{avg_hr_second:.0f} bpm")
            st.metric("FC Max", f"{df_second_latest['Max BPM'].max()} bpm")
            avg_swolf_second = df_second_latest[df_second_latest['SWOLF'] > 0]['SWOLF'].mean()
            st.metric("SWOLF Moyen", f"{avg_swolf_second:.1f}")

        # Calcul du temps total de repos pour l'avant-dernière session
        rest_time_second_latest = df_second_latest['Rest Time (s)'].sum()
        
        # Comparaison des KPIs y compris le temps de repos
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Comparaison des sessions")
            st.metric("Différence Distance Totale", f"{df_latest['Dist (m)'].sum() - df_second_latest['Dist (m)'].sum()}m")
            st.metric("Différence FC Moyenne", f"{avg_hr_latest - avg_hr_second:.0f} bpm")
            st.metric("Différence FC Max", f"{df_latest['Max BPM'].max() - df_second_latest['Max BPM'].max()} bpm")
            st.metric("Différence SWOLF", f"{avg_swolf_latest - avg_swolf_second:.1f}")
            st.metric("Différence Temps de Repos", f"{rest_time_latest - rest_time_second_latest:.1f} secondes")



# Créer l'application
def create_app(folder_path):
    st.set_page_config(page_title="Analyse Natation", layout="wide")
    st.title("Analyse de Session de Natation")

    # Menu de navigation
    with st.sidebar:
        selected = option_menu("Menu", ["Home", "All Sessions", "Latest's Session"],
                               icons=["house", "bar-chart-line-fill", "tsunami"],
                               menu_icon="menu", default_index=0)

    # Charger et traiter les données
    df_all = combine_csv_files(folder_path)
    df_latest, df_second_latest = get_latest_csv_file(folder_path)

    # Gestion de la navigation entre les pages
    if selected == "Home":
        display_home_page()
    elif selected == "All Sessions":
        display_evolution_chart(df_all)
    elif selected == "Latest's Session":
        display_kpi_page(df_latest,df_second_latest)

# Exécution de l'application
if __name__ == "__main__":
    create_app( Path(__file__).parent / "./DATA/")
