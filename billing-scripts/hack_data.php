<?php
include("db_inc_moriarty.php");
make_link();
mb_internal_encoding('UTF-8');
$common_queries = array();
$targets = array();
$hackers = array();
$rewards_all = array("showmoney","smallmoney","healthget","lasttransactions","votes","hacklog","alltransactions","healthadd","bigmoney","deface","clearlogs","emplinfo","ratinglog");
$rewards_dead = array("healthget","lasttransactions","votes","hacklog","alltransactions","clearlogs");
$rewards_human = array("showmoney","smallmoney","healthget","lasttransactions","votes","hacklog","alltransactions","healthadd","bigmoney","deface","clearlogs","ratinglog");
$rewards_org = array("showmoney","smallmoney","lasttransactions","votes","hacklog","alltransactions","bigmoney","clearlogs","emplinfo","ratinglog");
$words = array_values(preg_grep('/^[a-z]+$/',explode("\n",file_get_contents('italian'))));
$wordslen = count($words);
function create_phrase($n) {
    global $words, $wordslen;
    $w = array();
    for ($i=0;$i<$n;$i++)
        array_push($w,$words[rand(0,$wordslen)]);
    return implode(' ',$w);
}
for ($i=0;$i<5;$i++) {
    $phrase = create_phrase(4);
    $text = "'$phrase' Набрать все гласные в прямом порядке.";
    $answer = str_replace(' ','',strtr($phrase,'bcdfghjklmnpqrstvwxz','                    '));
    $level = 0;
    array_push($common_queries,array('text'=>$text,'answer'=>$answer,'level'=>$level));
}
for ($i=0;$i<5;$i++) {
    $phrase = create_phrase(4);
    $text = "'$phrase' Набрать все гласные в обратном порядке.";
    $answer = strrev(str_replace(' ','',strtr($phrase,'bcdfghjklmnpqrstvwxz','                    ')));
    $level = 0;
    array_push($common_queries,array('text'=>$text,'answer'=>$answer,'level'=>$level));
}
/*for ($i=0;$i<10;$i++) {
    $answer = create_phrase(2);
    $phrase = strtr($answer,'qwertyuiop[]asdfghjkl;zxcvbnm,./','йцукенгшщзхъфывапролджячсмитьбю.');
    $text = "'$phrase' текст был набран не в той раскладке, набрать правильно.";
    $level = 1;
    print_r(array('text'=>$text,'answer'=>$answer,'level'=>$level));
    array_push($common_queries,array('text'=>$text,'answer'=>$answer,'level'=>$level));
}*/
$digits=array('нулей','единиц','двоек','троек','четверок','пятерок','шестерок','семерок','восьмерок','девяток');
$nondigints = array('1' => 1,'2' => 2,'3' => 3,'4' => 4,'5' => 5,'6' => 6,'7' => 7,'8' => 8,'9' => 9,'0' => 0, 'O'=>0, 'О'=>0, 'l'=>1, 'З'=>3, ' '=>null,'один' => 1,'два' => 2,'три' => 3,'четыре' => 4,'пять' => 5,'шесть' => 6,'семь' => 7,'восемь' => 8,'девять' => 9,'ноль' => 0);
for ($i=0;$i<11;$i++) {
    $phrase='';
    $answer = 0;
    $di = rand(0,9);
    $digit = $digits[$di];
    for ($k=0;$k<3;$k++){
        for ($j=0;$j<20;$j++) {
            $d=array_rand($nondigints);
            $phrase.=$d;
            if ($nondigints[$d] == $di)
                $answer++;
        }
        $phrase.="\n";
    }
    $text = "$phrase\nсколько здесь \"".$digit."\".";
    $level = 1;
    array_push($common_queries,array('text'=>$text,'answer'=>strval($answer),'level'=>$level));
}

