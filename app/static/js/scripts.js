function getId(clicked_Id) {
  let ele = document.querySelector('input[name="actions"]:checked').value;
  document.getElementById(clicked_Id).className = ele + " px-0 hand-edit";
  let num_range = clicked_Id.substring(clicked_Id.length - 1);
  let list_ranges = JSON.parse(document.getElementById("new_range").value.replace(/'/g, '"'));
  let wtf_range = new Object(list_ranges[num_range - 1]);
  wtf_range["_" + clicked_Id.substring(0, clicked_Id.length - 2)] = document.getElementById(clicked_Id).className;
  list_ranges[num_range - 1] = wtf_range;
  document.getElementById("new_range").value = JSON.stringify(list_ranges);
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
  window.location = window.location.protocol + "//" + window.location.host + "/modifier_ranges/" + monId + "/" + url_villain + "/";
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
  window.location = window.location.protocol + "//" + window.location.host + "/modifier_ranges/" + state_phero.value + "/" + monId.replace("vs ","") + "/";
};

function ShowFreq(monId) {
  let choix = document.forms.choix;
  let state_phero = choix.elements.phero;
  let state_pvillain = choix.elements.pvillain;
  window.location = window.location.protocol + "//" + window.location.host + "/ranges/" + state_phero.value + "/" + state_pvillain.value + "/" + monId + "/";
};

function razRange() {
  var x = document.getElementsByName("hand");
  var i;
  for (i = 0; i < x.length; i++) {
    x[i].className = "btn btn-info px-0 hand-edit";
  }
};

function ShowWaiting() {
    if (document.getElementsByName("form")[0].checkValidity() === true) {
        document.getElementById("loading").style.display = "block";
        document.getElementById("filtre").style.display = "none";
        document.getElementById("submit").style.display = "none";
    }
};