import plotly.graph_objects as go
import plotly.offline as opy
from nat_state_vis_app import settings
from django.shortcuts import render
from core.utils.data_loader import load_uof_data, load_sovereignty_data, load_democracy_data, get_questions
from core.utils.sankey_utils import create_uof_sankey_figure, create_issue_demscore_sankey_figure
from core.utils.scatter_utils import create_uof_scatter_figure, create_by_state_scatter_figure
from core.utils.html_utils import generate_sankey_html, generate_plot_html, generate_error_html
from core.utils.parallel_categories_utils import create_parallel_categories_figure
from core.utils.data_loader import load_membership_data
from core.utils.members_comparison_utils import create_eu_comparison_table
from core.utils.sunburst_utils import create_uofq8_sunburst_figure
from core.utils.data_loader import load_nato_data
from core.utils.sankey_utils import create_uof_art51_nato_sankey
from core.utils.html_utils import generate_sunburst_html
from core.utils.data_loader import load_nonintervention_data
# from core.utils.state_comparison_utils import create_state_comparison_table
from core.utils.data_loader import load_uof_transposed_data
from core.utils.members_comparison_utils import create_eu_non_members_comparison_table


# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def methodology(request):
    return render(request, 'core/methodology.html')

def use_of_force(request):
    return render(request, 'core/uof.html')


def sovereignty(request):
    return render(request, 'core/sovereignty.html')

def nonintervention(request):
    return render(request, 'core/nonintervention.html')


def uof_sankey(request):
    try:
        df = load_uof_data()
        fig = create_uof_sankey_figure(df)
        sankey_html = generate_sankey_html(fig)
        return render(request, 'core/uof_sankey.html', {'uof_sankey': sankey_html})
    except Exception as e:
        return render(request, 'core/uof_sankey.html', {
            'uof_sankey': generate_error_html(str(e))
        })


def uof_demscore_sankey(request):
    try:
        df_uof = load_uof_data()
        df_dem = load_democracy_data()
        fig = create_issue_demscore_sankey_figure(df_uof, df_dem)
        sankey_html = generate_plot_html(fig)
        return render(request, 'core/uof_demscore_sankey.html', {
            'uof_demscore_sankey': sankey_html
        })
    except Exception as e:
        return render(request, 'core/uof_demscore_sankey.html', {
            'uof_demscore_sankey': generate_error_html(str(e))
        })


def uof_scatter(request):
    try:
        df = load_uof_data()
        preguntas = get_questions(df)
        fig = create_uof_scatter_figure(df, preguntas)
        plot_div = fig.to_html(full_html=False, config={'responsive': True})
        return render(request, 'core/uof_scatter.html', {'uof_scatter': plot_div})
    except Exception as e:
        return render(request, 'core/uof_scatter.html', {
            'uof_scatter': generate_error_html(str(e))
        })


def uof_by_state_scatter(request):
    try:
        df_uof = load_uof_data()
        preguntas_uof = get_questions(df_uof)
        estados = df_uof['State'].unique()
        fig = create_by_state_scatter_figure(df_uof, preguntas_uof, estados)
        plot_div = fig.to_html(full_html=False, config={'responsive': True})
        return render(request, 'core/uof_by_state_scatter.html', {
            'uof_by_state_scatter': plot_div,
            'states_count': len(estados),
            'questions_count': len(preguntas_uof)
        })
    except Exception as e:
        return render(request, 'core/uof_by_state_scatter.html', {
            'uof_by_state_scatter': generate_error_html(str(e))
        })


def uof_sov_parallel_categories(request):
    try:
        df_uof = load_uof_data()
        df_sov = load_sovereignty_data()
        questions_uof = get_questions(df_uof)
        questions_sov = get_questions(df_sov)
        fig = create_parallel_categories_figure(df_uof, df_sov, questions_uof, questions_sov)
        plot_html = generate_plot_html(fig)
        return render(request, 'core/uof_sov_parallel_categories.html', {
            'uof_sov_parallel_categories': plot_html
        })
    except Exception as e:
        return render(request, 'core/uof_sov_parallel_categories.html', {
            'uof_sov_parallel_categories': generate_error_html(str(e))
        })


def eu_comparison_uof_view(request):
    # Cargar datos
    df_uof = load_uof_data()
    df_membresia = load_membership_data()
    questions_uof = get_questions(df_uof)

    # Crear la tabla
    tabla_fig = create_eu_comparison_table(df_uof, questions_uof, df_membresia)
    tabla_fig = opy.plot(tabla_fig, output_type='div', include_plotlyjs=False)

    return render(request, 'core/uof_eu_members.html', {
        'uof_eu_members_table': tabla_fig})

