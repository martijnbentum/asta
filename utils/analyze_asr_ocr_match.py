from utils import select
from texts.models import Recording, Annotation
import json
from matplotlib import pyplot as plt
import numpy as np
from utils.dialect import dialect_groups

area_dict = select.make_area_to_recording_dict()


areas = 'Acht,Ov-O,NLimb-Z,NLimb-M,NLimb-N,NBra-M,NBra-Z,NBra-W,NBra-O'
areas += ',ZHol-O,ZHol-W,ZHol-N'
areas = areas.split(',')


def align_to_duration(a,min_duration=1,min_match=0):
    mismatch = 100 - min_match
    ols = a.filter_ocr_lines(mismatch_threshold=mismatch)
    ols = [x for x in ols if x.duration != False and x.duration >=min_duration]
    duration = sum([x.duration for x in ols])
    return duration

def area_to_align_duration(area_name, min_duration = 1, min_match = 0):
    recordings = area_dict[area_name]
    align_durations = []
    for recording in recordings:
        align = recording.align
        align_durations.append(align_to_duration(align,
            min_duration = min_duration,min_match=min_match))
    return align_durations

def area_to_recording_duration(area_name):
    recordings = area_dict[area_name]
    recording_durations = []
    for recording in recordings:
        recording_durations.append(recording.duration)
    return recording_durations
        

def match_range_to_durations_for_area(area_name, matches=list(range(0,101,5)) ):
    rd = area_to_recording_duration(area_name)
    output = {'recording_durations':rd}
    output['recording_duration_total']= sum(rd)
    for match in matches:
        ad = area_to_align_duration(area_name, min_match=match)
        output['align_match_durations-' + str(match)] = ad
        output['align_match_durations_total-' + str(match)] = sum(ad)
    save_json(output, area_name_to_filename(area_name) )
    return output

def make_json_duration_files_for_areas(areas = areas):
    for area in areas:
        print('handling area:',area)
        match_range_to_durations_for_area(area)
    print('done')

def area_name_to_filename(area_name):
    return 'data/' + area_name + '-durations.json'

def _get_matches(durations_dict):
    matches = []
    for k in durations_dict.keys():
        if 'align_match_durations_total-' in k: 
            matches.append(int(k.split('-')[-1]))
    return matches

def make_area_duration_tuple(area_name):
    filename = area_name_to_filename(area_name)
    o = load_json(filename)
    x = _get_matches(o)
    y = []
    for value in x:
        y.append(o['align_match_durations_total-'+str(value)]/3600)
    return x, y

def _plot_match_duration(x,y,name = None, clear_canvas = True):
    if clear_canvas:
        plt.clf()
    if name != None:
        plt.title(name)
    plt.xlabel('% token match between ocr and asr')
    plt.ylabel('hours')
    plt.plot(x,y)
    if clear_canvas:
        plt.show()
    
def plot_area(area_name):
    x, y = make_area_duration_tuple(area_name)
    _plot_match_duration(x,y, area_name)

def plot_dialect(dialect_name, multiple = False):
    area_names = dialect_groups[dialect_name]
    data = []
    for area_name in area_names:
        x, y = make_area_duration_tuple(area_name)
        if type(data) == list: data = np.array(y)
        else: data+= np.array(y)
    if multiple: 
        dialect_name = None
        clear_canvas = False
    else: clear_canvas = True
    _plot_match_duration(x,data, dialect_name, clear_canvas)

def plot_dialects():
    names = []
    plt.clf()
    plt.title('hours of audio per % match per dialect')
    for dialect_name in dialect_groups.keys():
        names.append(dialect_name)
        plot_dialect(dialect_name, multiple = True)
    plt.legend(names)
    plt.show()

    

def save_json(data,filename):
    with open(filename,'w') as fout:
        json.dump(data,fout)

def load_json(filename):
    with open(filename) as fin:
        data = json.load(fin)
    return data

def analyse_annotation_match():
    a = Annotation.object.all()
