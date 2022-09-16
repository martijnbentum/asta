var start_time = JSON.parse(document.getElementById('start-time').textContent);
var end_time = JSON.parse(document.getElementById('end-time').textContent);
var web_wav= JSON.parse(document.getElementById('web-wav').textContent);
var text_clean= JSON.parse(document.getElementById('text-clean').textContent);
var alignment= JSON.parse(document.getElementById('alignment').textContent);
var already_annotated=JSON.parse(document.getElementById('already-annotated').textContent);
var nocrlines=JSON.parse(document.getElementById('nocrlines').textContent);

console.log(start_time,end_time,alignment)
console.log(text_clean)
var form= document.getElementById('form')

var audio = document.getElementById('audio');

document.onkeyup = function (e) {
    console.log(e.which,e.code,e)
    handle_keypress(e.key)
}

function copy_transcription() {
	var textbox = document.getElementById('corrected_transcription');
    textbox.value= text_clean
}

function handle_keypress(key) {
    console.log('handling:',key)
	var textbox = document.getElementById('corrected_transcription');
    if (document.activeElement === textbox) {
        console.log('typing:',key,'in textbox; ignoring commands')
        return
    }
    if (audio.paused) {
        console.log('audio not playing')
        if (key == ' ') {
            console.log('playing audio')
            play()
        }
    }
    if (key == 'b') {
        document.getElementById('bad').click();
    }
    if (key == 's') {
        document.getElementById('start_match').click();
    }
    if (key == 'm') {
        document.getElementById('middle_match').click();
    }
    if (key == 'i') {
        document.getElementById('middle_mismatch').click();
    }
    if (key == 'e') {
        document.getElementById('end_match').click();
    }
    if (key == 'g') {
        document.getElementById('good').click();
    }
    if (key == 'p') {
        document.getElementById('previous').click();
    }
    if (key == 'n') {
        document.getElementById('next').click();
    }

}

function play() {
	audio.currentTime = start_time;
	console.log(audio, start_time, audio.currentTime)
	audio.play();
	audio.addEventListener('timeupdate', (event) => {
		console.log(audio.currentTime);
		if (audio.currentTime > end_time){
			audio.pause() 
		}
	});
}

function set_annotation_buttons() {
    console.log(alignment)
    var button_ids;
    button_ids = 'bad,start_match,middle_match,middle_mismatch,end_match,good'.split(',')
    console.log(button_ids)
    for (let i = 0; i < button_ids.length; i++) {
        var button_id = button_ids[i];
        var button = document.getElementById(button_id)
        console.log('handling button:', button_id)
        if (button_id == alignment || alignment == '') {
            if (button_id == 'bad') {
                button.classList.add('btn-danger')
            } else if (button_id == 'good') {
                button.classList.add('btn-success')
            } else {
                button.classList.add('btn-warning')
            }
        } else {
            button.classList.add('btn-light')
        }
    }
}

function set_prev_next_buttons() {
    var [line_index, record_index] = get_indices();
    console.log(line_index, record_index)
    if (record_index == 0 && line_index == 1) {
        var button = document.getElementById('previous')
        button.classList.add('lightgrey')
    }
    if (already_annotated != 'true') {
        var button = document.getElementById('next')
        button.classList.add('lightgrey')
    }
}

function previous() {
    var [line_index, record_index] = get_indices();
    console.log('previous', record_index,line_index, prev_next)
    if (record_index == 0 && line_index == 1) { 
        console.log('not going back')
        return 
    }
	var prev_next= document.getElementById('prev_next');
	prev_next.value = 'previous'
    console.log('previous', record_index==0,line_index==1, prev_next)
    form.submit()
}

function next() {
    console.log('previous', already_annotated, prev_next)
    if (already_annotated != 'true') { 
        console.log('not going forward')
        return 
    }
	var prev_next= document.getElementById('prev_next');
	prev_next.value = 'next';
    console.log('previous', already_annotated, prev_next)
    form.submit()
}

function get_indices() {
	var line_index= document.getElementById('line_index');
	line_index = parseInt(line_index.value) 
	console.log('line index:',line_index)
	var record_index= document.getElementById('record_index');
	record_index = parseInt(record_index.value) 
	console.log('record index:',record_index)
    return [line_index, record_index]
}

function set_quality(value) {
	var quality = document.getElementById('quality');
	quality.value = value;
	console.log(quality)
}

get_indices();
set_annotation_buttons();
set_prev_next_buttons();
