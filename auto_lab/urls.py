from django.urls import path
from auto_lab import views

urlpatterns = [
    path('', views.monitor, name='monitor'),
    path('live<int:cs_id_selected>/', views.monitor_selected, name='live_cycle_station'),
    path('experiments', views.experiments, name='experiments'),
    path('add_experiment', views.add_experiment, name='add_experiment'),
    path('import_experiment', views.import_experiment, name='import_experiment'),
    path('add_battery', views.add_battery, name='add_battery'),
    path('form_submit_experiment', views.form_submit_experiment, name='form_submit_experiment'),
    path('form_import_experiment', views.form_import_experiment, name='form_import_experiment'),
    path('form_submit_battery', views.form_submit_battery, name='form_submit_battery'),
    path('graph', views.graph, name='graph'),
    path('validate-profile/', views.validateProfile, name='validate-profile'),
    path('validate-field/', views.validateField, name='validate-field'),
    path('apply-experiments-filters/', views.applyExperimentsFilters, name='apply-experiments-filters'),
    path('csv<int:exp_id_selected>/', views.getCsv, name='csv'),
    path('report<int:exp_id_selected>/', views.getReport, name='report'),
    path('report_template<int:exp_id_selected>/', views.loadReportTemplate, name='report_template'),
    path('preview<int:exp_id_selected>/', views.loadReportTemplate, name='report_template'),
    path('get-new-measures/', views.getNewMeasures, name='get-new-measures'),
    path('translate-measures-names/', views.translateMeasuresNames, name='translate-measures-names'),
    path('get-new-graph/', views.getNewGraph, name='get-new-graph'),
    path('get-profiles/', views.getProfiles, name='get-profiles'),
    path('generate_previews/', views.generatePreviews, name='generate-previews'),
]