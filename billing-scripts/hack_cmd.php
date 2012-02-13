<?php
$tgt = $_GET["target"];
$cmd = $_GET["cmd"];
$args = explode(' ',$_GET["args"]);
if ($args[0] =='')
    $args=array();
include ("db_inc_moriarty.php");
make_link();

function get_client($tgt) {
    $query = "SELECT c.clnt_name as name, c.balance as balance, c.max_overdraft, c.clnt_id as id, LOWER(c.clnt_name) as name, GROUP_CONCAT(t.teg_name) as tags,GROUP_CONCAT(t.groups) as groups, c.is_company FROM clients as c
    LEFT JOIN tegs_clnt  as tc ON (c.clnt_id = tc.clnt_id)
    LEFT JOIN tegs as t ON (t.teg_id = tc.teg_id)
    WHERE REPLACE(LOWER(clnt_name),' ','_') = '".mysql_real_escape_string($tgt)."' GROUP BY c.clnt_id";
    if (!($res = make_query($query))) {
        return false;
    }
    $target = mysql_fetch_assoc($res);
    if (!$target) {
        return false;
    }
    return $target;
}

function move_money_hack($src_clnt, $dst_clnt, $mg_balance_dirt, $mg_comment) {
   //echo "$trsubs_id, $src_clnt, $mgclnt_def, $mg_balance, $mg_comment<BR/>\n";
   $dst_clnt = intval($dst_clnt);$src_clnt=intval($src_clnt);
   $query = "select subs_subs_id from subs_clnt where master_subs_id is NULL and clnt_clnt_id = $dst_clnt";
   if(!$res = make_query($query)) {echo 'ERROR1111!!!!';die;}
   if ($s = mysql_fetch_assoc($res)) $trsubs_id = $s['subs_subs_id'];
   else {
    $query = "select subs_subs_id from subs_clnt where master_subs_id = subs_subs_id and clnt_clnt_id = $dst_clnt";
    if(!$res = make_query($query)) {echo 'ERROR1111!!!!';die;}
    if ($s = mysql_fetch_assoc($res)) $trsubs_id = $s['subs_subs_id'];
    else {echo 'Invalid parameters';die;}
   }
   //выберем из суммы только цифры
   $mg_balance = intval($mg_balance_dirt);
   if($mg_balance <= 0){echo 'Invalid parameters';die;}
    $mg_comment = mysql_real_escape_string($mg_comment);
   //ищем клиента-получателя с заданным именем
   make_query('Start transaction');
   $query = "insert into money_transactions(tran_date, clnt_src, clnt_dst, oper_subs_id, amount, comment) values "
            ."('".time()."', $src_clnt, $dst_clnt, $trsubs_id, $mg_balance, '$mg_comment')";
   //echo "$query<BR/>";
   $res3 = make_query($query);
   $query = "update clients set balance=balance - $mg_balance where clnt_id = $src_clnt";
   $res4 = make_query($query);
   $query = "update clients set balance=balance + $mg_balance where clnt_id = $dst_clnt";
   $res5 = make_query($query);
    make_query('commit');
 }//move_money 
 
