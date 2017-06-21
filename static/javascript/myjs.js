/**
 * Created by YakirTsuberi on 5/31/2017.
 */
var exist_client = document.getElementsByName("exist_client")[0];
function fill_all(inputs, data, cnt) {
    for (var i in inputs) {
        if (data[i] !== undefined) {
            inputs[i].value = data[cnt] === 'none' ? '' : data[cnt];
        }
        cnt += 1;

    }
}
function clean_all() {
    var all_input = document.getElementsByTagName('input');
    for (i in all_input) {
        if (!all_input[i].name.startsWith('sim_num')) {
            all_input[i].value = null
        }
    }
}
exist_client.addEventListener('change', function () {
    var client_input = document.getElementById('client_input').getElementsByTagName('input');
    var credit_card_input = document.getElementById('credit_card_input').getElementsByTagName('input');
    var bank_input = document.getElementById('bank_input').getElementsByTagName('input');
    var shownVal = document.getElementById("client").value;
    var value2send = document.querySelector("#clients option[value='" + shownVal + "']");
    if (value2send) {
        var data_client = JSON.parse(value2send.dataset.value.split('(').join('[').split(')').join(']').split("'").join('"'));

        fill_all(client_input, data_client[0], 1);
        fill_all(bank_input, data_client[1], 2);
        fill_all(credit_card_input, data_client[2], 2);
    } else {
        clean_all()
    }
});

var connections = document.querySelectorAll('input[name^="sim_num"]').length;
var container = document.getElementById('container');
function add_connect() {
    var div = document.createElement('div');
    connections += 1;
    console.log(connections);
    var start_sim = document.getElementsByName('sim_num1')[0].value;
    var html = '<div class="panel panel-primary"><div class="panel-heading"><span>מסלול</span><span class="pull-left">' + connections + '</span></div><div class="panel-body"><input value="' + start_sim + '" class="form-control" name="sim_num' + connections.toString() + '" placeholder="מספר סים" type="text" required="required"/><input class="form-control" name="phone_num' + connections.toString() + '" placeholder="מספר לניוד" type="text" required="required"/></div></div>';
    div.innerHTML = html;
    container.appendChild(div);
}
function remove_connect() {
    if (container.children.length > 1) {
        container.removeChild(container.lastElementChild);
        connections -= 1
    }
}