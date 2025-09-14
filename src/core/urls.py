from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('uof', views.use_of_force, name='use_of_force'),
    path('sovereignty', views.sovereignty, name='sovereignty'),
    path('nonintervention', views.nonintervention, name='nonintervention'),
    path('uof-sankey', views.uof_sankey, name='uof_sankey'),
    path('uof-demscore-sankey', views.uof_demscore_sankey, name='uof_demscore_sankey'),
    path('uof-scatter', views.uof_scatter, name='uof_scatter'),
    path('uof-by-state-scatter', views.uof_by_state_scatter, name='uof_by_state_scatter'),
    path('uof-sovereignty-parallel-categories', views.uof_sov_parallel_categories, name='uof_sov_parallel_categories'),
    path('uof-eu-states-to-eu', views.eu_comparison_view, name='uof_eu_states_to_eu'),
    path('uof-art51-nato-sankey', views.uof_q8_nato_sankey, name='uof_q8_nato_sankey'),
    path('sovereignty-sankey', views.sovereignty_sankey, name='sovereignty_sankey'),
    path('sov-demscore-sankey', views.sov_demscore_sankey, name='sov_demscore_sankey'),

]