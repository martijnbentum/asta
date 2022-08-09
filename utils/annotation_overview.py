from texts.models import Annotation
from collections import Counter
from operator import attrgetter

def get_annotations_with_user(user):
    '''return query set of annotation based on user.'''
    annotations = Annotation.objects.none()
    try:annotations = Annotation.objects.filter(user = user)
    except ValueError:
        print(user,'not a user return empty annotation query set')
    return annotations

def make_annotation_dict(annotations, attribute_name):
    '''return a dictionary with names linking to a list of annotations.
    for example alignment (e.g. good bad) linking to corresponding annotations
    annotations     a query set or list of annotations
    attribute_name  the name of the attribute of the annotation or nested
                    attribute e.g. 'alignment' or 'recording.area'
    '''
    d = {}
    f = attrgetter(attribute_name)
    for name, annotation in [[f(x),x] for x in annotations]:
        if name not in d.keys(): d[name] = []
        d[name].append(annotation)
    return d

def user_annotion_alignment_dict(user):
    '''return a dictionary linking alignment to corresponding annotations.'''
    annotations = get_annotations_with_user(user)
    d = make_annotation_dict(annotations,'alignment')
    return d

def user_alignment_counts(user):
    '''return a dictionary linking alignment to count (i.e. number of
    annotation with this alignment.'''
    annotations = get_annotations_with_user(user)
    return dict(Counter([x.alignment for x in annotations]))
        
def user_annotion_province_dict(user):
    '''return a dictionary linking province to corresponding annotations.'''
    annotations = get_annotations_with_user(user)
    d = make_annotation_dict(annotations,'recording.province.name')
    return d
        
def user_province_counts(user):
    '''return a dictionary linking province to count (i.e. number of
    annotation with this province.'''
    annotations = get_annotations_with_user(user)
    return dict(Counter([x.recording.province.name for x in annotations]))
    
def user_annotion_area_dict(user):
    '''return a dictionary linking province to corresponding annotations.'''
    annotations = get_annotations_with_user(user)
    d = make_annotation_dict(annotations,'recording.area')
    return d
        
def user_area_counts(user):
    '''return a dictionary linking area to count (i.e. number of
    annotation with this area.'''
    annotations = get_annotations_with_user(user)
    return dict(Counter([x.recording.area for x in annotations]))
