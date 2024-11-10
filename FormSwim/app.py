
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def load_and_process_data(data_string):
    # Sauter les 3 premières lignes et lire le CSV
    df = pd.read_csv(data_string,header=2)
    
    # Filtrer uniquement les longueurs (pas les repos)
    #df_active = df[df['Dist (m)'] > 0].copy()
    
    # Convertir les temps en secondes pour les calculs
    df['Seconds_per_50m'] = df['Pace/50'].apply(lambda x: 
        sum(float(x) * 60**i for i, x in enumerate(reversed(str(x).split(':')))) if pd.notna(x) else None)
    
    return df

def create_app(data_string):
    st.set_page_config(page_title="Analyse Natation", layout="wide")
    st.title("Analyse de Session de Natation")
    
    # Charger et traiter les données
    df = load_and_process_data(data_string)

    # Métriques globales
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
    df_test = df[df['Dist (m)'] > 0].copy()
    # Graphique temps par 50m vs distance cumulée
    st.subheader("Évolution du temps par 50m en fonction de la distance cumulée")
    fig = px.line(df_test, 
                  x='Cumul Dist (m)', 
                  y='Seconds_per_50m',
                  color='Strk',
                  title="Temps par 50m vs Distance cumulée",
                  labels={
                      'Cumul Dist (m)': 'Distance cumulée (m)',
                      'Seconds_per_50m': 'Temps par 50m (secondes)',
                      'Strk': 'Style de nage'
                  })
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse par style de nage
    st.subheader("Analyse par style de nage")
    col1, col2 = st.columns(2)
    
    with col1:
        style_stats = df.groupby('Strk').agg({
            'Dist (m)': 'sum',
            'Seconds_per_50m': 'mean',
            'SWOLF': 'mean',
            'Strk Count': 'mean'
        }).round(2)
        st.dataframe(style_stats)
    
    with col2:
        # Distribution des SWOLF par style
        fig_swolf = px.box(df[df['SWOLF'] > 0], 
                          x='Strk', 
                          y='SWOLF',
                          title="Distribution des SWOLF par style")
        st.plotly_chart(fig_swolf)
    
    # Évolution de la fréquence cardiaque
    st.subheader("Évolution de la fréquence cardiaque")

    fig_hr = px.line(df[df['Avg BPM (moving)'] > 0], 
                     x='Cumul Dist (m)',
                     y=['Avg BPM (moving)', 'Max BPM'],
                     title="Évolution de la FC pendant la session")
    st.plotly_chart(fig_hr, use_container_width=True)
    
    # Analyse des temps de repos
    st.subheader("Analyse des temps de repos")
    rest_times = df['Rest Time'].apply(lambda x: 
        sum(float(x) * 60**i for i, x in enumerate(reversed(str(x).split(':')))))


    fig_rest = px.histogram(rest_times[rest_times!=0],
                           title="Distribution des temps de repos",
                                  x ='Rest Time' , nbins=10)
    
    st.plotly_chart(fig_rest, use_container_width=True)

# Pour exécuter l'application
if __name__ == "__main__":
    create_app("./DATA/FORM_2024-11-07_122351.csv")
