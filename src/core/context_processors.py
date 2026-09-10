from django.conf import settings


def visualizations_ready(request):
    """
    Makes settings.VISUALIZATIONS_READY available in every template
    as `vis_ready`, e.g. {% if vis_ready.self_defense %}.

    In settings.py:

        VISUALIZATIONS_READY = {
            'use_of_force': False,     # hidden -> shows "Under Construction"
            'sovereignty': True,
            'nonintervention': True,
            'self_defense': False,     # hidden -> shows "Under Construction"
        }
    """
    return {
        'vis_ready': getattr(settings, 'VISUALIZATIONS_READY', {})
    }
