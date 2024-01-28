import os, sys
from time import gmtime, strftime, time, localtime
from datetime import datetime, timedelta, timezone
import csv
import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
# from django.core.files.base import ContentFile
# from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import io as pio

from wattrex_cycler_datatypes.comm_data import CommDataMnCmdDataC, CommDataMnCmdTypeE
from wattrex_mn_manager import MN_REQS_CHAN_NAME, MN_DATA_CHAN_NAME
from system_shared_tool import SysShdIpcChanC

from auto_lab.models import Alarm, Battery, Compatibledevices, Computationalunit, \
                                Cyclerstation, Experiment, Extendedmeasures, Genericmeasures, \
                                Instructions, Leadacid, Lithium, Profile, \
                                Redoxelectrolyte, Redoxstack, Devicestatus, Useddevices, \
                                Usedmeasures, Availablemeasures, Detecteddevices
from auto_lab.models_types import Technology_e, Chemistry_Lithium_e, Chemistry_LeadAcid_e, BipolarType_e, \
                         MembraneType_e, ElectrolyteType_e, DeviceType_e, Available_e, ExperimentStatus_e, \
                         DeviceStatus_e, Mode_e, LimitType_e, ConnStatus_e, Polarity_e
from auto_lab.validator import ques
from auto_lab.analyzer import analyzer, stringToInstructions

# Global chan to communicate with the MN
_MN_REQ_CHAN : SysShdIpcChanC = SysShdIpcChanC(name=MN_REQS_CHAN_NAME)
_MN_DATA_CHAN : SysShdIpcChanC = SysShdIpcChanC(name=MN_DATA_CHAN_NAME)

def graph(request):
    someDict = {'equipmentSelected': {'children': 'Empty'}}
    context = {
        'some_dict':someDict,
    }
    return render(request, 'graph.html', context)


def monitor(request, return_render = True):
    live_experiments = Experiment.objects.filter(status__in=['RUNNING', 'PAUSE']).select_related('cs_id')
    live_cycle_stations = []
    for experiment in live_experiments:
        live_cycle_stations.append(experiment.cs_id)

    context = {
        'cycle_stations_on': live_cycle_stations,
    }
    if return_render:
        return render(request, 'monitor.html', context)
    else:
        return context


def monitor_selected(request, cs_id_selected): #TODO: Hacer que si un equipo está desactivado (status != ONLINE) se pueda seguir accediendo a sus experimentos ya que ahora no puedes hacer click en el en la vista de monitor.html
    # print(monitor(request, render = False))
    cycle_stations_on = monitor(request, return_render = False)['cycle_stations_on']
    cycle_station_selected = Cyclerstation.objects.get(cs_id=cs_id_selected)
    experiments_selected = Experiment.objects.filter(cs_id=cs_id_selected).filter(status__in=['RUNNING', 'PAUSE']).order_by('-exp_id').first()
    profile_selected = Profile.objects.get(prof_id=experiments_selected.prof_id.prof_id)

    last_profile_instr = Instructions.objects.order_by('-instr_id').select_related('prof_id').first()

    last_profile_instr = Instructions.objects.filter(prof_id=profile_selected).order_by('-instr_id').first()
    last_meas_instr = Genericmeasures.objects.filter(exp_id=experiments_selected).order_by('-meas_id').select_related('instr_id').first()

    profile_instr = {
        'prof_id': profile_selected.prof_id if profile_selected is not None else None,
        'last_instr': last_meas_instr.instr_id if last_meas_instr is not None else None,
        'total_n_instr': last_profile_instr.instr_id if last_profile_instr is not None else None,
        'instr': f'{last_meas_instr.instr_id.mode}, {last_meas_instr.instr_id.set_point/1000}, {last_meas_instr.instr_id.limit_type}, {last_meas_instr.instr_id.limit_point/1000}' if last_meas_instr is not None else None,
    }
    if experiments_selected is not None:
        different_extended_measures = Extendedmeasures.objects.filter(exp_id=experiments_selected).values_list('used_meas_id', flat=True).distinct()
        different_extended_measures = set(different_extended_measures)
        extended_measures_names = {}
        for ext_meas in different_extended_measures:
            extended_measures_names[ext_meas] = Usedmeasures.objects.get(used_meas_id=ext_meas).custom_name if Usedmeasures.objects.get(used_meas_id=ext_meas).custom_name != None else Usedmeasures.objects.get(used_meas_id=ext_meas).meas_type.meas_name
        context = {
            'cycle_stations_on': cycle_stations_on,
            'experiment_selected': experiments_selected,
            'live_graph': graphLive(experiments_selected.exp_id, time_window=60),
            'used_meas_ids_and_names': json.dumps(extended_measures_names),
            'profile': profile_instr,
        }
        return render(request, 'monitor.html', context)
    else:
        return HttpResponseBadRequest("<h1>Error 400 - Bad request</h1><h3>There are no experiments running or paused on the cycler station selected</h3>")


def form_submit_experiment(request):
    if request.method == 'POST':
        form = request.POST
        print(form)
        newExperiment = Experiment( name=form['expName_input'],
                                    description=form['expDescription_input'],
                                    date_creation=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                                    status='QUEUED',
                                    cs_id=Cyclerstation.objects.get(cs_id=form['expEquipment_input']),
                                    bat_id=Battery.objects.get(bat_id=form['expBattery_input']),
                                  )

        if 'profile_instructions_write' in form or 'profile_instructions_upload' in form:
            profile_method = None
            if 'profile_instructions_write' in form:
                profile_method = 'write'
            elif 'profile_instructions_upload' in form:
                profile_method = 'upload'
            instructions = stringToInstructions(form['profile_instructions_'+profile_method])
            tmp_analyzer = analyzer(instructions)

            newProfile = Profile(   name=form['profName_input_'+profile_method],
                                    description=form['profDescription_input_'+profile_method],
                                    volt_max=tmp_analyzer.volt_max,
                                    volt_min=tmp_analyzer.volt_min,
                                    curr_max=tmp_analyzer.curr_max,
                                    curr_min=tmp_analyzer.curr_min,
                                )
            newProfile.save()
            newExperiment.prof_id = newProfile

            for instr in instructions:
                instr.prof_id = newProfile
                instr.mode = instr.mode.value
                instr.limit_type = instr.limit_type.value
            Instructions.objects.bulk_create(instructions)

        elif 'expProfileSelected_input' in form:
            newExperiment.prof_id = Profile.objects.get(prof_id=form['expProfileSelected_input'])
        else:
            return HttpResponseBadRequest("<h1>Error 400 - Bad request</h1><h3>There is no profile selected</h3>")

        newExperiment.save()

        if form['expBattery_type'] == 'RedoxStack':
            newRedoxElectrolyte = Redoxelectrolyte( exp_id = newExperiment,
                                                    bat_id = Redoxstack.objects.get(bat_id=newExperiment.bat_id),
                                                    polarity = form['expElectrolytePolarity_input'],
                                                    electrolyte_vol = form['expElectrolyteVolume_input'],
                                                    initial_soc = form['expElectrolyteInitialSOC_input'],
                                                    min_flow_rate = form['expElectrolyteMinFlowRate_input'],
                                                    max_flow_rate = form['expElectrolyteMaxFlowRate_input'],
                                                  )
            newRedoxElectrolyte.save()

    urlToBeRedirected = f'/'
    return redirect(urlToBeRedirected)

