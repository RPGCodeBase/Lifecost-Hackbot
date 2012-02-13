<?php
$name = $_GET["name"];
$n = intval($_GET["n"]);
if ($n == 0) {
    die;
    }
include ("db_inc_moriarty.php");
make_link();
$name = strstr($name,'@',true);
$tags = false;
$query = "SELECT GROUP_CONCAT(t.teg_name) as tags
FROM subscribers as s
INNER JOIN subs_clnt as sc ON (sc.subs_subs_id = s.subs_id)
INNER JOIN clients as c ON (c.clnt_id = sc.clnt_clnt_id)
LEFT JOIN tegs_clnt  as tc ON (c.clnt_id = tc.clnt_id)
LEFT JOIN tegs as t ON (t.teg_id = tc.teg_id AND t.public)
WHERE s.login = '" . mysql_real_escape_string($name) . "' AND not c.is_company GROUP BY c.clnt_id";
if ($res = make_query($query)) {
        $hacker = mysql_fetch_assoc($res);

        if ($hacker == false) {
            echo $name." has no tags";
            die;
        }
        if ($hacker['tags'] == '') {
            echo $name." has no tags";
            die;
        }
        if (strstr($hacker['tags'],'virtual')===false)
            $tags = explode(',',$hacker['tags']);
}
if ($tags === false) {
    $query = "SELECT GROUP_CONCAT(t.teg_name) as tags
    FROM subscribers as sf
    INNER JOIN hacker_link as hl ON (hl.fake_subs_id = sf.subs_id)
    INNER JOIN subscribers as s ON (hl.real_subs_id = s.subs_id)
    INNER JOIN subs_clnt as sc ON (sc.subs_subs_id = s.subs_id)
    INNER JOIN clients as c ON (c.clnt_id = sc.clnt_clnt_id)
    LEFT JOIN tegs_clnt  as tc ON (c.clnt_id = tc.clnt_id)
    LEFT JOIN tegs as t ON (t.teg_id = tc.teg_id AND t.public)
    WHERE sf.login = '" . mysql_real_escape_string($name) . "' AND not c.is_company GROUP BY c.clnt_id";
    if ($res = make_query($query)){
        $hacker = mysql_fetch_assoc($res);
        if ($hacker == false) {
            echo $name." has no tags";
            die;
        }
        if ($hacker['tags'] == '') {
            echo $name." has no tags";
            die;
        }
        $tags = explode(',',$hacker['tags']);
    }
}
echo $name." has tags: ";
for ($i = 0; $i < $n && count($tags); $i++) {
    $j = rand(0,count($tags)-1);
    $tag = $tags[$j];
    unset($tags[$j]);
    $tags = array_values($tags);
    echo "#$tag ";
}
/*
$bonus = 100;
if ($target != "government"){
    if ($res = make_query("SELECT teg_name FROM clients LEFT JOIN tegs_clnt USING(clnt_id) INNER JOIN tegs USING (teg_id) WHERE clnt_name = '" . mysql_real_escape_string($target) . "'")){
        while ($tagRow = mysql_fetch_array($res)){
            $tag = $tagRow[0];
            if ($tag == "foreign" || $tag == "master" || $tag == "supermaster" || $tag == "bank"){
                echo "$target hacked by $hackers - unauthorized";
                die;
            }
            $bonuses = array("celebrity" => 200, "organisation" => 300, "business" => 300, "transnational" => 600, "party" => 600, "lifecost" => 1200);
            $newbonus = $bonuses[$tag];
            if ($newbonus > $bonus)
                $bonus = $newbonus;
        }
    }
} else
    $bonus = 1200;

$hackers = explode(",", $hackers);
foreach (array_values($hackers) as $hacker){
    //копипаста из upd_rating.inc, убейте меня за это
    $hacker_id = fetch_value("SELECT subs_id FROM subscribers WHERE login = '" . mysql_real_escape_string($hacker) . "'");
    $hacker_id = 5; //XXX
    if (make_query("update clients set rating = rating + ($bonus) where clnt_id = $hacker_id")
    && make_query("insert into rating_transactions (tran_date, clnt_src, clnt_dst, amount, comment) values (UNIX_TIMESTAMP(now()), -1, $hacker_id, $bonus, 'Хак')")){
        echo "$hacker ($hacker_id): +$bonus\n";
    } else{
        echo mysql_error();
        die;
    }
}*/
?>


