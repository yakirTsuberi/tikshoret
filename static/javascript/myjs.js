/**
 * Created by YakirTsuberi on 5/31/2017.
 */
var connections = 0;
var container = document.getElementById('container');
add_connect();
function add_connect() {
    console.log(connections);
    var div = document.createElement('div');
    connections += 1;
    var html = '<div class="panel panel-primary"><div class="panel-heading"><span>מסלול</span><span class="pull-left">' + connections + '</span></div><div class="panel-body"><input class="form-control" name="sim_num' + connections.toString() + '" placeholder="מספר סים" type="text" required="required"/><input class="form-control" name="phone_num' + connections.toString() + '" placeholder="מספר לניוד" type="text" required="required"/></div></div>';
    div.innerHTML = html;
    container.appendChild(div);
}
function loading() {
    document.getElementById('pageloader').style.visibility = 'visible';
}