def form_import_experiment(request):
    MAX_NUMERIC_VALUE = 8388
    form = request.POST

    if request.method == 'POST' and len(request.FILES) > 0:
        extended_measures_selected = form.getlist('expExtendedMeasures_input')
        for x in extended_measures_selected:
            extended_measures_selected[extended_measures_selected.index(x)] = int(x)
        instructions_given = True
        try:
            extended_measures_selected.remove(0)
        except ValueError as e:
            instructions_given = False

        extended_measures_selected_names_and_id = {Measuresdeclaration.objects.get(meas_type=meas_type).meas_name.lower() : meas_type for meas_type in extended_measures_selected}

        stored_time = time()

        profilefile = request.FILES['file_upload']
        file_read = profilefile.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_read, delimiter=',')
        line_count = 0
        ext_meas_csv_columns = {} # {meas_type : column_index}
        generic_meas_csv_columns = {} # {generic_meas_name : column_index}
        ext_meas_list = []
        generic_meas_list = []
        max_instr_id = 0
        for row in csv_reader:
            if line_count == 0:
                for column in row:
                    row[row.index(column)] = column.lower()
                for column in row:
                    if column in extended_measures_selected_names_and_id:
                        ext_meas_csv_columns[extended_measures_selected_names_and_id[column]] = row.index(column)
                    else:
                        if column == 'timestamp':
                            generic_meas_csv_columns['timestamp'] = row.index(column)
                        elif column == 'voltage':
                            generic_meas_csv_columns['voltage'] = row.index(column)
                        elif column == 'current':
                            generic_meas_csv_columns['current'] = row.index(column)
                        elif instructions_given and column == 'instr_id':
                            generic_meas_csv_columns['instr_id'] = row.index(column)

                print(f'Column names are {", ".join(row)}')
            else:
                try:
                    for generic_meas in generic_meas_csv_columns:
                        if generic_meas == 'timestamp':
                            datetime.strptime(row[generic_meas_csv_columns[generic_meas]], '%Y-%m-%d %H:%M:%S.%f')
                        elif generic_meas == 'voltage':
                            if float(row[generic_meas_csv_columns[generic_meas]]) > MAX_NUMERIC_VALUE or float(row[generic_meas_csv_columns[generic_meas]]) < -MAX_NUMERIC_VALUE:
                                raise ValueError
                        elif generic_meas == 'current':
                            if float(row[generic_meas_csv_columns[generic_meas]]) > MAX_NUMERIC_VALUE or float(row[generic_meas_csv_columns[generic_meas]]) < -MAX_NUMERIC_VALUE:
                                raise ValueError
                        elif instructions_given and generic_meas == 'instr_id':
                            if int(row[generic_meas_csv_columns[generic_meas]]) <= 0:
                                raise ValueError
                            else:
                                if int(row[generic_meas_csv_columns[generic_meas]]) > max_instr_id:
                                    max_instr_id = int(row[generic_meas_csv_columns[generic_meas]])
                    for ext_meas in ext_meas_csv_columns:
                        if float(row[ext_meas_csv_columns[ext_meas]]) > MAX_NUMERIC_VALUE or float(row[ext_meas_csv_columns[ext_meas]]) < -MAX_NUMERIC_VALUE:
                            raise ValueError
                except Exception as e:
                    print(e)
                    return HttpResponseBadRequest("<h1>Error 406 - Not Acceptable</h1><h3>Data in csv not valid</h3><img src='https://http.cat/400'>")
            line_count += 1
        print(f'1. Processed {line_count} lines. Elapsed time: {time() - stored_time} seconds')
        line_count = 0
        csv_reader = csv.reader(file_read, delimiter=',')
        # print(profilefile.read().decode('utf-8').splitlines())

        newExperiment = Experiment( name=form['expName_input'],
                                    description=form['expDescription_input'],
                                    date_creation=strftime("%Y-%m-%d %H:%M:%S", localtime()),
                                    date_begin=strftime("%Y-%m-%d %H:%M:%S", localtime()),
                                    date_finish=strftime("%Y-%m-%d %H:%M:%S", localtime()),
                                    status='FINISHED',
                                    cs_id=Cyclerstation.objects.get(name = "Virtual", cs_id = 1),
                                    bat_id=Battery.objects.get(bat_id=form['expBattery_input']),
                                  )

        if 'profile_instructions_write' in form or 'profile_instructions_upload' in form:
            profile_method = None
            if 'profile_instructions_write' in form:
                profile_method = 'write'
            elif 'profile_instructions_upload' in form:
                profile_method = 'upload'
            instructions = stringToInstructions(form['profile_instructions_'+profile_method])
            if max_instr_id > len(instructions):
                return HttpResponseBadRequest("<h1>Error 406 - Not Acceptable</h1><h3>Data in csv not valid</h3><img src='https://http.cat/400'>")
            tmp_analyzer = analyzer(instructions)

            newProfile = Profile(   name=form['profName_input_'+profile_method],
                                    description=form['profDescription_input_'+profile_method],
                                    volt_max=tmp_analyzer.volt_max,
                                    volt_min=tmp_analyzer.volt_min,
                                    curr_max=tmp_analyzer.curr_max,
                                    curr_min=tmp_analyzer.curr_min,
                                )
            newProfile.save()
            newExperiment.prof_id = newProfile

            for instr in instructions:
                instr.prof_id = newProfile
            Instructions.objects.bulk_create(instructions)

        elif 'expProfileSelected_input' in form:
            newExperiment.prof_id = Profile.objects.get(prof_id=form['expProfileSelected_input'])
            if max_instr_id > len(Instructions.objects.filter(prof_id=newExperiment.prof_id).values_list('instr_id', flat=True)):
                return HttpResponseBadRequest("<h1>Error 406 - Not Acceptable</h1><h3>Data in csv not valid</h3><img src='https://http.cat/400'>")
        else:
            return HttpResponseBadRequest("<h1>Error 400 - Bad request</h1><h3>There is no profile selected</h3><img src='https://http.cat/400'>")

        newExperiment.save()

        if form['expBattery_type'] == 'RedoxStack':
            newRedoxElectrolyte = Redoxelectrolyte( exp_id = newExperiment,
                                                    bat_id = newExperiment.bat_id,
                                                    electrolyte_vol = form['expElectrolyteVolume_input'],
                                                    max_flow_rate = form['expElectrolyteMaxFlowRate_input'],
                                                  )
            newRedoxElectrolyte.save()

        stored_time = time()
        for row in csv_reader:
            if line_count != 0:
                new_generic_meas = Genericmeasures(  exp_id = newExperiment,
                                                        meas_id = line_count,
                                                        timestamp = datetime.strptime(row[generic_meas_csv_columns['timestamp']], '%Y-%m-%d %H:%M:%S.%f'),
                                                        instr_id = Instructions.objects.get(prof_id=newExperiment.prof_id, instr_id=int(row[generic_meas_csv_columns['instr_id']])) if instructions_given else Instructions.objects.get(prof_id=newExperiment.prof_id, instr_id=1),
                                                        voltage = int(float(row[generic_meas_csv_columns['voltage']])*1000),
                                                        current = int(float(row[generic_meas_csv_columns['current']])*1000),
                                                    )
                # new_generic_meas.save()
                generic_meas_list.append(new_generic_meas)
                for meas_type in ext_meas_csv_columns:
                    new_ext_meas = Extendedmeasures(   exp_id = newExperiment,
                                                        meas_id = new_generic_meas.meas_id,
                                                        meas_type = Measuresdeclaration.objects.get(meas_type=meas_type),
                                                        value = int(float(row[ext_meas_csv_columns[meas_type]])*1000),
                                                    )
                    ext_meas_list.append(new_ext_meas)

            line_count += 1
        _time = time()
        Genericmeasures.objects.bulk_create(generic_meas_list)
        Extendedmeasures.objects.bulk_create(ext_meas_list)
        print(f'Time taken to bulk: {time() - _time} seconds')
        print(f'2. Processed {line_count} lines. Elapsed time: {time() - stored_time} seconds')

        urlToBeRedirected = f'/experiments'
        return redirect(urlToBeRedirected)
    else:
        return HttpResponseBadRequest("<h1>Error 403</h1><h3>Forbidden</h3><img src='https://http.cat/403'>")

