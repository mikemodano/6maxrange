function loadpage() {
    document.getElementById("BB").checked = true;
    document.getElementById("vs BU").checked = true;
}

var wtf_range = new Object();

function getId(monId) {
  let ele = document.getElementsByName('actions');
  for(i = 0; i < ele.length; i++) {
      if(ele[i].checked)
      document.getElementById(monId).className = ele[i].value + " px-0 hand";
      wtf_range[monId] = document.getElementById(monId).className;
      document.getElementById("new_range").value = JSON.stringify(wtf_range);
  }
};

function ShowFacing(monId) {
  let choix = document.forms.choix;
  let state_pvillain = choix.elements.pvillain;
  if (monId == "BB" && state_pvillain.value == "UO") {
    url_villain = "BU";
  }
  else if (state_pvillain.value == monId || state_pvillain.value == "") {
    url_villain = "UO";
  }
  else {
    url_villain = state_pvillain.value;
  }
  let ladate=new Date();
  let minutes = ladate.getMinutes();
  window.location = "http://127.0.0.1:5000/ranges/" + monId + "/" + url_villain + "/0/";
};

function ShowFacing2(monId) {
    document.getElementById("UO").className = "btn btn-primary px-3 mx-1";
    document.getElementById("vs SB").className = "btn btn-primary px-3 mx-1";
    document.getElementById("vs BU").className = "btn btn-primary px-3 mx-1";
    document.getElementById("vs CO").className = "btn btn-primary px-3 mx-1";
    document.getElementById("vs MP").className = "btn btn-primary px-3 mx-1";
    document.getElementById("vs UTG").className = "btn btn-primary px-3 mx-1";
    if (monId == "BB") {
        document.getElementById("UO").className = "d-none";
    }
    else {
        document.getElementById("vs " + monId).className = "d-none";
    }
};

function ShowAction(monId) {
  let choix = document.forms.choix;
  let state_phero = choix.elements.phero;
  let state_numrange = choix.elements.num_range;
  let ladate=new Date();
  let minutes = ladate.getMinutes();
  window.location = "http://127.0.0.1:5000/ranges/" + state_phero.value + "/" + monId.replace("vs ","") + "/0/";
};

function ShowAction2(monId) {
    if (monId == "UO") {
        document.getElementById("action2").className = "bloc-bouton";
        document.getElementById("action1").className = "d-none";
    }
    else {
        document.getElementById("action1").className = "bloc-bouton";
        document.getElementById("action2").className = "d-none";
    }
};

function ShowFreq(monId) {
  let choix = document.forms.choix;
  let state_phero = choix.elements.phero;
  let state_pvillain = choix.elements.pvillain;
  window.location = "http://127.0.0.1:5000/ranges/" + state_phero.value + "/" + state_pvillain.value + "/" + monId + "/";
};

function razRange() {
  var x = document.getElementsByName("hand");
  var i;
  for (i = 0; i < x.length; i++) {
    x[i].className = "btn btn-info px-0 hand";
  }
};