$ltext = file_get_contents('text');
$alpabet = mb_split('/','й/ц/у/к/е/н/г/ш/щ/з/х/ъ/ф/ы/в/а/п/р/о/л/д/ж/э/я/ч/с/м/и/т/ь/б/ю');
$max_textlen = 50;
$min_textlen = 40;
for ($i=0;$i<11;$i++) {
    $start = rand(0,mb_strlen($ltext)-$max_textlen);
    $len = rand($min_textlen,$max_textlen);
    $end =  mb_strpos($ltext,' ',$start+$len);
    $start = mb_strpos($ltext,' ',$start)+1;
    $len = $end-$start;
    $phrase = mb_convert_case(mb_ereg_replace(" ^",'',mb_ereg_replace("$ ",'',mb_ereg_replace(" +",' ',mb_ereg_replace("([^а-яА-Я])",' ',mb_substr($ltext,$start,$len),"p")))),MB_CASE_LOWER);
    $answer = $phrase;
    $num = rand(5,7);
    for ($k=0;$k<$num;$k++) {
        $l = $alpabet[array_rand($alpabet)];
        $pos = rand(0,mb_strlen($phrase));
        $phrase = mb_substr($phrase,0,$pos).$l.mb_substr($phrase,$pos,$len+$k-$pos);
    }
    
    $text = "'$phrase'\n исправьте фразу";
    $level = 1;
    array_push($common_queries,array('text'=>$text,'answer'=>$answer,'level'=>$level));
}

if ($res = make_query("SELECT s.login, s.barcode, c.clnt_id as id, LOWER(c.clnt_name) as name, GROUP_CONCAT(t.teg_name) as tags,GROUP_CONCAT(t.groups) as groups, c.is_company FROM clients as c
LEFT JOIN tegs_clnt  as tc ON (c.clnt_id = tc.clnt_id)
LEFT JOIN tegs as t ON (t.teg_id = tc.teg_id)
LEFT JOIN subs_clnt as sc ON (sc.clnt_clnt_id = c.clnt_id)
LEFT JOIN subscribers as s ON (s.subs_id = sc.subs_subs_id AND sc.master_subs_id IS NULL)
GROUP BY c.clnt_id")){
    while ($target = mysql_fetch_assoc($res)){
        $pr_questions = array();
        $name = str_replace(' ','_',$target["name"]);
        $tags = explode(',',$target['tags']);
        $groups = explode(',',$target['groups']);
        $id = $target['id'];
        if (substr($name, 0,7) == 'account')
            continue;
        if (array_search('мастер',$groups) !== false)
            continue;
        if (array_search('bank',$tags) !== false)
            continue;
        if (array_search('dead',$tags) !== false)
            continue;                        
        if (array_search('foreign',$tags) !== false)
            continue;
        if ($target['is_company']) {
            if (array_search('dead',$tags) !== false)
                continue;
            $level = 1;
            if ($id == 998 || array_search('transnational',$tags))
                $level = 2;
            else if ($id == 958)
                $level = 3;
            $rewards = $rewards_org; //TODO determine deface
        } else {
            $level = 0;
            if (array_search('dead',$tags) !== false) {
                $rewards = $rewards_dead;
            } else {
                $rewards = $rewards_human;
            }
            //if ($target['login']) array_push($pr_questions,array('text'=>'логин абонента','answer'=>$target['login'],'level'=>0));
            for ($i=0;$i<3;$i++) {
                if ($target['barcode']) array_push($pr_questions,array('text'=>'номер счета абонента (13 цифр)','answer'=>$target['barcode'],'level'=>3));
            }
        }
        $tres = make_query("select amount FROM billing.money_transactions as mt WHERE mt.clnt_src = $id OR mt.clnt_dst = $id ORDER BY mt.tran_date DESC LIMIT 3");
        if ($tres) {
            $last = 'последней';
            while($tr = mysql_fetch_assoc($tres)) {
                array_push($pr_questions,array('text'=>"Сумма $last транзакции",'answer'=>strval($tr['amount']),'level'=>0));
                $last = 'пред'.$last;
            }
        }
        $targets[$name] = array("questions" => $pr_questions, "rewards" => $rewards, "level" => $level);
    }

    if ($res = make_query("SELECT c.clnt_id, s.login, RIGHT(teg_name,1) AS level
FROM clients c
INNER JOIN subs_clnt ON clnt_clnt_id=c.clnt_id AND master_subs_id IS NULL
INNER JOIN subscribers s ON s.subs_id = subs_subs_id
INNER JOIN tegs_clnt tc ON tc.clnt_id = c.clnt_id AND tc.end_date IS NULL 
INNER JOIN tegs t ON t.teg_id = tc.teg_id 
WHERE t.teg_name IN ('hacker1','hacker2','hacker3')")){
        while ($q = mysql_fetch_assoc($res)){
            $hackers[$q["login"]] = array("level" => $q["level"]);
        }
        $object = array("targets" => $targets, "hackers" => $hackers, "questions" => $common_queries);
//        print_r($object);
        echo json_encode($object);
    }
}
?>