def form_submit_battery(request):
    if request.method == 'POST':
        form = request.POST
        print(form)
        newBattery = Battery(   name=form['batName_input'],
                                description=form['batDescription_input'],
                                manufacturer=form['batManufacturer_input'],
                                model=form['batModel_input'],
                                sn=form['batSerialNumber_input'],
                                fab_date=datetime.strptime(form['batFabricationDate_input'], '%Y/%m/%d'),
                                tech=form['batTechnology_input'],
                                cells_num=int(form['batCellsNumber_input']),
                                cell_volt_min=int(float(form['batMinCellVoltage_input'])*1000),
                                cell_volt_max=int(float(form['batMaxCellVoltage_input'])*1000),
                                volt_min=int(float(form['batMinVoltage_input'])*1000),
                                volt_max=int(float(form['batMaxVoltage_input'])*1000),
                                curr_min=int(float(form['batMinCurrent_input'])*1000),
                                curr_max=int(float(form['batMaxCurrent_input'])*1000),
                            )
        newBattery.save()

        if newBattery.tech == 'Lithium':
            newLithium = Lithium(   bat_id = newBattery,
                                    capacity = int(float(form['batCapacityLithium_input'])*1000),
                                    chemistry = form['batChemistryLithium_input'],
                                )
            newLithium.save()

        elif newBattery.tech == 'LeadAcid':
            newLeadAcid = Leadacid( bat_id = newBattery,
                                    capacity = int(float(form['batCapacityLeadAcid_input'])*1000),
                                    chemistry = form['batChemistryLeadAcid_input'],
                                  )
            newLeadAcid.save()

        elif newBattery.tech == 'RedoxStack':
            newRedoxStack = Redoxstack( bat_id = newBattery,
                                        electrode_size = int(float(form['redoxElectrodeSize_input'])*100),
                                        electrode_composition = form['redoxElectrodeComposition_input'],
                                        bipolar_type = BipolarType_e(form['redoxBipolarType_input']).value,
                                        membrane_type = MembraneType_e(form['redoxMembraneType_input']).value,
                                        electrolyte_type = ElectrolyteType_e(form['redoxElectrolyteType_input']).value
                                      )
            newRedoxStack.save()

    return redirect('/add_experiment')


def validateProfile(request):
    file = ques.Crotolamo_c(request.POST['text'])
    is_valid = True
    error_msg = ''
    try:
        instructions = ques.permatrago(file.list)

        tmp_analyzer = analyzer(stringToInstructions(request.POST['text']))
        battery_id = request.POST['battery_selected']
        cycler_station_id = request.POST['cycler_station_selected']
        if battery_id == '' or cycler_station_id == '':
            raise Exception('No battery or cycler station selected')
        battery = Battery.objects.get(bat_id=battery_id)
        used_devices = Useddevices.objects.filter(cs_id=cycler_station_id)
        volt_max, volt_min, curr_max, curr_min = battery.volt_max, battery.volt_min, battery.curr_max, battery.curr_min
        for device in used_devices:
            if device.dev_id.comp_dev_id.volt_min is not None and device.dev_id.comp_dev_id.volt_max is not None\
               and device.dev_id.comp_dev_id.curr_min is not None and device.dev_id.comp_dev_id.curr_max is not None:
                if device.dev_id.comp_dev_id.volt_min > volt_min:
                    volt_min = device.dev_id.comp_dev_id.volt_min
                if device.dev_id.comp_dev_id.volt_max < volt_max:
                    volt_max = device.dev_id.comp_dev_id.volt_max
                if device.dev_id.comp_dev_id.curr_min > curr_min:
                    curr_min = device.dev_id.comp_dev_id.curr_min
                if device.dev_id.comp_dev_id.curr_max < curr_max:
                    curr_max = device.dev_id.comp_dev_id.curr_max
        if tmp_analyzer.curr_max > curr_max or tmp_analyzer.curr_min < curr_min:
            error_msg = 'Current out of range'
            is_valid = False
        if tmp_analyzer.volt_max is not None and (tmp_analyzer.volt_max > volt_max or tmp_analyzer.volt_min < volt_min):
            error_msg = 'Voltage out of range'
            is_valid = False

    except Exception as err:
        print(err)
        error_msg = str(err)
        is_valid =False
        #raise err
    return HttpResponse(json.dumps({'is_valid': is_valid, 'error_msg': error_msg}))


def validateField(request):
    post_dict = dict(request.POST)
    table = post_dict['table'][0]
    column = post_dict['column'][0]
    value = post_dict['value'][0]
    django_orm_table = globals()[table]
    filter_dict = {str(column)+'__exact' : value}
    exists = True
    try:
        django_orm_table.objects.get(**filter_dict)
    except ObjectDoesNotExist:
        exists = False
    # print(exists)
    return HttpResponse(json.dumps({'exists': exists}))


def experiments(request):
    technology_list = [tech[0] for tech in Technology_e.choices]

    battery_list = []
    for battery in Battery.objects.all():
        battery_list.append(battery)

    cycle_station_list = []
    for station in Cyclerstation.objects.all():
        cycle_station_list.append(station)
    # equipmentsName = Equipment.objects.all().values_list('name', flat=True)

    profile_list = []
    for profile in Profile.objects.all():
        profile_list.append(profile)

    experiments_list = []
    for experiment in Experiment.objects.all().select_related('cs_id', 'bat_id', 'prof_id'):
        experiments_list.append([experiment, experiment.cs_id.name, experiment.bat_id, experiment.prof_id.name])

    context = {
        'battery_list': battery_list,
        'technology_list': technology_list,
        'cycle_station_list': cycle_station_list,
        'profile_list': profile_list,
        'experiments_list': experiments_list,
    }
    return render(request, 'experiments.html', context)


