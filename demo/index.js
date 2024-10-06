var unk_user_timer_id, intervalId, language_id, vocal_id;
// log display function
function append(text) {
  // document.getElementById("websocket_events").insertAdjacentHTML('beforeend', "<li>" + text + ";</li>");
  console.log(text);
}

function stopWelcomingTimer() {
  clearInterval(intervalId);
}

function stopLanguageTimer() {
  clearInterval(language_id);
}

function stopWelcomingUnknownUserTimer() {
  clearInterval(unk_user_timer_id);
}

function stopVocalTimer() {
  clearInterval(vocal_id);
}

function startWelcomingTimer() {
  if (intervalId) {
    return
  }

  var changed = true;
  intervalId = setInterval(function () {
    if (changed) {
      document.getElementById('text_default').innerText = "Put yourself in front of me to start";
      changed = false;
    } else {
      document.getElementById('text_default').innerText = "Mettiti di fronte a me per iniziare.";
      changed = true;
    }
  }, 5000); // 5000 milliseconds = 5 seconds
  console.log("SURE ID " + intervalId)
}

function startLanguageTimer() {

  if (language_id) {
    return
  }
  var changed = true;
  language_id = setInterval(function () {
    if (changed) {
      document.getElementById('text_default').innerText = "Che lingua preferisci: italiano o inglese?";
      changed = false;
    } else {
      document.getElementById('text_default').innerText = "Choose your language: italian or english?";
      changed = true;
    }
  }, 5000); // 5000 milliseconds = 5 seconds
}

function startWelcomingUnknownUserTimer() {

  if (unk_user_timer_id) {
    return
  }
  var changed = true;
  unk_user_timer_id = setInterval(function () {
    if (changed) {
      document.getElementById('text_default').innerText = "Hi! I don't think I know you, would you prefer to use vocal commands or the touchscreen?";
      changed = false;
    } else {
      document.getElementById('text_default').innerText = "Ciao! Non credo di conoscerti, vuoi usare la modalità vocale o preferisci usare il touchscreen?";

      changed = true;
    }
  }, 5000); // 5000 milliseconds = 5 seconds
}
function startVocalTimer() {

  if (vocal_id) {
    return
  }
  var changed = true;
  vocal_id = setInterval(function () {
    if (changed) {
      document.getElementById('vocal').value = "Comandi vocali";
      changed = false;
    } else {
      document.getElementById('vocal').value = "Vocal commands";
      changed = true;
    }
  }, 5000); // 5000 milliseconds = 5 seconds
}
// websocket global variable
var websocket = null;

function wsrobot_connected() {
  var connected = false;
  if (websocket != null)
    console.log("websocket.readyState: " + websocket.readyState)
  if (websocket != null && websocket.readyState == 1) {
    connected = true;
  }
  console.log("connected: " + connected)
  return connected;
}

function wsrobot_init(ip, port) {
  var url = "ws://" + ip + ":" + port + "/modimwebsocketserver";
  console.log(url);
  websocket = new WebSocket(url);

  websocket.onmessage = function (event) {
    //stopWelcoming();

    console.log("message received: " + event.data);
    v = event.data.split('_');
    console.log(v)

    if (v[0] == 'display') {
      if (v[1] == 'text')
        document.getElementById(v[1] + '_' + v[2]).innerHTML = v[3];
      else if (v[1] == 'image') {
        p = v[3];
        for (i = 4; i < v.length; i++) {
          p = p + "_" + v[i];
        }
        console.log("image: " + p);
        document.getElementById(v[1] + '_' + v[2]).src = p;
      }
      else if (v[1] == 'button') {
        var b = document.createElement("input");
        //Assign different attributes to the element. 
        p = v[2]
        for (i = 3; i < v.length; i++) {
          p = p + "_" + v[i];
        }
        console.log(p);
        vp = p.split('$');

        if (vp[1].substr(0, 3) == 'img') {
          b.type = "image";
          b.src = vp[1];
        }
        else {
          b.type = "button";
          b.value = vp[1];
        }

        b.name = vp[0];
        b.id = vp[0];
        b.onclick = function (event) { button_fn(event) };
        var bdiv = document.getElementById("buttons");
        bdiv.appendChild(b);
      }
    }
    else if (v[0] == 'remove') {
      if (v[1] == 'buttons') {
        var bdiv = document.getElementById("buttons");
        var fc = bdiv.firstChild;
        while (fc) {
          bdiv.removeChild(fc);
          fc = bdiv.firstChild;
        }

      }
    }
    else if (v[0] == 'url') {
      p = v[1]
      for (i = 2; i < v.length; i++) {
        p = p + "_" + v[i];
      }
      console.log('load url: ' + p)
      window.location.assign(p)
    }

    if (v[0] === "display" && v[1] === "image") {

      image_name = v[3].split("/")[1].split(".")[0];
      console.log("NOME IMG" + image_name)
      if (image_name === "welcome") {
        stopLanguageTimer()
        stopWelcomingUnknownUserTimer()
        stopVocalTimer()

        startWelcomingTimer()
      }

      else if (image_name === "registration") {
        stopWelcomingTimer()
        stopLanguageTimer()

        startWelcomingUnknownUserTimer()
        startVocalTimer()

      }

      else if (image_name === "language") {
        stopWelcomingTimer()
        stopWelcomingUnknownUserTimer()
        stopVocalTimer()
        
        startLanguageTimer()
      }

      else if (image_name === "hello") {
        stopWelcomingTimer()
        stopWelcomingUnknownUserTimer()
        stopLanguageTimer()
        stopVocalTimer()

      }

      else {
        stopWelcomingTimer()
        stopWelcomingUnknownUserTimer()
        stopLanguageTimer()
        stopVocalTimer()

      }
    }
  }

  websocket.onopen = function () {
    append("connection received");
    document.getElementById("status").innerHTML = "<font color='green'>OK</font>";

  }

  websocket.onclose = function () {
    append("connection closed");
    document.getElementById("status").innerHTML = "<font color='red'>NOT CONNECTED</font>";
  }

  websocket.onerror = function () {
    append("!!!connection error!!!");
  }

}

function wsrobot_quit() {
  websocket.close();
  websocket = null;
}

function wsrobot_send(data) {
  if (websocket != null)
    websocket.send(data);
}

function button_fn(event) {
  var bsrc = event.srcElement || event.originalTarget
  console.log('websocket button ' + bsrc.id)
  wsrobot_send(bsrc.id);
}


// MODIM Code port

ip = window.location.hostname;
if (ip == '')
  ip = '127.0.0.1';

// to connect from a remote client, set modim IP here
// ip='10.0.1.200'
codeport = 9010;
codeurl = "ws://" + ip + ":" + codeport + "/websocketserver";
console.log(codeurl);
codews = new WebSocket(codeurl);

codews.onopen = function () {
  console.log("codews connection received");
}



