from jiwer import wer
import jiwer
from utils import make_dataset as md
from utils import select

provinces = 'Gelderland,Overijssel,Groningen,Drenthe,Zeeland,Noord-Holland'
provinces += ',Flevoland,Zuid-Holland,Limburg,Noord-Brabant,Utrecht,Friesland'
provinces = provinces.split(',')

def fremy_dutch_datasets_to_wer(datasets = None, split = 'dev'):
    if not datasets: datasets = md.make_datasets(save=False)
    gt, pred = [],[]
    output = {}
    for dialect_name in md.dialect_groups.keys():
        dataset = datasets[dialect_name]
        ocrlines= getattr(dataset,split)
        for ocrline in ocrlines:
            gt.append(ocrline.cleaner.text_clean)
            pred.append(ocrline.asr_text)
        word_error_rate = wer(gt,pred)
        output[dialect_name] = word_error_rate
    return output

def recordings_to_ols_list(recordings):
    ols = []
    for recording in recordings:
        if not hasattr(recording,'align'): continue
        if not hasattr(recording.align,'ocr_lines'):continue
        for ocrline in recording.align.ocr_lines:
            if ocrline.duration and ocrline.duration >= 1:
                ocrline.cleaner = md.Cleaner(ocrline.ocr_text)
                ols.append(ocrline)
    return ols
        
        
def fremy_dutch_province_to_wer(province_name):
    recordings = select.get_recordings_with_province_list([province_name])
    ocrlines = recordings_to_ols_list(recordings)
    gt, pred = [], []
    duration = 0
    print(province_name, len(ocrlines))
    for ocrline in ocrlines:
        gt_text =ocrline.cleaner.text_clean
        pred_text = ocrline.asr_text
        if not gt_text or not pred_text: continue
        gt.append(gt_text)
        pred.append(pred_text)
        duration += ocrline.duration
    word_error_rate = wer(gt,pred)
    return word_error_rate, duration, gt, pred


def fremy_dutch_provinces_to_wer():
    output = {}
    print(provinces)
    for province_name in provinces:
        output[province_name] = fremy_dutch_province_to_wer(province_name)
    return output

def show_wer_duration_province_wer_dict(d):
    for province_name in d.keys():
        m = province_name.ljust(20)
        m += str(round(d[province_name][0],2)).ljust(6)
        m += str(round(d[province_name][1]/3600,2))
        print(m)

def provinces_wer_dict_to_cer(d):
    for province_name in d.keys():
        word_error_rate, duration, gt, pred = d[province_name]
        print(province_name,jiwer.cer(gt,pred))
        
        
    



