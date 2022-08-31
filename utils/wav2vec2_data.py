from datasets import load_dataset, Audio
from dataclasses import dataclass, field
from transformers import Wav2Vec2Processor
import torch

from utils.audio import load_audio_section
from utils.dialect import dialect_groups
from typing import Any, Dict, List, Optional, Union
import json

cache_dir = '/vol/tensusers/mbentum/ASTA/WAV2VEC_DATA/'

def load_all_dialects():
    d = {}
    for dialect_name in dialect_groups.keys():
        d[dialect_name] = load_dialect(dialect_name)
    return d

def make_dialect_json_filename(dialect_name, cache_dir, split):
    return cache_dir + dialect_name + '_' + split + '.json'

def _load_audio(item):
    st, et = item['start_time'], item['end_time']
    filename = item['audiofilename']
    item['audio'] = {}
    item['audio']['array'] = load_audio_section(st,et,filename,
        sampling_rate = 1600)
    item['audio']['sampling_rate'] = 16000
    return item

def load_dialect(dialect_name, cache_dir = cache_dir, load_audio=True):
    d = {}
    for split in 'train,dev,test'.split(','):
        filename = make_dialect_json_filename(dialect_name,cache_dir,split)
        d[split] = load_dataset('json',data_files=filename,field='data',
            cache_dir = cache_dir)
        if load_audio:
            d[split] = d[split] = d[split].map(_load_audio)
    for key in d.keys():
        d[key] = d[key]['train']
    return d


@dataclass
class DataCollatorCTCWithPadding:
    '''
    Data collator that will dynamically pad the inputs received.

    processor   :class:`~transformers.Wav2Vec2Processor`
                The processor used for proccessing the data.
    padding     :obj:`bool`, :obj:`str` or
                :class:`~transformers.tokenization_utils_base.PaddingStrategy`,
                `optional`, defaults to :obj:`True`:

                Select a strategy to pad the returned sequences (according to
                the model's padding side and padding index)
                among:

                * :obj:`True` or :obj:`'longest'`:
                Pad to the longest sequence in the batch (or no padding
                if only a single sequence if provided).

                * :obj:`'max_length'`: Pad to a maximum length specified
                with the argument :obj:`max_length` or to the
                maximum acceptable input length for the model if that
                argument is not provided.

                * :obj:`False` or :obj:`'do_not_pad'` (default): No padding
                (i.e., can output a batch with sequences of
                different lengths).
    '''

    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True


    def __call__(self, features: List[Dict[str, Union[List[int],
        torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        '''
        split inputs and labels since they have to be of different lenghts
        and need different padding methods
        '''
        input_features = [{"input_values": f["input_values"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]

        batch = self.processor.pad(input_features,padding=self.padding,
            return_tensors="pt")

        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(label_features,
                padding=self.padding,return_tensors="pt")

        # replace padding with -100 to ignore loss correctly
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100)

        batch["labels"] = labels

        return batch

