# utils/data_loader.py
import pandas as pd
from django.conf import settings

def load_uof_data():
    """Carga los datos de Use of Force"""
    uof_data = settings.BASE_DIR / 'data' / 'uof-sept2025.csv'
    df = pd.read_csv(uof_data)
    df = df.rename(columns={'ISO': 'iso'})
    return df

def load_sovereignty_data():
    """Carga los datos de Sovereignty"""
    sovereignty_data = settings.BASE_DIR / 'data' / 'sovereignty-sept2025.csv'
    df = pd.read_csv(sovereignty_data)
    df = df.rename(columns={'ISO': 'iso'})
    return df

def load_nonintervention_data():
    """Carga los datos de Sovereignty"""
    sovereignty_data = settings.BASE_DIR / 'data' / 'nonintervention-sept2025.csv'
    df = pd.read_csv(sovereignty_data)
    df = df.rename(columns={'ISO': 'iso'})
    return df

def load_membership_data():
    """Carga los datos de Use of Force"""
    eu_states_data = settings.BASE_DIR / 'data' / 'eu-states.csv'
    df = pd.read_csv(eu_states_data)
    df = df.rename(columns={'ISO': 'iso', 'Membership': 'membership'})
    return df

def load_nato_data():
    """Carga los datos de NATO"""
    nato_data = settings.BASE_DIR / 'data' / 'NATO_EU_Member.csv'
    df = pd.read_csv(nato_data)
    df = df.rename(columns={'ISO': 'iso'})
    return df

def load_democracy_data():
    """Carga los datos de Democracy Index"""
    dem_score_data = settings.BASE_DIR / 'data' / 'democracy-index-eiu.csv'
    df_dem = pd.read_csv(dem_score_data)
    df_dem = df_dem.rename(columns={'Year': 'year', 'Code': 'iso', 'Democracy score': 'dem_score'})
    most_recent_year = df_dem['year'].max()
    df_dem = df_dem[df_dem['year'] == most_recent_year]
    return df_dem

def get_questions(df):
    """Obtiene las preguntas de Use of Force"""
    num_col = len(df.columns)
    last_index = num_col + 1
    return list(df.columns[2:last_index])

