# utils/data_loader.py
import pandas as pd
from django.conf import settings

def load_uof_data():
    """Carga los datos de Use of Force"""
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    df = pd.read_csv(uof_data)
    df = df.rename(columns={'ISO': 'iso'})
    return df

def load_sovereignty_data():
    """Carga los datos de Sovereignty"""
    sovereignty_data = settings.BASE_DIR / 'data' / 'sovereignty-aug2025.csv'
    df = pd.read_csv(sovereignty_data)
    return df

def load_democracy_data():
    """Carga los datos de Democracy Index"""
    dem_score_data = settings.BASE_DIR / 'data' / 'democracy-index-eiu.csv'
    df_dem = pd.read_csv(dem_score_data)
    df_dem = df_dem.rename(columns={'Year': 'year', 'Code': 'iso', 'Democracy score': 'dem_score'})
    most_recent_year = df_dem['year'].max()
    df_dem = df_dem[df_dem['year'] == most_recent_year]
    return df_dem

def get_uof_questions(df_uof):
    """Obtiene las preguntas de Use of Force"""
    return list(df_uof.columns[2:18])

def get_sovereignty_questions(df_sov):
    """Obtiene las preguntas de Sovereignty"""
    return list(df_sov.columns[2:35])