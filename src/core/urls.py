from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('uof', views.use_of_force, name='use_of_force'),
    path('uof-sankey', views.uof_sankey, name='uof_sankey'),
    path('uof-demscore-sankey', views.uof_demscore_sankey, name='uof_demscore_sankey'),
    path('uof-scatter', views.uof_scatter, name='uof_scatter'),
    path('uof-by-state-scatter', views.uof_by_state_scatter, name='uof_by_state_scatter'),

]