def applyExperimentsFilters(request):
    post_dict = dict(request.POST)
    input_select = post_dict['input_select']
    # print(f"Full REQUEST -> {request.POST}\n")
    filters = {
        'technology': json.loads(post_dict['filters_technology'][0]),
        'battery': json.loads(post_dict['filters_battery'][0]),
        'cycle_station': json.loads(post_dict['filters_cycle_station'][0]),
        'profile': json.loads(post_dict['filters_profile'][0]),
    }

    batteries = []
    if len(filters['battery']) > 0:
        if len(filters['technology']) > 0:
            batteries = Battery.objects.filter(tech__in=filters['technology']).filter(bat_id__in=filters['battery'])
        else:
            batteries = Battery.objects.filter(bat_id__in=filters['battery'])
    else:
        if len(filters['technology']) > 0:
            batteries = Battery.objects.filter(tech__in=filters['technology'])
        else:
            batteries = Battery.objects.all()

    cycle_stations = []
    if len(filters['cycle_station']) > 0:
        cycle_stations = Cyclerstation.objects.filter(cs_id__in=filters['cycle_station'])
    else:
        cycle_stations = Cyclerstation.objects.all()

    profiles = []
    if len(filters['profile']) > 0:
        profiles = Profile.objects.filter(prof_id__in=filters['profile'])
    else:
        profiles = Profile.objects.all()

    experiments_list = []
    bats = set()
    stations = set()
    prof = set()
    for experiment in Experiment.objects.filter(bat_id__in=[_battery.bat_id for _battery in batteries]).filter(cs_id__in=[_cs.cs_id for _cs in cycle_stations]).filter(prof_id__in=[_profile.prof_id for _profile in profiles]).select_related('cs_id', 'bat_id', 'prof_id'):
        # experiments_list.append([experiment, experiment.cs_id.name, experiment.bat_id, experiment.prof_id.name])
        experiments_list.append(experiment)
        bats.add(experiment.bat_id.bat_id)
        stations.add(experiment.cs_id.cs_id)
        prof.add(experiment.prof_id.prof_id)

    response = {
        'technology_list': [{'id' : tech[0], 'name' : tech[1]} for tech in Technology_e.choices if tech[0] in filters['technology']],
        'battery_list': [{'id' : battery.bat_id, 'name' : battery.name, 'tech' : battery.tech} for battery in batteries],
        'cycle_station_list': [{'id' : cycle_station.cs_id, 'name' : cycle_station.name} for cycle_station in cycle_stations],
        'profile_list': [{'id' : profile.prof_id, 'name' : profile.name} for profile in profiles],
        'experiment_list': [{'id' : experiment.exp_id, 'sn' : experiment.bat_id.sn, 'name' : experiment.name, 'description' : experiment.description, 'date_begin' : experiment.date_begin.strftime("%Y/%m/%d, %H:%M:%S") if experiment.date_begin is not None else None, 'date_finish' : experiment.date_finish.strftime("%Y/%m/%d, %H:%M:%S") if experiment.date_finish is not None else None, 'status' : experiment.status} for experiment in experiments_list],
        'bats': list(bats),
        'stations': list(stations),
        'profs': list(prof),
    }

    return HttpResponse(json.dumps(response))


def getNewMeasures(request):
    post_dict = dict(request.POST)
    # print(post_dict['last_meas_id'])
    last_meas_id = post_dict['last_meas_id'][0]
    # print(last_meas_id)
    meas_numeric_list = json.loads(post_dict['meas_numeric_list'][0])
    # print(meas_numeric_list)
    new_generic_measures = Genericmeasures.objects.filter(exp_id=post_dict['experiment_id'][0]).filter(meas_id__gt=last_meas_id).order_by('meas_id')
    new_extended_measures = Extendedmeasures.objects.filter(exp_id=post_dict['experiment_id'][0]).filter(meas_id__gt=last_meas_id).order_by('meas_id')

    new_meas = {}
    new_meas_ids = list(new_generic_measures.values_list('meas_id', flat=True))
    new_meas['Voltage'] = []
    new_meas['Current'] = []
    for meas_id in new_generic_measures:
        new_meas['Voltage'].append(meas_id.voltage/1000.0)
        new_meas['Current'].append(meas_id.current/1000.0)
    for ext_meas_numeric in meas_numeric_list:
        if ext_meas_numeric != -1:
            temp_ext_meas = new_extended_measures.filter(used_meas_id=ext_meas_numeric).values_list('value', flat=True)
            new_meas[ext_meas_numeric] = [meas/1000.0 for meas in list(temp_ext_meas)]
    if new_generic_measures.first() is not None:
        actual_instr_id = list(new_generic_measures.values_list('instr_id', flat=True))[-1]
    else:
        actual_instr_id = None
    response = {
        'newMeas': new_meas,
        'newMeasIds': new_meas_ids,
        'actualInstruction': actual_instr_id,
    }
    return HttpResponse(json.dumps(response))


def translateMeasuresNames(request):
    post_dict = dict(request.POST)

    meas_names_list = json.loads(post_dict['measures_names'][0])
    exp_id = post_dict['exp_id']
    selected_experiment = Experiment.objects.get(exp_id=exp_id)
    used_measures = Usedmeasures.objects.filter(cs_id=selected_experiment.cs_id)
    used_measures_names = []
    for used_measure in used_measures:
        used_measures_names.append(used_measure.custom_name)
    # print(meas_names_list)
    meas_numeric_list = []
    for name in meas_names_list:
        if name in ['Voltage', 'voltage', 'Current', 'current']:
            meas_numeric_list.append(-1)
        else:
            meas_numeric_list.append(Measuresdeclaration.objects.get(meas_name=name).meas_type)

    response = {
        'meas_numeric_list': meas_numeric_list
    }
    return HttpResponse(json.dumps(response))


def add_experiment(request):
    batteries = Battery.objects.all()
    cycler_stations = Cyclerstation.objects.filter(deprecated=False)
    redox_stack = {}
    redox_stack['bipolar_type'] = BipolarType_e.values
    redox_stack['membrane_type'] = MembraneType_e.values
    redox_stack['electrolyte_type'] = ElectrolyteType_e.values
    redox_stack['polarity'] = Polarity_e.values
    context = {
        'batteries': batteries,
        'cycler_stations': cycler_stations,
        'redox_stack': redox_stack,
    }
    return render(request, 'add_experiment.html', context)


def import_experiment(request):
    batteries = Battery.objects.all()
    redox_stack = {}
    redox_stack['bipolar_type'] = BipolarType_e.values
    redox_stack['membrane_type'] = MembraneType_e.values
    redox_stack['electrolyte_type'] = ElectrolyteType_e.values
    measures_declaration = Measuresdeclaration.objects.all()
    context = {
        'batteries': batteries,
        'redox_stack': redox_stack,
        'measures_declaration': measures_declaration,
    }
    return render(request, 'import_experiment.html', context)


def add_battery(request):
    technologies = Technology_e.values
    chemistries = {}
    chemistries['lithium'] = Chemistry_Lithium_e.values
    chemistries['leadacid'] = Chemistry_LeadAcid_e.values
    redox_stack = {}
    redox_stack['bipolar_type'] = BipolarType_e.values
    redox_stack['membrane_type'] = MembraneType_e.values
    redox_stack['electrolyte_type'] = ElectrolyteType_e.values
    manufacturers = Battery.objects.all().order_by('-bat_id').values_list('manufacturer', flat=True)
    manufacturers = set(manufacturers)
    models = Battery.objects.all().order_by('-bat_id').values_list('model', flat=True)
    models = set(models)
    electrodeCompositions = Redoxstack.objects.all().order_by('-bat_id').values_list('electrode_composition', flat=True)
    electrodeCompositions = set(electrodeCompositions)

    context = {
        'technologies': technologies,
        'redox_stack': redox_stack,
        'chemistries': chemistries,
        'manufacturers': manufacturers,
        'models': models,
        'electrodeCompositions': electrodeCompositions
    }
    return render(request, 'add_battery.html', context)


