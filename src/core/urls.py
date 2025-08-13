from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('uof', views.use_of_force, name='use_of_force'),
    path('uof-sankey', views.uof_sankey, name='uof_sankey'),
    path('uof-demscore-sankey', views.uof_demscore_sankey, name='uof_demscore_sankey'),

]