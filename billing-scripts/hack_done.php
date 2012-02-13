<?php
$tgt = $_GET["target"];
$hackers = $_GET["hackers"];
include ("db_inc_moriarty.php");
make_link();
$bonus = 100;
$query = "SELECT c.clnt_id as id, LOWER(c.clnt_name) as name, GROUP_CONCAT(t.teg_name) as tags,GROUP_CONCAT(t.groups) as groups, c.is_company FROM clients as c
LEFT JOIN tegs_clnt  as tc ON (c.clnt_id = tc.clnt_id)
LEFT JOIN tegs as t ON (t.teg_id = tc.teg_id)
WHERE REPLACE(LOWER(clnt_name),' ','_') = '".mysql_real_escape_string($tgt)."' GROUP BY c.clnt_id";
if ($res = make_query($query)){
    $target = mysql_fetch_assoc($res);
    if ($target === false) {
        echo "$tgt hacked by $hackers - unauthorized";
        die;
    }
    $tags = explode(',',$target['tags']);
    $groups = explode(',',$target['groups']);
    $id = $target['id'];
    if (array_search('мастер',$groups) !== false || array_search('bank',$tags) !== false || array_search('foreign',$tags) !== false) {
        echo "$tgt hacked by $hackers - unauthorized";
        die;
    }

    if ($id == 998 || $id == 958)
        $bonus = 1200;
    else if (array_search('transnational',$tags) !== false || array_search('party',$tags) !== false )
        $bonus = 600;
    else if ($target['is_company'])
        $bonus = 300;
    else if (array_search('celebrity',$tags) !== false)
        $bonus = 200;
}
$hackers = explode(",", $hackers);
foreach (array_values($hackers) as $hacker){
    $hacker_id = fetch_value("SELECT c.clnt_id FROM subscribers as s
INNER JOIN subs_clnt as sc ON (sc.subs_subs_id = s.subs_id)
INNER JOIN clients as c ON (c.clnt_id = sc.clnt_clnt_id)
WHERE s.login = '" . mysql_real_escape_string($hacker) . "' LIMIT 1");
    if (!($res = make_query("SELECT COUNT(*) from hack_log WHERE $hacker_id = hacker_id AND target = '".mysql_real_escape_string($tgt)."'"))) die;
    $n = mysql_result($res,0);
    $bonus >>= $n;
    if ($bonus) {
//        if (make_query("update clients set rating = rating + ($bonus) where clnt_id = $hacker_id")
//        && make_query("insert into rating_transactions (tran_date, clnt_src, clnt_dst, amount, comment) values (UNIX_TIMESTAMP(now()), -1, $hacker_id, $bonus, 'Хак')")
//        && make_query("insert into hack_log (completed, hacker_id, target) values (now(), $hacker_id, '".mysql_real_escape_string($tgt)."')")){
            echo "$hacker ($hacker_id): +$bonus\n";
//        } else{
//            echo 'ERRROR!!!!!!1';
//            die;
//        }
    }
}
?>
