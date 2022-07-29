var start_time = JSON.parse(document.getElementById('start-time').textContent);
var end_time = JSON.parse(document.getElementById('end-time').textContent);
var web_wav= JSON.parse(document.getElementById('web-wav').textContent);

console.log(start_time,end_time)

function play() {
	var audio = document.getElementById('audio');
	audio.currentTime = start_time;
	console.log(audio)
	audio.play();
	audio.addEventListener('timeupdate', (event) => {
		console.log(audio.currentTime);
		if (audio.currentTime > end_time){
			audio.pause() 
		}
	});
}


function update_indices() {
	var line_index= document.getElementById('line_index');
	line_index.value = parseInt(line_index.value) +1
	console.log('updated line index:',line_index.value)
	var record__index= document.getElementById('record_index');
	console.log('record index:',record_index.value)
}

function set_quality(value) {
	var quality = document.getElementById('quality');
	quality.value = value;
	console.log(quality)
}

update_indices();

