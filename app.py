import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go
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
    fig1 = px.line(df, x=x_col, y=y_col, color=color_col, title=title, labels=labels,markers=True,hover_data={'Rest Time (s)': True,'Strk':False,'Cumul Dist (m)':True,'Seconds_per_50m':False})
    fig1.update_traces(mode='lines+markers')
    fig1.update_traces(
        marker=dict(
            size=df['Rest Time (s)'],  # Taille des points basée sur 'Rest Time (s)'
            sizemode='diameter',           # Mode de taille (vous pouvez ajuster avec 'diameter' si besoin)
            sizeref=max(df['Rest Time (s)']) / 20,  # Facteur de normalisation
            color='white' # Coloration en fonction de 'Rest Time (s)' aussi si souhaité
        ),
        text=df['Rest Time (s)'],        # Texte d'annotation avec 'Rest Time (s)' sur chaque point
        textposition="top center"        # Position du texte d'annotation
    )
    st.plotly_chart(fig1, use_container_width=True)

# Fonction pour afficher un graphique de type box plot
def plot_box_chart(df, x_col, y_col, title):
    fig2 = px.box(df, x=x_col, y=y_col, title=title)
    st.plotly_chart(fig2, use_container_width=True)

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
def display_home_page(df_all,df_latest):
    st.header("Bienvenue sur l'outil d'analyse de sessions de natation")
    st.write("Utilisez le menu pour naviguer entre les pages.")

    avg_hr_latest = df_all[df_all['Avg BPM (moving)'] > 0]['Avg BPM (moving)'].mean()
    avg_swolf_latest = df_all[df_all['SWOLF'] > 0]['SWOLF'].mean()
    rest_time_latest = df_all['Rest Time (s)'].sum()
    avg_hr_second = df_latest[df_latest['Avg BPM (moving)'] > 0]['Avg BPM (moving)'].mean()
    avg_swolf_second = df_latest[df_latest['SWOLF'] > 0]['SWOLF'].mean()
    rest_time_second_latest = df_latest['Rest Time (s)'].sum()
    rest_time_second_latest_count = df_latest[df_latest['Rest Time (s)'] > 0.0]['Rest Time (s)'].count()
    rest_time_latest_count = df_all[df_all['Rest Time (s)'] > 0.0]['Rest Time (s)'].count()
  

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Distance Totale", f"{df_all['Dist (m)'].sum():,} m".replace(",", " "),f"{df_latest['Dist (m)'].sum():,} m".replace(",", " "))
    with col2:
        st.metric("BPM Moyenne", f"{avg_hr_latest:.0f}",f"{avg_hr_second:.0f} bpm",delta_color ="inverse")
    with col3:
        st.metric("BPM Max",df_all['Max BPM'].max(), f"{df_latest['Max BPM'].max()} bpm",delta_color ="inverse")
    with col4:
        st.metric("SWOLF", f"{avg_swolf_latest:.0f}",f"{avg_swolf_second:.1f}",delta_color ="inverse")
    with col5:
        st.metric("Temps de Repos", f"{rest_time_latest/ 60:.0f} min",f"{rest_time_second_latest/60:.0f} m",delta_color ="inverse")
    with col6:
        st.metric("Nombre de Repos", rest_time_latest_count,f"{rest_time_second_latest_count:.0f}",delta_color ="inverse")
 