def getProfiles(request):
    post_dict = dict(request.POST)
    battery_id = post_dict['battery'][0]
    cycler_station_id = post_dict['cycler_station'][0]
    battery = Battery.objects.get(bat_id=battery_id)
    used_devices = Useddevices.objects.filter(cs_id=cycler_station_id)
    volt_max, volt_min, curr_max, curr_min = battery.volt_max, battery.volt_min, battery.curr_max, battery.curr_min

    for device in used_devices:
        if device.dev_id.comp_dev_id.volt_min is not None and device.dev_id.comp_dev_id.volt_max is not None\
               and device.dev_id.comp_dev_id.curr_min is not None and device.dev_id.comp_dev_id.curr_max is not None:
            if device.dev_id.comp_dev_id.volt_min > volt_min:
                volt_min = device.dev_id.comp_dev_id.volt_min
            if device.dev_id.comp_dev_id.volt_max < volt_max:
                volt_max = device.dev_id.comp_dev_id.volt_max
            if device.dev_id.comp_dev_id.curr_min > curr_min:
                curr_min = device.dev_id.comp_dev_id.curr_min
            if device.dev_id.comp_dev_id.curr_max < curr_max:
                curr_max = device.dev_id.comp_dev_id.curr_max
    # print(f"\nvolt_max: {volt_max}\nvolt_min: {volt_min}\ncurr_max: {curr_max}\ncurr_min: {curr_min}\n")
    profiles = Profile.objects.filter(volt_max__lte=volt_max).filter(volt_min__gte=volt_min).filter(curr_max__lte=curr_max).filter(curr_min__gte=curr_min)
    profiles_extra = Profile.objects.filter(volt_max=None).filter(volt_min=None).filter(curr_max__lte=curr_max).filter(curr_min__gte=curr_min)
    # profiles_ids = profiles.values_list('prof_id', flat=True) + profiles_extra.values_list('prof_id', flat=True)
    profiles_ids = list(profiles.values_list('prof_id', flat=True)) + list(profiles_extra.values_list('prof_id', flat=True))
    profiles = profiles | profiles_extra
    for profile in profiles:
        profile.__setattr__('instr', list(Instructions.objects.filter(prof_id=profile.prof_id).order_by('instr_id')))
        for instr in profile.instr:
            instr.set_point = instr.set_point/1000.0
            instr.limit_point = instr.limit_point/1000.0
    context = {
        'profiles': profiles,
    }
    return render(request, 'profile_elements.html', context)


def getReport(request, exp_id_selected):
    response = loadReportTemplate(request, exp_id_selected, override_base='empty.html', graph_font_family='TeX Gyre Pagella')
    response['Content-Type'] = 'text/html'
    response['Content-Disposition'] = 'attachment; filename="'+ 'report_id_' + str(Experiment.objects.get(exp_id=exp_id_selected).exp_id).replace(" ", "_") +'_'+ str(Experiment.objects.get(exp_id=exp_id_selected).
        name).replace(" ", "_") + '_battery_'+ str(Battery.objects.get(bat_id=Experiment.objects.get(exp_id=exp_id_selected).bat_id.bat_id).name).replace(" ", "_")+'.html"'

    return response


def loadReportTemplate(request, exp_id_selected, override_base = None, graph_font_family : str = None):
    experiment_selected = Experiment.objects.get(exp_id=exp_id_selected)
    if experiment_selected.date_finish != None:
        experiment_duration = experiment_selected.date_finish - experiment_selected.date_begin
    elif experiment_selected.date_begin != None:
        experiment_duration = datetime.now(timezone.utc) - experiment_selected.date_begin
    else:
        experiment_duration = None
    # used_equipments = Useddevices.objects.filter(cs_id=experiment_selected.cs_id)
    used_devices = Useddevices.objects.filter(cs_id=experiment_selected.cs_id)
    detected_used_devices = [device.dev_id for device in used_devices]
    for device in detected_used_devices:
        device.device_type = device.comp_dev_id.device_type
        device.name = device.comp_dev_id.name
    # comp_devices = Compatibledevices.objects.filter(comp_dev_id__in=used_equipments.values('comp_dev_id'))
    recorded_measures = set(Extendedmeasures.objects.filter(exp_id=exp_id_selected).values_list('used_meas_id', flat=True))
    used_meas_ids = Usedmeasures.objects.filter(cs_id=experiment_selected.cs_id).filter(used_meas_id__in=recorded_measures)
    measures_names = []
    for meas in used_meas_ids:
        if meas.custom_name == None:
            measures_names.append(meas.meas_type.meas_name)
        else:
            measures_names.append(meas.custom_name)
    triggered_alarms = Alarm.objects.filter(exp_id=exp_id_selected)
    profile_used = Profile.objects.get(prof_id=experiment_selected.prof_id.prof_id)
    instructions = Instructions.objects.filter(prof_id=profile_used).order_by('instr_id')
    experiment_selected.__setattr__('duration', experiment_duration)
    context = {
        'experiment': experiment_selected,
        'battery': experiment_selected.bat_id,
        'cycler_station': experiment_selected.cs_id,
        # 'used_equipments': used_equipments,
        # 'comp_devices': comp_devices,
        'detected_used_devices': detected_used_devices,
        'measures_names': measures_names,
        'override_base': override_base,
        'graph': graphPreview(exp_id_selected, graph_font_family=graph_font_family),
        'triggered_alarms': triggered_alarms,
        'profile': profile_used,
        'instructions': instructions,
    }
    return render(request, 'preview.html', context)


def getNewGraph(request):
    post_dict = dict(request.POST)
    meas_numeric_list = json.loads(post_dict['meas_numeric_list'][0])
    # print(meas_numeric_list)
    last_meas_id = Genericmeasures.objects.filter(exp_id=post_dict['experiment_id'][0]).order_by('-meas_id').first()
    # print(last_meas_id.meas_id)
    limit_time = int(post_dict['time_window'][0])
    new_generic_measures = Genericmeasures.objects.filter(exp_id=post_dict['experiment_id'][0]).filter(meas_id__gt=max(0, (last_meas_id.meas_id-limit_time))).order_by('meas_id')
    new_extended_measures = Extendedmeasures.objects.filter(exp_id=post_dict['experiment_id'][0]).filter(meas_id__gt=max(0, (last_meas_id.meas_id-limit_time))).order_by('meas_id')

    new_meas = {}
    new_meas_ids = list(new_generic_measures.values_list('meas_id', flat=True))
    # print(new_meas_ids)
    new_meas['Voltage'] = []
    new_meas['Current'] = []
    for meas_id in new_generic_measures:
        new_meas['Voltage'].append(meas_id.voltage/1000.0)
        new_meas['Current'].append(meas_id.current/1000.0)
    for ext_meas_numeric in meas_numeric_list:
        if ext_meas_numeric != -1:
            temp_ext_meas = new_extended_measures.filter(used_meas_id=ext_meas_numeric).values_list('value', flat=True)
            new_meas[ext_meas_numeric] = [meas/1000.0 for meas in list(temp_ext_meas)]

    response = {
        'newMeas': new_meas,
        'newMeasIds': new_meas_ids,
    }
    return HttpResponse(json.dumps(response))


