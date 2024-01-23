from texts.models import Recording
from . import select

def get_recordings():
    r = select.get_recordings_with_areas_list(['Acht'])
    return r

def add_good_bad(d,align):
    annotations = align.annotations
    indices = []
    for annotation in annotations:
        alignment = annotation.alignment
        index = annotation.ocrline_index
        if alignment in ['good','bad'] and index not in indices:
            indices.append(index)
            d[alignment].append(align.ocr_lines[index])

def make_good_bad_dict():
    recordings = get_recordings()
    d = {'good':[],'bad':[]}
    for recording in recordings:
        add_good_bad(d, recording.align)
    return d
