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

function set_quality(value) {
	var quality = document.getElementById('quality');
	quality.value = value;
	console.log(quality)
}


function play1() {
	var duration = end_time - start_time;
	//console.log('play audio {{a.recording.web_mp3}}')
	console.log(web_wav)
	var audio = new Audio(web_wav);
	console.log('audio: ',audio)
	audio.currentTime=start_time;
	console.log('play', start_time, start_time)
	var play_promise = audio.play();
	console.log(play_promise);
	/*
	if (play_promise !== undefined) {
		console.log('ok')
		play_promise.then( function () {
			setTimeout(function () {
				console.log('stop {{o.stop_time}}',duration)
				audio.pause();
			}, duration);
		})
	}
	*/
}