def graphLive(exp_id_selected, time_window=300, only_data=False):
    last_meas_id = Genericmeasures.objects.filter(exp_id=exp_id_selected).order_by('-meas_id').first()
    if last_meas_id is None:
        # No measures recorded yet
        return None
    else:
        last_meas_id = last_meas_id.meas_id
        generic_measures = Genericmeasures.objects.filter(exp_id=exp_id_selected).order_by('meas_id').filter(meas_id__gte=max(0, last_meas_id-time_window))
        x_meas_id = []
        y_measures = {}
        y_measures['voltage'] = []
        y_measures['current'] = []
        for meas in generic_measures:
            x_meas_id.append(meas.meas_id)
            y_measures['voltage'].append(meas.voltage/1000.0)
            y_measures['current'].append(meas.current/1000.0)

        extended_measures = Extendedmeasures.objects.filter(exp_id=exp_id_selected).order_by('meas_id').filter(meas_id__gte=max(0, last_meas_id-time_window))
        different_extended_measures = extended_measures.values_list('used_meas_id', flat=True).distinct()
        different_extended_measures = set(different_extended_measures)
        extended_measures_names = {}
        for ext_meas in different_extended_measures:
            extended_measures_names[ext_meas] = Usedmeasures.objects.get(used_meas_id=ext_meas).custom_name if Usedmeasures.objects.get(used_meas_id=ext_meas).custom_name != None else Usedmeasures.objects.get(used_meas_id=ext_meas).meas_type.meas_name
            y_measures[extended_measures_names[ext_meas]] = [value/1000.0 for value in extended_measures.filter(used_meas_id=ext_meas).values_list('value', flat=True)]
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(go.Scatter(
            mode = 'lines+markers',
            x = x_meas_id,
            y = y_measures['voltage'],
            name = str('voltage').capitalize(),
            marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
            ),
            secondary_y = False
        )

        fig.add_trace(go.Scatter(
            mode = 'lines+markers',
            x = x_meas_id,
            y = y_measures['current'],
            name = str('current').capitalize(),
            marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
            ),
            secondary_y = True
        )

        for ext_meas in extended_measures_names:
            fig.add_trace(go.Scatter(
                mode = 'lines+markers',
                x = x_meas_id,
                y = y_measures[extended_measures_names[ext_meas]],
                name = str(extended_measures_names[ext_meas]),#.capitalize(),
                marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
                text = f"ID: {ext_meas}"
                ),
                secondary_y = True
            )

        fig.update_xaxes(
            tickangle=-45,
            title_text='Duration (s)',
            ticksuffix='s',
        )

        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(
                    visible=True
                ),
                type="-"
            )
        )

        fig.update_yaxes(
            secondary_y = True,
            autorange = True
        )
        fig.layout.yaxis.ticksuffix=' V '
        fig.layout.yaxis.title='Voltage'
        # fig.layout.yaxis2.ticksuffix=' A'
        fig.layout.yaxis2.title='Others'

        if len(x_meas_id) > 0:
            range_x=[x_meas_id[0]-1, x_meas_id[-1]+1]
        else:
            range_x=[0, 1]

        fig.update_layout(
            height=700,
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            xaxis=dict(gridcolor='lightgrey', title='Duration', mirror=True,
                    zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey',
                    range=range_x),
            yaxis=dict(gridcolor='lightgrey',mirror=True, anchor='free',
                    #zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey'
                    ),
            yaxis2=dict(anchor='free', overlaying='y', side='right', position=0.95,),
            # yaxis2=dict(gridcolor='lightgrey', title='Current', mirror=True, anchor='free',
            #            zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey'),
            title=dict(text='', x=0.5),
            margin=dict(l=50, r=50, b=50, t=50, pad=4),
            font=dict(size=16),
            #font=dict(family='TeX Gyre Pagella',  size=16),
            showlegend=True,
            legend=dict(
                orientation="h",
            ),
            shapes=[go.layout.Shape(
                type='rect',
                xref='paper',
                yref='paper',
                x0=0,
                y0=0,
                x1=0.94,
                y1=1,
                line={'width': 1, 'color': 'grey'}
                                )
                    ],
        )

        config={
                'toImageButtonOptions': {
                    'format': 'svg', 'filename': f"{fig.layout.title['text'].replace(' ','_')}", 'displaylogo': False
                    },
                'responsive': True
                }

        return pio.to_html(fig, include_plotlyjs=True, full_html=False, div_id='graphLive', config=config)


def graphPreview(exp_id_selected, extended_measures_to_graph : bool = True, save_img : bool = False, graph_font_family : str = None):
    time_start = time()

    MAX_NUMBER_OF_POINTS = 1000
    x_meas_id = []
    y_measures = {}

    y_measures['voltage'] = []
    y_measures['current'] = []
    query_generic_measures = \
    f'''
        SELECT block, MIN(MeasID) AS first_block_row, AVG(Voltage/1000) AS avg_voltage, AVG(Current/1000) AS avg_current
        FROM (SELECT GenericMeasures.MeasID AS MeasID, NTILE({MAX_NUMBER_OF_POINTS}) OVER (ORDER BY MeasID) AS Block, GenericMeasures.Voltage, GenericMeasures.Current AS Current FROM GenericMeasures WHERE ExpID={exp_id_selected}) AS Chunks
        GROUP BY Block
    '''

    with connection.cursor() as cursor:
        cursor.execute(query_generic_measures)

        columns = [col[0] for col in cursor.description]

        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for result in results:
        y_measures['voltage'].append(result['avg_voltage'])
        y_measures['current'].append(result['avg_current'])
        x_meas_id.append(result['first_block_row'])

    if extended_measures_to_graph:
        extended_measures = Extendedmeasures.objects.filter(exp_id=exp_id_selected).order_by('meas_id')
        different_extended_measures = extended_measures.values_list('used_meas_id', flat=True).distinct()
        different_extended_measures = set(different_extended_measures)

        extended_measures_names = {}
        for diff_ext_meas in different_extended_measures:
            extended_measure_name = Usedmeasures.objects.get(used_meas_id=diff_ext_meas).custom_name if Usedmeasures.objects.get(used_meas_id=diff_ext_meas).custom_name != None else Usedmeasures.objects.get(used_meas_id=diff_ext_meas).meas_type.meas_name
            extended_measures_names[diff_ext_meas] = extended_measure_name
            query_extended_measures = \
            f'''
                SELECT block, MIN(MeasID) AS first_block_row, AVG(Value/1000) AS avg_meas
                FROM (SELECT ExtendedMeasures.MeasID AS MeasID, NTILE({MAX_NUMBER_OF_POINTS}) OVER (ORDER BY MeasID) AS Block, ExtendedMeasures.Value AS Value FROM ExtendedMeasures WHERE ExpID={exp_id_selected} AND UsedMeasID={diff_ext_meas}) AS Chunks
                GROUP BY Block
            '''
            results = None
            with connection.cursor() as cursor:
                cursor.execute(query_extended_measures)

                columns = [col[0] for col in cursor.description]

                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            y_measures[extended_measure_name] = [result_row['avg_meas'] for result_row in results]

    print(f"Time elapsed retrieving data: {time() - time_start}")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        mode = 'lines+markers',
        x = x_meas_id,
        y = y_measures['voltage'],
        name = str('voltage').capitalize(),
        marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
        ),
        secondary_y = False
    )

    fig.add_trace(go.Scatter(
        mode = 'lines+markers',
        x = x_meas_id,
        y = y_measures['current'],
        name = str('current').capitalize(),
        marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
        ),
        secondary_y = True
    )
    if extended_measures_to_graph:
        for ext_meas in extended_measures_names:
            fig.add_trace(go.Scatter(
                mode = 'lines+markers',
                x = x_meas_id,
                y = y_measures[extended_measures_names[ext_meas]],
                name = str(extended_measures_names[ext_meas]),#.capitalize(),
                marker=dict(size=5, symbol='pentagon'),  # Personalizar los marcadores
                ),
                secondary_y = True
            )

    fig.update_xaxes(
        tickangle=-45,
        title_text='Duration (s)',
        ticksuffix='s',
    )



    fig.update_yaxes(
        secondary_y = True,
        autorange = True
    )
    # fig.update_layout(uirevision='constant', #Esto es para que la grafica no reinicie la vista que se ha seleccionado (zoom, paneo, cambios de escala, etc) (https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks)
    #                     transition_duration=200,)
    # fig.layout.autosize = True
    fig.layout.yaxis.ticksuffix=' V '
    fig.layout.yaxis.title='Voltage'
    # fig.layout.yaxis2.ticksuffix=' A'
    fig.layout.yaxis2.title='Others'

    if len(x_meas_id) > 0:
        range_x=[x_meas_id[0]-1, x_meas_id[-1]+1]
    else:
        range_x=[0, 1]

    fig.update_layout(
        height=700,
        plot_bgcolor='white',
        xaxis=dict(gridcolor='lightgrey', title='Duration', mirror=True,
                   zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey',
                   range=range_x),
        yaxis=dict(gridcolor='lightgrey',mirror=True, anchor='free',
                   #zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey'
                   ),
        yaxis2=dict(anchor='free', overlaying='y', side='right', position=0.95,),
        # yaxis2=dict(gridcolor='lightgrey', title='Current', mirror=True, anchor='free',
        #            zeroline=True, zerolinewidth=1, zerolinecolor='lightgrey'),
        title=dict(text='', x=0.5),
        margin=dict(l=50, r=50, b=50, t=50, pad=4),
        font=dict(size=16),
        showlegend=True,
        legend=dict(
            orientation="h",
        ),
        shapes=[go.layout.Shape(
            type='rect',
            xref='paper',
            yref='paper',
            x0=0,
            y0=0,
            x1=0.94,
            y1=1,
            line={'width': 1, 'color': 'grey'}
                            )
                ],
    )

    if graph_font_family is not None:
        fig.update_layout(font=dict(family=graph_font_family))

    config={
            'toImageButtonOptions': {
                'format': 'svg', 'filename': f"{fig.layout.title['text'].replace(' ','_')}", 'displaylogo': False
                },
            'responsive': True
            }

    if save_img:
        if not os.path.exists(f"./static/images/graph_preview/exp_{exp_id_selected}.webp"):
            fig_to_save = fig
            fig_to_save.update_layout(height=400, width=600, legend=dict(orientation="h", yanchor='top', xanchor='left', y=1.2, x=-0.05))
            fig_to_save.write_image(f"./static/images/graph_preview/exp_{exp_id_selected}.webp")
        else:
            print(f"Image exp_{exp_id_selected}.webp already exists...")
        pass

    # The following is added after save image to avoid innecessary info in saved preview graph
    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            type="-"
        )
    )

    return pio.to_html(fig, include_plotlyjs=True, full_html=False, div_id='graphPreview', config=config)
    # return {'x' : x_meas_id, 'y' : y_measures}


