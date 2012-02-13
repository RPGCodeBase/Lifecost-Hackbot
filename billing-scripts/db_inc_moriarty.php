<?php
  function make_link () {
//      $link = new mysqli('localhost', 'billing', 'PASSWORD', 'billing');
//      $link->query("SET NAMES 'utf8'");
//      return $link;
     $link = mysql_pconnect('localhost', 'billing', 'PASSWORD');
     mysql_select_db('billing', $link);
     mysql_query("SET NAMES 'utf8'");
     return $link;
  }

 //это просто обертка для обращения к базе
 function make_query($query) {
    global $link;
    if (!isset($link)) {
        $link = make_link();
    }
    
    $result = mysql_query($query);//$query
    return $result;
 }

 function fetch_value($query){
    if ($res = make_query($query))
        if ($res = mysql_fetch_array($res))
            return $res[0];
    return NULL;
 }

 function read_error(){
    say("Не смогла прочитать то, что нужно :(<span class='hidden'>" . mysql_error() . "</span>", 1);
 }

 function write_error(){
    say("Не смогла записать то, что нужно :(<span class='hidden'>" . mysql_error() . "</span>", 1);
 }

?>