# Fonction pour afficher la page de visualisation de l'évolution du temps par distance cumulée
def display_evolution_chart(df):
    
    stroke_type = st.selectbox(
        'Choix du type de nage',
        options=['FR', 'BR'],
        help="FR = Freestyle, BR = Breaststroke",
        label_visibility="visible"
    )
    

    df_test2 = df.copy()
    df_test2[['Rest Time (s)']]  = df_test2[['Rest Time (s)']].shift(-1)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Distance Totale", f"{df[df['Strk'] == stroke_type]['Length (m)'].sum():,} m".replace(",", " "))
    with col2:
        st.metric("BPM Moyenne", f"{df[(df['Strk'] == stroke_type) & (df['Avg BPM (moving)'] > 0)]['Avg BPM (moving)'].mean():.0f}",delta_color ="inverse")
    with col3:
        st.metric("BPM Max", f"{df[(df['Strk'] == stroke_type) & (df['Avg BPM (moving)'] > 0)]['Avg BPM (moving)'].max():.0f}",delta_color ="inverse")
    with col4:
        st.metric("SWOLF", f"{df[(df['Strk'] == stroke_type) & (df['SWOLF'] > 0)]['SWOLF'].mean():.0f}",delta_color ="inverse")
    with col5:
        st.metric("Temps de repos", f"{df_test2[(df_test2['Strk'] == stroke_type) & (df_test2['Rest Time (s)'] > 0)]['Rest Time (s)'].mean():.0f} s",delta_color ="inverse")
    with col6:
        st.metric("Nombre de repos", f"{df_test2[(df_test2['Strk'] == stroke_type) & (df_test2['Rest Time (s)'] > 0)]['Rest Time (s)'].count():.0f}",delta_color ="inverse")
    
    

    # Graphique temps par 50m vs distance cumulée

    df_test = df.copy()
    df_test[['Rest Time (s)']]  = df_test[['Rest Time (s)']].shift(-1)
    df_test = df_test.fillna(0)
    df_test = df_test[df_test['Strk'] != 'REST']
    df_test = df_test.groupby(['Cumul Dist (m)','Strk'], as_index=False)[['Seconds_per_50m','Rest Time (s)','Strk Count']].mean()
    df_test = df_test[df_test['Strk'] == stroke_type]
    plot_line_chart(df_test, 'Cumul Dist (m)', 'Seconds_per_50m', 'Strk', 
                    "Temps par 50m vs Distance cumulée",
                    labels={'Cumul Dist (m)': 'Distance cumulée (m)', 'Seconds_per_50m': 'Temps par 50m (secondes)', 'Strk': 'Style de nage'})


    
 

    fig = go.Figure()
    df_test = df_test[df_test['Strk'] == stroke_type]
    df_test.reset_index(inplace=True)
    # Calculate whether strokes increased or decreased
    for i in range(len(df_test) - 1):
        current_strokes = df_test['Strk Count'][i]
        next_strokes = df_test['Strk Count'][i + 1]
        
        # Determine color based on whether strokes increased or decreased
        color = 'red' if next_strokes > current_strokes else 'green'
        
        # Add line segment
        fig.add_trace(
            go.Scatter(
                x=df_test['Cumul Dist (m)'][i:i+2],
                y=df_test['Strk Count'][i:i+2],
                mode='lines',
                line=dict(
                    color=color,
                    width=3
                ),
                showlegend=False,
                hovertemplate=(
                    'Cumul Dist (m): %{x}<br>'
                    'Strk Count: %{y}<br>'
                    f'Change: {"Increased" if color == "red" else "Decreased"}<br>'
                    '<extra></extra>'
                )
            )
        )
    
    # Add markers for each point
    fig.add_trace(
        go.Scatter(
            x=df_test['Cumul Dist (m)'],
            y=df_test['Strk Count'],
            mode='markers',
            marker=dict(
                color='blue',
                size=10
            ),
            name='Stroke Count',
            hovertemplate=(
                'Cumul Dist (m): %{x}<br>'
                'Strk Count: %{y}<br>'
                '<extra></extra>'
            )
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Stroke Count Analysis by Pool Length',
        xaxis_title='Pool Length Number',
        yaxis_title='Number of Strokes',
        hovermode='closest',
        height=600,
    )
    
    # Add custom legend for color meaning
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='red', width=3),
            name='Strokes Increased'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='green', width=3),
            name='Strokes Decreased'
        )
    )
    st.plotly_chart(fig, use_container_width=True)