def getCsv(request, exp_id_selected):
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + str(Experiment.objects.get(exp_id=exp_id_selected).name).capitalize().replace(" ", "_") + '(Measures).csv"'
    writer = csv.writer(response)

    generic_measures = Genericmeasures.objects.filter(exp_id=exp_id_selected).order_by('meas_id')
    differnt_extended_measures = Extendedmeasures.objects.filter(exp_id=exp_id_selected).values_list('used_meas_id', flat=True).distinct()
    diff_ext_meas_list = []
    for diff_meas in differnt_extended_measures:
        diff_ext_meas_list.append(diff_meas)
    diff_ext_meas_names = []
    for diff_meas in diff_ext_meas_list:
        diff_ext_meas_names.append(Usedmeasures.objects.get(used_meas_id=diff_meas).custom_name if Usedmeasures.objects.get(used_meas_id=diff_meas).custom_name != None else Usedmeasures.objects.get(used_meas_id=diff_meas).meas_type.meas_name)


    headerRow = ['Timestamp', 'MeasID', 'Voltage', 'Current'] + diff_ext_meas_names #+ availableMagNamesOrdered
    writer.writerow(headerRow)

    if generic_measures.last() is not None:
        # last_meas_id = generic_measures.last().meas_id
        diff_ext_meas_values = {}
        raw_diff_ext_meas_values = {}
        for diff_meas in diff_ext_meas_list:
            raw_diff_ext_meas_values[diff_meas] = Extendedmeasures.objects.filter(exp_id=exp_id_selected).filter(used_meas_id=diff_meas).order_by('meas_id').values('meas_id', 'value')
            diff_ext_meas_values[diff_meas] = {raw_row['meas_id'] : raw_row['value'] for raw_row in raw_diff_ext_meas_values[diff_meas]}

        for generic_measure in generic_measures:
            current_meas_id = generic_measure.meas_id
            row = [generic_measure.timestamp, generic_measure.meas_id, generic_measure.voltage, generic_measure.current]
            for diff_meas in diff_ext_meas_list:
                if current_meas_id in diff_ext_meas_values[diff_meas]:
                    row.append(diff_ext_meas_values[diff_meas][current_meas_id])
                else:
                    row.append(None)
                    print(f"No se encontró la meas_id({current_meas_id}) en {diff_ext_meas_names[diff_ext_meas_list.index(diff_meas)]}")
            # print(row)
            writer.writerow(row)

    return response


def generatePreviews(request):
    if request.method == 'POST':
        file_path = "./static/images/graph_preview/last_generation_datetime.txt"
        if not os.path.exists('./static/images/graph_preview'):
            os.mkdir('./static/images/graph_preview')
            f = open(file_path, "x")
            f.write(str(datetime.strptime('1780/01/01 00:00:00', '%Y/%m/%d %H:%M:%S')))
            f.close()
        f = open(file_path, "r")
        last_date = datetime.strptime(f.readline(), '%Y-%m-%d %H:%M:%S')
        f.close()

        exp_to_generate = Experiment.objects.filter(status__in=('FINISHED', 'ERROR')).filter(date_finish__gte=last_date)
        for exp in exp_to_generate:
            graphPreview(exp_id_selected=exp.exp_id, extended_measures_to_graph=False, save_img=True)

        f = open(file_path, "w")
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        f.close()

    else:
        print('Forbidden access!')

    return HttpResponse('<h1>403 - Forbidden</h1>')


def cycler_station(request):
    cycler_stations = Cyclerstation.objects.all()
    # active_cu = Computationalunit.objects.filter(available=Available_e.ON).filter(last_connection__gte=datetime.now(timezone.utc)-timedelta(minutes=10))
    active_cu = Computationalunit.objects.filter(available=Available_e.ON.value)
    filtered_cu = []
    # Set as not available the CUs that have not been connected for more than 1 minute
    # for cu in active_cu:
    #     if cu.last_connection > datetime.now(timezone.utc)-timedelta(minutes=100000): # TODO: Change to 1 minute
    #         filtered_cu.append(cu)
    #     else:
    #         cu.available = Available_e.OFF
    #         cu.save()

    context = {
        'cycler_stations': cycler_stations,
        'active_cu': active_cu,
    }
    return render(request, 'cycler_station.html', context)


def getCsOfCu(request):
    post_dict = dict(request.POST)
    cu_id = post_dict['cu_id'][0]
    cs = Cyclerstation.objects.filter(cu_id=cu_id).filter(deprecated=False)
    cs = cs.values('cs_id', 'name', 'location')
    response = list(cs)
    return HttpResponse(json.dumps(response))


