import praatio
from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier


def make_filename(recording):
    '''create filename based on the mp3_url of the audio file
    '''
    name = recording.mp3_url
    name = name.split('soundbites/')[-1].split('.')[0]
    name = name.replace('/','--')
    return '../textgrids/' + name + '.textgrid'

def _insert_overlap(ok,overlap,after):
    if len(ok) == 0: 
        before = overlap[0][0]
        if before.ocrline_index < after.ocrline_index:
            ok.append(before)
        else: return
    before = ok[-1]
    for lines in overlap:
        line = lines[0]
        if before.ocrline_index < line.ocrline_index < after.ocrline_index:
            ok.append(line)

def _combine_text_ocr_lines(lines):
    output = lines[0]
    if len(lines) == 1: return output
    text = ' '.join([x.ocr_text for x in lines[1:]])
    chunked_indices = [x.ocrline_index for x in lines]
    output.ocr_text
    output.transcription._text_clean += ' ' + text
    output.chunked_indices = chunked_indices
    return output

def _chunk_not_ok(not_ok):
    chunk = []
    chunks = []
    for i,line in enumerate(not_ok):
        if len(chunk) == 0: chunk.append(line)
        elif chunk[-1].ocrline_index == line.ocrline_index -1:
            chunk.append(line)
        else:
            output = _combine_text_ocr_lines(chunk)
            chunks.append(output)
            chunk = []
    if chunk: chunks.append( _combine_text_ocr_lines(chunk) )
    return chunks

def _find_times(ocrline_index, ok, end_time):
    if ocrline_index == 0:
        start = 0.0
        if ok[0].start_time > 0: end = ok[0].start_time
        else: end = 1.0
        print(ocrline_index,start, end)
        return start, end
    for i,line in enumerate(ok):
        if i >= len(ok) -1: 
            start = line.end_time
        elif line.ocrline_index < ocrline_index < ok[i+1].ocrline_index:
            start = line.end_time
            end = ok[i+1].start_time
            print(ocrline_index,start, end)
            return start, end
    end = end_time
    print(ocrline_index,start, end)
    return start,end


def _set_start_end_time_not_ok(ok,not_ok, end_time):
    print('chunking not ok',len(not_ok))
    not_ok = _chunk_not_ok(not_ok)
    print('n not ok = ',len(not_ok))
    output = []
    last_start, last_end = None, None
    for i,line in enumerate(not_ok):
        start, end = _find_times(line.ocrline_index, ok, end_time)
        print(i, 'times', line.ocrline_index, start,end,last_start,last_end)
        if i > 0 and last_start == start and last_end == end:
            print(' updating last line --:',output[-1].ocr_text )
            output[-1].ocr_text 
            output[-1].transcription._text_clean += ' ' + line.ocr_text
            print(' updated last line --:',output[-1].ocr_text )
        else: 
            line.inferred_start_time = start
            line.inferred_end_time = end
            output.append( line )
        last_start, last_end = start, end
    not_ok = output
    return not_ok
        
def _fix_short_not_ok(not_ok, end_time):
    for i,line in enumerate(not_ok):
        if i > 0:
            last_end = not_ok[i-1].inferred_end_time
        else: last_end = 0
        if i < len(not_ok) - 1:
            next_start = not_ok[i+1].inferred_start_time
        else: next_start = end_time
        start,end = line.inferred_start_time, line.inferred_end_time
        print('pre --:',start,end)
        duration = end - start
        if duration >= 2: continue
        start -= 1
        if start < last_end: start = last_end
        end += 1
        if end > next_start: end = next_start 
        line.inferred_start_time = start
        line.inferred_end_time = end
        print('post --:',start,end)

def _handle_ocr_lines(recording):
    ocr_lines = recording.align.ocr_lines
    overlap, overlap_indices = get_ocr_line_overlap(ocr_lines)
    not_ok = []
    ok = []
    for i,ocr_line in enumerate(ocr_lines):
        if ocr_line.ocrline_index in overlap_indices: continue
        if not _check_ocr_line_times_ok(ocr_line):
            not_ok.append(ocr_line)
        else:
            _insert_overlap(ok,overlap,ocr_line)
            ok.append(ocr_line)
    not_ok = _set_start_end_time_not_ok(ok,not_ok, recording.duration)
    _fix_short_not_ok(not_ok, recording.duration)
    return ok, not_ok, overlap

def _check_ocr_line_times_ok(ocr_line):
    '''check if the times of an ocr line are ok.'''
    if not ocr_line.ok: return False
    if ocr_line.start_time == False: return False
    if ocr_line.end_time == False: return False
    if ocr_line.start_time > ocr_line.end_time: return False
    return True

def get_ocr_line_overlap(ocr_lines):
    overlap, overlap_indices = [], []
    for i,line in enumerate(ocr_lines):
        if not _check_ocr_line_times_ok(line): continue
        if line.ocrline_index in overlap_indices: continue
        start, end = line.start_time, line.end_time
        if i == len(ocr_lines)-1: break
        overlap_lines = []
        for other_line in ocr_lines[i+1:]:
            if not _check_ocr_line_times_ok(other_line): continue
            if other_line.ocrline_index in overlap_indices: continue
            other_start, other_end = other_line.start_time, other_line.end_time
            if other_start > end: break
            if line.ocrline_index not in overlap_indices:
                overlap_indices.append(line.ocrline_index)
                overlap_lines.append(line)
            overlap_lines.append(other_line)
            overlap_indices.append(other_line.ocrline_index)
        if overlap_lines: overlap.append(overlap_lines)
    return overlap, overlap_indices

def _make_aligned_lines(recording):
    manual, asr= [],[]
    for line in recording.align.ocr_lines:
        if not line.ok: continue
        start = line.start_time
        end = line.end_time
        if start >= end: continue
        label = line.ocr_text
        manual.append([start,end,label])
        label = line.asr_text
        asr.append([start,end,label])
    return manual, asr


def _check_overlap(manual,asr):
    output_manual, output_asr, overlap_manual = [], [], []
    overlaps = []
    for i,line in enumerate(manual):
        start, end, label = line
        if i == len(manual)-1: break
        found_overlap = False
        for other_line in manual[i+1:]:
            other_start, other_end, ol = other_line
            if other_start > end: break
            else: 
                overlaps.append([i,line,other_line])
                found_overlap = True
        if not found_overlap: 
            output_manual.append(line)
            output_asr.append(asr[i])
    return overlaps, output_manual,output_asr

            
            
        


def recording_to_textgrid(recording):
    '''create textgrid for a recording.'''
    tg = textgrid.Textgrid()
    manual, asr = _make_aligned_lines(recording)
    manual_overlap, manual, asr = _check_overlap(manual, asr)
    tg.addTier( make_tier(manual, 'manual transcription') )
    tg.addTier( make_tier(asr, 'wav2vec transcription') )
    name = make_filename(recording)
    tg.save(name, 'short_textgrid', True)
    return textgrid

def make_tier(lines, tier_label):
    '''create tier based on all transcription lines'''
    intervals = []
    for line in lines:
        start, end, label = line
        intervals.append( make_interval( start, end, label ) )
    tier = interval_tier.IntervalTier(name = tier_label, entries = intervals)
    return tier

def make_interval(start,end,label):
    return Interval(start,end,label)


