<?php
//exec('nohup sudo python visualization.py spectrum &');


if(isset($_GET['off'])) {
    exec('sudo killall python');
    echo exec('sudo python off.py 2>&1');
}

if(isset($_GET['on'])) {
   $visType = $_GET['on'];
   exec('nohup sudo python visualization.py ' . $visType . ' &');
} else {
   echo "nada";
}
?>