def getDetectedDevicesOfCu(request):
    initial_time = time()
    post_dict = dict(request.POST)
    cu_id = post_dict['cu_id'][0]
    response = {}
    http_response : HttpResponse = requestRefreshDevices(request)
    http_response_dict = json.loads(http_response.content)
    if http_response_dict['status'] == 'OK':
        active_cs_ids = Cyclerstation.objects.filter(cu_id=cu_id).filter(deprecated=False)
        active_used_devices = Useddevices.objects.filter(cs_id__in=active_cs_ids)
        detected_devices = Detecteddevices.objects.filter(cu_id=cu_id).filter(conn_status=ConnStatus_e.CONNECTED.value)
        free_devices = detected_devices.exclude(dev_id__in=active_used_devices)

        # print(f"Detected_devices: {detected_devices}")
        # print(f"Used_devices: {active_used_devices}")
        # print(f"Free_devices: {free_devices}")

        for device in free_devices:
            response[device.dev_id] = {'free': True, 'selected': False, 'sn': device.sn, 'name': device.comp_dev_id.name, 'device_type': device.comp_dev_id.device_type, 'available_measures': list(Availablemeasures.objects.filter(comp_dev_id=device.comp_dev_id).values('meas_type', 'meas_name'))}
        for device in active_used_devices:
            response[device.dev_id.dev_id] = {'free': False, 'selected': False, 'sn': device.dev_id.sn, 'name': device.dev_id.comp_dev_id.name, 'device_type': device.dev_id.comp_dev_id.device_type, 'available_measures': list(Availablemeasures.objects.filter(comp_dev_id=device.dev_id.comp_dev_id).values('meas_type', 'meas_name'))}

        if 'cs_id' in post_dict and post_dict['cs_id'][0] != "":
            cs_id = post_dict['cs_id'][0]
            cs_used_devices = Useddevices.objects.filter(cs_id=cs_id)
            for device in cs_used_devices:
                response[device.dev_id.dev_id]['free'] = True
                response[device.dev_id.dev_id]['selected'] = True
                for meas in response[device.dev_id.dev_id]['available_measures']:
                    used_meas = Usedmeasures.objects.filter(cs_id=cs_id).filter(dev_id=device.dev_id.dev_id).filter(meas_type=meas['meas_type'])
                    if len(used_meas) > 0:
                        meas['selected'] = True
                        meas['custom_name'] = used_meas[0].custom_name
                    else:
                        meas['selected'] = False
                        meas['custom_name'] = None


                # tmp_selected_measures = Usedmeasures.objects.filter(cs_id=cs_id).filter(dev_id=device.dev_id.dev_id)

                # response[device.dev_id.dev_id]['selected_measures'] = []
                # for meas in tmp_selected_measures:
                #     response[device.dev_id.dev_id]['selected_measures'].append({'meas_type': meas.meas_type.meas_type, 'used_meas_id': meas.used_meas_id, 'meas_name': meas.meas_type.meas_name, 'custom_name': meas.custom_name})
    else:
        print(http_response_dict['message'])
    elapsed_time = time() - initial_time
    print(f"Elapsed time: {elapsed_time}")
    return HttpResponse(json.dumps(response))


def _launch_cs(cu_id, cs_id) -> None:
    print(f'Launching CS ({cs_id}) on CU ({cu_id})...')
    cmd_to_mn_manager = CommDataMnCmdDataC(CommDataMnCmdTypeE.LAUNCH, cu_id, cs_id = cs_id)
    _MN_REQ_CHAN.send_data(cmd_to_mn_manager)


def requestRefreshDevices(request) -> HttpResponse:
    TIMEOUT = 20
    post_dict = dict(request.POST)
    response = HttpResponse(json.dumps({'status': 'OK'}))
    if 'cu_id' in post_dict:
        cu_id = int(post_dict['cu_id'][0])
        print(f'Requesting refresh devices of CU: ...')
        cmd_to_mn_manager = CommDataMnCmdDataC(CommDataMnCmdTypeE.REQ_DETECT, cu_id)
        _MN_REQ_CHAN.send_data(cmd_to_mn_manager)
        try:
            refresh_confirm : CommDataMnCmdDataC = _MN_DATA_CHAN.receive_data(timeout=TIMEOUT)
        except Exception as err:
            print(f'Error receiving refresh confirm: {err}')
            response = HttpResponse(json.dumps({'status': 'ERROR', 'message': 'Error receiving refresh confirm (timeout)'}))
        else:
            # TODO: Check if the response is the expected for exactly this request
            if refresh_confirm.cmd_type == CommDataMnCmdTypeE.INF_DEV:
                print(f'Refresh confirm received!')
            else:
                print(f'Unexpected response: {refresh_confirm}')
                response = HttpResponse(json.dumps({'status': 'ERROR', 'message': 'Unexpected response'}))

    else:
        response = HttpResponse(json.dumps({'status': 'ERROR', 'message': 'No cu_id provided'}))

    return response


def addNewCs(request):
    post_dict = dict(request.POST)
    print(json.loads(post_dict['selected_devices'][0]))
    cu_id = post_dict['cu_id'][0]
    selected_devices = json.loads(post_dict['selected_devices'][0])
    new_cs = Cyclerstation.objects.create(cu_id=Computationalunit.objects.get(cu_id=cu_id),
                                          name=post_dict['cs_name'][0],
                                          location=post_dict['cs_location'][0],
                                          register_date=datetime.now(timezone.utc),
                                          deprecated=False)
    new_cs.save()
    new_used_devices = []
    for device in selected_devices:
        new_used_devices.append(Useddevices.objects.create(cs_id=new_cs,
                                                           dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']),))
    # new_used_devices = Useddevices.objects.bulk_create(new_used_devices)
    for dev in new_used_devices:
        try:
            dev.save()
        except Exception as e:
            print(e)

    new_used_meas = []
    for device in selected_devices:
        for meas in device['measures']:
            new_used_meas.append(Usedmeasures.objects.create(cs_id=new_cs,
                                                        dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']),
                                                        meas_type=Availablemeasures.objects.get(comp_dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']).comp_dev_id, meas_type=meas['meas_type']),
                                                        custom_name=meas['custom_name']))
    # new_used_meas = Usedmeasures.objects.bulk_create(new_used_meas)
    for meas in new_used_meas:
        try:
            meas.save()
        except Exception as e:
            print(e)

    _launch_cs(cu_id, new_cs.cs_id)

    return HttpResponse(json.dumps({'status': 'OK'}))


def modifyCs(request):
    post_dict = dict(request.POST)
    print(json.loads(post_dict['selected_devices'][0]))
    cu_id = post_dict['cu_id'][0]
    selected_devices = json.loads(post_dict['selected_devices'][0])
    cs_id_to_deprecate = post_dict['cs_id'][0]
    cs_to_deprecate = Cyclerstation.objects.get(cs_id=cs_id_to_deprecate)
    cs_to_deprecate.deprecated = True
    cs_to_deprecate.save()
    new_cs = Cyclerstation.objects.create(cu_id=Computationalunit.objects.get(cu_id=cu_id),
                                          name=cs_to_deprecate.name,
                                          location=cs_to_deprecate.location,
                                          register_date=datetime.now(timezone.utc),
                                          parent=cs_to_deprecate.cs_id,
                                          deprecated=False)
    new_cs.save()
    new_used_devices = []
    for device in selected_devices:
        new_used_devices.append(Useddevices.objects.create(cs_id=new_cs,
                                                                    dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']),))
    # new_used_devices = Useddevices.objects.bulk_create(new_used_devices)
    for dev in new_used_devices:
        try:
            dev.save()
        except Exception as e:
            print(e)

    new_used_meas = []
    for device in selected_devices:
        for meas in device['measures']:
            new_used_meas.append(Usedmeasures.objects.create(cs_id=new_cs,
                                                        dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']),
                                                        meas_type=Availablemeasures.objects.get(comp_dev_id=Detecteddevices.objects.get(dev_id=device['dev_id']).comp_dev_id, meas_type=meas['meas_type']),
                                                        custom_name=meas['custom_name']))
    # new_used_meas = Usedmeasures.objects.bulk_create(new_used_meas)
    for meas in new_used_meas:
        try:
            meas.save()
        except Exception as e:
            print(e)

    _launch_cs(cu_id, new_cs.cs_id)

    return HttpResponse(json.dumps({'status': 'OK'}))


def deleteCs(request):
    post_dict = dict(request.POST)
    cs_id = post_dict['cs_id'][0]
    cs = Cyclerstation.objects.get(cs_id=cs_id)
    cs.deprecated = True
    cs.save()
    return HttpResponse(json.dumps({'status': 'OK'}))