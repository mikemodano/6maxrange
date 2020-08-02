var wtf_range = new Object();

function getId(monId) {
  let ele = document.getElementsByName('actions');
  wtf_range = JSON.parse(document.getElementById("new_range").value);
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
  window.location = window.location.protocol + "//" + window.location.host + "/ranges/" + monId + "/" + url_villain + "/0/";
};

function ShowFacing2(monId) {
  let choix = document.forms.choix2;
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
  window.location = window.location.protocol + "//" + window.location.host + "/modifier_ranges/" + monId + "/" + url_villain + "/0/";
};

function ShowAction(monId) {
  let choix = document.forms.choix;
  let state_phero = choix.elements.phero;
  let state_numrange = choix.elements.num_range;
  window.location = window.location.protocol + "//" + window.location.host + "/ranges/" + state_phero.value + "/" + monId.replace("vs ","") + "/0/";
};

function ShowAction2(monId) {
  let choix = document.forms.choix2;
  let state_phero = choix.elements.phero;
  let state_numrange = choix.elements.num_range;
  window.location = window.location.protocol + "//" + window.location.host + "/modifier_ranges/" + state_phero.value + "/" + monId.replace("vs ","") + "/0/";
};

function ShowFreq(monId) {
  let choix = document.forms.choix;
  let state_phero = choix.elements.phero;
  let state_pvillain = choix.elements.pvillain;
  window.location = window.location.protocol + "//" + window.location.host + "/ranges/" + state_phero.value + "/" + state_pvillain.value + "/" + monId + "/";
};

function ShowFreq2(monId) {
  let choix = document.forms.choix2;
  let state_phero = choix.elements.phero;
  let state_pvillain = choix.elements.pvillain;
  window.location = window.location.protocol + "//" + window.location.host + "/modifier_ranges/" + state_phero.value + "/" + state_pvillain.value + "/" + monId + "/";
};

function razRange() {
  var x = document.getElementsByName("hand");
  var i;
  for (i = 0; i < x.length; i++) {
    x[i].className = "btn btn-info px-0 hand";
  }
};