function time_form_money_transactions($clnt_id, $all) {   // Вывод списка транзакций за указанное время по клиенту.
    global $smallog_size;
   $trantime = time() - $smallog_size;
   if ($all) { // Мастер видит все транзакции. Остальные - только за час
   $timer="";   
   }
   else
   {
   $timer=" and mt.tran_date > $trantime";
   }
   $query2 = "select -1 as dir, c.clnt_name, mt.tran_date, mt.amount, mt.comment from money_transactions mt, clients c"
            ." where mt.clnt_src = $clnt_id and mt.clnt_dst = c.clnt_id $timer "
			." union"
            ." select 1 as dir, c.clnt_name, mt.tran_date, mt.amount, mt.comment from money_transactions mt, clients c"
            ." where mt.clnt_dst = $clnt_id and mt.clnt_src = c.clnt_id  $timer "
            ." order by tran_date desc"
			;
   if(!$res2 = make_query($query2)) {
     echo("no data");
	 return;
   }
   echo "Transactions: \n";
   while($array2 = mysql_fetch_assoc($res2)) {
    echo date("Y.m.d H:i:s", $array2["tran_date"])."\t".
    (($array2["dir"] > 0)?"Приход":"Расход")."\t".
    $array2["amount"]."\t".$array2["clnt_name"]."\t".
    $array2["comment"]."\n";
   }
}
function time_form_rating_transactions($clnt_id) {   // Вывод списка транзакций за указанное время по клиенту.
   global $smallog_size;
   $trantime = time() - $smallog_size;
   $query2 = "select -1 as dir, c.clnt_name, mt.tran_date, mt.amount, mt.comment from rating_transactions mt, clients c"
            ." where mt.clnt_src = $clnt_id and mt.clnt_dst = c.clnt_id"
			." union"
            ." select 1 as dir, c.clnt_name, mt.tran_date, mt.amount, mt.comment from rating_transactions mt, clients c"
            ." where mt.clnt_dst = $clnt_id and mt.clnt_src = c.clnt_id"
            ." order by tran_date desc"
			;   if(!$res2 = make_query($query2)) {
     echo("no data");
	 return;
   }
   echo "Transactions: \n";
   while($array2 = mysql_fetch_assoc($res2)) {
    echo date("Y.m.d H:i:s", $array2["tran_date"])."\t".
    $array2["amount"]."\t".
    $array2["comment"]."\n";
   }
}//time_form_money_transactions


$rewards_all = array("showmoney","smallmoney","healthget","lasttransactions","votes","hacklog","alltransactions","healthadd","bigmoney","deface","clearlogs","emplinfo","ratinglog");
$sm_fraction = .05;
$bm_fraction = .15;
$fluct_fraction = .25;
$smin_transaction = 10;
$bmin_transaction = 100;
$smallog_size = 3600;

$target = get_client($tgt);
if (!$target) {
    echo 'ERROR1111!!!!';
    die;
}
$tags = explode(',',$target['tags']);
$groups = explode(',',$target['groups']);
$id = $target['id'];
if (array_search('мастер',$groups) !== false)
    continue;
if (array_search('bank',$tags) !== false)
    continue;
if (array_search('dead',$tags) !== false)
    continue;    
if (array_search('foreign',$tags) !== false)
    continue;
