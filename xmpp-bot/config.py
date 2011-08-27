# -*- coding: utf-8 -*-

#это базовые настройки для level = 0, меняются в зависимости от уровня хакера/система
#offenderVitality = 1
#defenderVitality = 50
hackerVitality = {
    1: 30,
    2: 60,
    3: 100
}
systemVitality = {
    0: 240,
    1: 500,
    2: 800,
    3: 1200
}
offenderDamage = 10 # *2^level
questionTime = 10
codeLength = 6

#количество хитов, снимаемое с нападающих, всегда одинаковое
defenderDamage = 5

#эталонное время для системы уровня 0, по которому определяется награда за ее взлом.
#диапазон делится на 2 части, если систему взломали за 30 секунд - самая большая награда, за 60 секунд - поменьше, больше 60 секунд - самая маленькая
defendSystemTime = 120

#базовое количество секунд, которое выдается на маленький взлом
rewardBaseScore = 10
#время в секундах, затрачиваемое на выполнение команд
rewardCommandTimeout = {
    "showmoney": 1,
    "smallmoney": 3,
    "healthget": 4,  
    "lasttransactions": 5,
    "votes": 10,
    "hacklog": 12,
    "alltransactions": 20,
    "healthadd": 25,
    "bigmoney": 35,
    "deface": 30,
    "clearlogs": 20,
    "emplinfo":15,
    "ratinglog":16
}                                                              

#константы
statCommandCooldown = 10
directAttackCooldown = 10
directAttackTime = 10
directAttackDamageOffender = 10
directAttackDamageDefender = 25
systemAttack = {
    0: 10,
    1: 15,
    2: 25,
    3: 50
}
questionFactor = {
    0: 1,
    1: 1.2,
    2: 1.5,
    3: 2
}
subscriptionsCount = {
    1: 5,
    2: 10,
    3: 20
}
channelsCount = {
    1: 2,
    2: 6,
    3: 8
}

#тайминг вопросов
nextQuestionMaxTimeout = 5
questionTime = { # по уровню системы
    0: 20,
    1: 15,
    2: 10,
    3: 6
}

#тоже константы - сколько хитов снимается в разных случаях:
cooldownOnKilled = 60  # убили канале
cooldownOnExit = 20    # вышел из канала
cooldownSystemAttack = { # сколько секунд в систему нельзя входить хакерам
    0: 300,
    1: 600,
    2: 1800,
    3: 3600
}
cooldownRestore = 5 # раз в столько секунд восстанавливается хит

nightSleepHour = 3
morningStartHour = 9

#а это уже настройки
conference = "conference.lifecost.tv"
server = "lifecost.tv"
nickname = "System"
mainChannel = "hackers"
baseUrl = "http://billing.lifecost.tv/hack/"
fromEmail = 'hackbot@lifecost.tv'
policeEmail = 'police-hack@lifecost.tv'
mailHost = 'mail.lifecost.tv'
mailPort = 25
