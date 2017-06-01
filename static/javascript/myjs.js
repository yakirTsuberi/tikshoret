/**
 * Created by YakirTsuberi on 5/31/2017.
 */
var connections = 1;
var container = document.getElementById('container');
function add_connect() {
    var div = document.createElement('div');
    connections += 1;
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