if ($cmd == "showmoney") {
    $money = $target['balance'];
    echo "$tgt has $money$";
} else if ($cmd =="smallmoney" or $cmd =="bigmoney") {
    if (count($args) < 1) {echo 'invalid parameters';die;}
//    print_r($args);
    $to = get_client($args[0]);
    if (!$to) {echo 'invalid parameters';die;}
    $fraction = ($cmd =="bigmoney"?$bm_fraction:$sm_fraction)*(1+$fluct_fraction*(rand(0,200)-100)/100.);
    $sum = max(min(max(floor($target['balance']*$fraction),$cmd =="bigmoney"?$bmin_transaction:$smin_transaction),$target['balance']+$target['max_overdraft']),0);
    unset($args[0]);
//    move_money_hack($id, $to['id'], $sum, join(' ',$args));
    echo $sum.'$ transferred to '.$to['name'];
} else if ($cmd =="healthget") {
    if (!($res = make_query("SELECT CONCAT(log,' ',FROM_UNIXTIME(modified_at)) from illness_log WHERE client_id = '$id'"))) {echo 'ERROR1111!!!!';die;}
    $text = mysql_result($res,0);
    if (!$text) echo 'Healthy as a bull!';
    else echo $text;
} else if ($cmd =="healthadd") {
    if (!($res = make_query("SELECT log, modified_by from illness_log WHERE client_id = '$id'"))) {echo 'ERROR1111!!!!';die;}
    $rec = mysql_fetch_assoc($res);
    if (!$rec) {
        $log = ''; $mid = $id;
    } else 
        $log = $rec['log']; $mid = $rec['modified_by'];
    $log = mysql_real_escape_string($rec['log'].$_GET["args"]);
//    if (!($res = make_query("REPLACE INTO illness_log(client_id, log,modified_by, modified_at) VALUES('$id', '$log', '$mid', UNIX_TIMESTAMP(now()))"))) {echo 'ERROR1111!!!!';die;}
    echo $log;
} else if ($cmd =="lasttransactions") {
    time_form_money_transactions($id);
} else if ($cmd =="alltransactions") {
    time_form_money_transactions($id, true);
} else if ($cmd =="votes") {
    if (!($res = make_query("SELECT pa.party_name FROM polls as pl INNER JOIN parties as pa ON (pl.party_party_id = pa.party_id) INNER JOIN subs_clnt as sc ON (pl.subs_subs_id = sc.subs_subs_id AND sc.master_subs_id is NULL) WHERE vote_vote_id = (SELECT vote_id FROM votes v ORDER BY vote_id DESC LIMIT 1) AND sc.clnt_clnt_id = $id"))) {echo 'ERROR1111!!!!';die;}
    $party = mysql_result($res);
    if (!$party) echo 'No votes';
    else echo "Last vote: $party";
} else if ($cmd =="hacklog") {
    if (!($res = make_query("SELECT s.login, l.completed FROM hack_log as l
INNER JOIN subs_clnt as sc ON (sc.clnt_clnt_id = l.hacker_id)
INNER JOIN subscribers as s ON (s.subs_id = sc.subs_subs_id AND sc.master_subs_id IS NULL)
where (NOT l.deleted) AND l.target = '".mysql_real_escape_string($tgt)."' ORDER BY completed DESC"))) {echo 'ERROR1111!!!!';die;}
   echo "Hacks: \n";
   while($log = mysql_fetch_assoc($res)) {
    echo $log["completed"]."\t".$log["login"]."\n";
   }
} else if ($cmd =="deface") {
    if (!($res = make_query("SELECT s.blog_id FROM subs_clnt as sc
INNER JOIN subscribers as s ON (s.subs_id = sc.subs_subs_id AND sc.master_subs_id IS NULL)
where sc.clnt_clnt_id = '$id'"))) {echo 'ERROR1111!!!!';die;}
    $blog_id=mysql_result($res,0);
    if (!$blog_id) {echo 'Invalid target';die;}
    $content = mysql_real_escape_string($_GET["args"]);
//    if (!($res = make_query("INSERT INTO statusnet.notice (profile_id, content, created, modified, reply_to,is_local, source, conversation) VALUES ('$blog_id', '$content', UTC_TIMESTAMP(), UTC_TIMESTAMP(), NULL,1, 'web', NULL)"))) {echo 'ERROR1111!!!!';die;}
//   $insert_id = mysql_insert_id();
//    if (!($res = make_query("UPDATE statusnet.notice SET uri = CONCAT('http://livenice.lifecost.tv/index.php/notice/','$insert_id') WHERE id ='$insert_id'"))) {echo 'ERROR1111!!!!';die;}
    echo 'DEFACED ;-)';
} else if ($cmd =="clearlogs") {
//    if (!($res = make_query("UPDATE hack_log SET deleted = True WHERE target = '".mysql_real_escape_string($tgt)."'"))) {echo 'ERROR1111!!!!';die;}
    echo 'Who\'s there? ;-)';
} else if ($cmd =="emplinfo") {
    if (!($res = make_query("SELECT c.clnt_name FROM subs_clnt as sc
INNER JOIN subscribers as s ON (s.subs_id = sc.subs_subs_id AND sc.master_subs_id)
INNER JOIN subs_clnt as sc1 ON (sc1.subs_subs_id = s.subs_id AND sc1.master_subs_id IS NULL)
INNER JOIN clients as c ON (c.clnt_id = sc1.clnt_clnt_id)
WHERE sc.clnt_clnt_id = '$id' AND sc.end_date IS NULL"))) {echo 'ERROR1111!!!!';die;}
   echo "Emloyees: \n";
   while($emp = mysql_fetch_assoc($res)) {
    echo $emp["clnt_name"]."\n";
   }
} else if ($cmd == "ratinglog") {
    time_form_rating_transactions($id);
} else
    die;
?>
