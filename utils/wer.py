from jiwer import wer
from utils import make_dataset as md

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
        