def eu_comparison_sov_view(request):
    # Cargar datos
    df_sov = load_sovereignty_data()
    df_membresia = load_membership_data()
    questions_sov = get_questions(df_sov)

    # Crear la tabla
    tabla_fig = create_eu_comparison_table(df_sov, questions_sov, df_membresia)
    tabla_fig = opy.plot(tabla_fig, output_type='div', include_plotlyjs=False)

    return render(request, 'core/sov_eu_members.html', {
        'sov_eu_members_table': tabla_fig})

def eu_non_eu_comparison_sov_view(request):
    # Cargar datos
    df_sov = load_sovereignty_data()
    df_membresia = load_membership_data()
    questions_sov = get_questions(df_sov)

    # Crear la tabla
    tabla_fig = create_eu_non_members_comparison_table(df_sov, questions_sov, df_membresia)
    tabla_fig = opy.plot(tabla_fig, output_type='div', include_plotlyjs=False)

    return render(request, 'core/sov_eu_non_eu_members.html', {
        'sov_eu_non_eu_members_table': tabla_fig})

def state_comparison_view(request):
    # Cargar datos
    df_uof = load_uof_transposed_data()
    questions_uof = get_questions(df_uof)
    # Crear la tabla
    tabla_fig = create_state_comparison_table(df_uof, questions_uof)
    tabla_fig = opy.plot(tabla_fig, output_type='div', include_plotlyjs=False)

    return render(request, 'core/uof_state_comparison.html', {
        'uof_state_comparison': tabla_fig})


def uof_q8_nato_sankey(request):
    try:
        df_uof = load_uof_data()
        df_nato = load_nato_data()
        fig = create_uof_art51_nato_sankey(df_uof, df_nato)
        sankey_html = generate_plot_html(fig)
        return render(request, 'core/uof_q8_nato_sankey.html', {
            'uof_q8_sankey': sankey_html
        })
    except Exception as e:
        return render(request, 'core/uof_q8_nato_sankey.html', {
            'uof_q8_sankey': generate_error_html(str(e))
        })


def sovereignty_sankey(request):
    try:
        df = load_sovereignty_data()
        fig = create_uof_sankey_figure(df)
        sankey_html = generate_sankey_html(fig)
        return render(request, 'core/sovereignty_sankey.html', {'sovereignty_sankey': sankey_html})
    except Exception as e:
        return render(request, 'core/sovereignty_sankey.html', {
            'sovereignty_sankey': generate_error_html(str(e))
        })


def sov_demscore_sankey(request):
    try:
        df_uof = load_sovereignty_data()
        df_dem = load_democracy_data()
        fig = create_issue_demscore_sankey_figure(df_uof, df_dem)
        sankey_html = generate_plot_html(fig)
        return render(request, 'core/sov_demscore_sankey.html', {
            'sov_demscore_sankey': sankey_html
        })
    except Exception as e:
        return render(request, 'core/sov_demscore_sankey.html', {
            'sov_demscore_sankey': generate_error_html(str(e))
        })


def nonintervention_sankey(request):
    try:
        df = load_nonintervention_data()
        fig = create_uof_sankey_figure(df)
        sankey_html = generate_sankey_html(fig)
        return render(request, 'core/nonintervention_sankey.html', {'nonintervention_sankey': sankey_html})
    except Exception as e:
        return render(request, 'core/nonintervention_sankey.html', {
            'nonintervention_sankey': generate_error_html(str(e))
        })


def nonintervention_demscore_sankey(request):
    try:
        df_uof = load_nonintervention_data()
        df_dem = load_democracy_data()
        fig = create_issue_demscore_sankey_figure(df_uof, df_dem)
        sankey_html = generate_plot_html(fig)
        return render(request, 'core/nonint_demscore_sankey.html', {
            'nonint_demscore_sankey': sankey_html
        })
    except Exception as e:
        return render(request, 'core/nonint_demscore_sankey.html', {
            'nonint_demscore_sankey': generate_error_html(str(e))
        })


def sovereignty_by_state_scatter(request):
    try:
        df_sov = load_sovereignty_data()
        preguntas_sov = get_questions(df_sov)
        estados = df_sov['State'].unique()
        fig = create_by_state_scatter_figure(df_sov, preguntas_sov, estados)
        plot_div = fig.to_html(full_html=False, config={'responsive': True})
        return render(request, 'core/sov_by_state_scatter.html', {
            'sov_by_state_scatter': plot_div,
            'states_count': len(estados),
            'questions_count': len(preguntas_sov)
        })
    except Exception as e:
        return render(request, 'core/sov_by_state_scatter.html', {
            'sov_by_state_scatter': generate_error_html(str(e))
        })