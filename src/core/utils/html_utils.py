# utils/html_utils.py

def generate_sankey_html(fig):
    """Genera HTML con estilos para gráficos Sankey"""
    sankey_html = fig.to_html(
        full_html=False,
        config={'responsive': True, 'displayModeBar': True},
        include_plotlyjs='cdn'
    )

    return f"""
    <div style="
        width: 100%;
        overflow: auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
    ">
        {sankey_html}
    </div>
    """


def generate_plot_html(fig):
    """Genera HTML con estilos para gráficos generales"""
    plot_html = fig.to_html(
        full_html=False,
        config={'responsive': True, 'displayModeBar': True},
        include_plotlyjs='cdn'
    )

    return f"""
    <div style="
        width: 100%;
        overflow: auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
    ">
        {plot_html}
    </div>
    """


def generate_error_html(error_message):
    """Genera HTML para mostrar errores"""
    return f"""
    <div style="
        padding: 20px;
        background: #ffebee;
        border: 1px solid #f44336;
        border-radius: 8px;
        color: #c62828;
        margin: 20px;
    ">
        <h3>Error al cargar el gráfico</h3>
        <p>{error_message}</p>
    </div>
    """