# Fonction pour afficher la page KPI
def display_kpi_page(df_latest,df_second_latest):

    
    stroke_type = st.selectbox(
        'Choix du type de nage',
        options=df_latest['Strk'][df_latest['Strk'] != 'REST'].unique(),
        help="FR = Freestyle, BR = Breaststroke",
        label_visibility="visible"
    )

    # Graphique temps par 50m vs distance cumulée
    st.subheader("Évolution du temps par 50m en fonction de la distance cumulée")
    df_test = df_latest.copy()
    df_test[['Rest Time (s)']]  = df_test[['Rest Time (s)']].shift(-1)
    df_test = df_test.fillna(0)
    df_test = df_test[df_test['Strk'] == stroke_type]
    
    plot_line_chart(df_test, 'Cumul Dist (m)', 'Seconds_per_50m', 'Strk', 
                    "Temps par 50m vs Distance cumulée",
                    labels={'Cumul Dist (m)': 'Distance cumulée (m)', 'Seconds_per_50m': 'Temps par 50m (secondes)', 'Strk': 'Style de nage'})



    fig = go.Figure()
    
    # Calculate whether strokes increased or decreased
    
    df_latest2 = df_latest[df_latest['Strk'] == stroke_type]
    df_latest2.reset_index(inplace=True)

    for i in range(len(df_latest2) - 1):
        current_strokes = df_latest2['Strk Count'][i]
        next_strokes = df_latest2['Strk Count'][i + 1]
        
        # Determine color based on whether strokes increased or decreased
        color = 'red' if next_strokes > current_strokes else 'green'
        
        # Add line segment
        fig.add_trace(
            go.Scatter(
                x=df_latest2['Cumul Dist (m)'][i:i+2],
                y=df_latest2['Strk Count'][i:i+2],
                mode='lines',
                line=dict(
                    color=color,
                    width=3
                ),
                showlegend=False,
                hovertemplate=(
                    'Cumul Dist (m): %{x}<br>'
                    'Strk Count: %{y}<br>'
                    f'Change: {"Increased" if color == "red" else "Decreased"}<br>'
                    '<extra></extra>'
                )
            )
        )
    
    # Add markers for each point
    fig.add_trace(
        go.Scatter(
            x=df_latest2['Cumul Dist (m)'],
            y=df_latest2['Strk Count'],
            mode='markers',
            marker=dict(
                color='blue',
                size=10
            ),
            name='Stroke Count',
            hovertemplate=(
                'Cumul Dist (m): %{x}<br>'
                'Strk Count: %{y}<br>'
                '<extra></extra>'
            )
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Stroke Count Analysis by Pool Length',
        xaxis_title='Pool Length Number',
        yaxis_title='Number of Strokes',
        hovermode='closest',
        height=600,
    )
    
    # Add custom legend for color meaning
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='red', width=3),
            name='Strokes Increased'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='green', width=3),
            name='Strokes Decreased'
        )
    )
    st.plotly_chart(fig, use_container_width=True)



    # Analyse par style de nage
    st.subheader("Analyse par style de nage")
    df_latest_test = df_latest[df_latest['Dist (m)'] > 0].copy()
    style_stats = df_latest_test.groupby('Strk').agg({
        'Dist (m)': 'sum',
        'Seconds_per_50m': 'mean',
        'SWOLF': 'mean',
        'Strk Count': 'mean'
    }).round(2)
    st.dataframe(style_stats)

    plot_box_chart(df_latest[df_latest['SWOLF'] > 0], 'Strk', 'SWOLF', "Distribution des SWOLF par style")

    # Évolution de la fréquence cardiaque
    st.subheader("Évolution de la fréquence cardiaque")
    fig_hr = px.line(df_latest[df_latest['Avg BPM (moving)'] > 0], 
                     x='Cumul Dist (m)',
                     y=['Avg BPM (moving)', 'Max BPM'],
                     title="Évolution de la FC pendant la session")
    st.plotly_chart(fig_hr, use_container_width=True)

    # Analyse des temps de repos
    st.subheader("Analyse des temps de repos")
    rest_times = df_latest['Rest Time'].apply(lambda x: 
        sum(float(part) * 60**i for i, part in enumerate(reversed(str(x).split(':')))) if pd.notna(x) else None)

    fig_rest3 = px.histogram(rest_times[rest_times!=0],
                           title="Distribution des temps de repos",
                                  x ='Rest Time' , nbins=10)
    
    st.plotly_chart(fig_rest3, use_container_width=True)




   

  


# Créer l'application
def create_app(folder_path):
    
    st.set_page_config(page_title="KPI'S FormSwim", layout="wide",initial_sidebar_state="expanded")
    # Menu de navigation
    selected = option_menu(
    menu_title="Menu",
    options=["Home", "All Sessions", "Latest's Session"],
    icons=["house", "bar-chart-line-fill", "tsunami"],
    menu_icon="menu",
    default_index=0,
    orientation="horizontal"
    )

    
  

    # Charger et traiter les données
    df_all = combine_csv_files(folder_path)
    df_latest, df_second_latest = get_latest_csv_file(folder_path)

    # Gestion de la navigation entre les pages
    if selected == "Home":
        display_home_page(df_all,df_latest)
    elif selected == "All Sessions":
        display_evolution_chart(df_all)
    elif selected == "Latest's Session":
        display_kpi_page(df_latest,df_second_latest)

# Exécution de l'application
if __name__ == "__main__":
    create_app( Path(__file__).parent / "./DATA/")
