"""Shared tokenizer and deliberately small, inspectable search vocabulary."""
import re
STOP='и в во на с со по а но или не ни это этот эта эти тот та те как что то я ты он она мы вы они у к ко от до за из без для про при о об обо же ли бы ну вот уже ещё еще очень просто хомяк хомяка хомячок белый рисунок персонаж вариант кадр the a an and or of in on with to is it this that hamster'.split()
SUFFIXES=sorted('иями ями ами иями иями иями ого ему ому его ими ыми иях ах ях ия ие ий ый ой ая яя ое ее ые ие ов ев ам ям ом ем ют ут ат ят ить еть ать ешь ете ешь ёшь ешь ют ся сь ть ет ит ют а я у ю ы и е о ing ers ies ed es s'.split(),key=len,reverse=True)
def normalize(text): return str(text).lower().replace('ё','е')
def stem(t):
 for x in SUFFIXES:
  if len(t)-len(x)>=3 and t.endswith(x):return t[:-len(x)]
 return t
def tokens(text):return [stem(t) for t in re.findall(r'[a-zа-я0-9]+',normalize(text)) if t not in STOP and len(t)>1]
# id | label | kind | RU/EN synonyms / phrases; exact groups are not model predictions.
RAW='''writing|Записывает|action|пишет;писать;записываю;записывает;запишу;записать;запиши;записывай;конспект;блокнот;тетрадь;ручка;документирую;фиксирую;notes;notebook;writing;pen;record
inspection|Рассматривает|action|лупа;проверяет;расследует;рассматривает;детектив;подвох;magnifying;inspect;detective;investigation
oxygen|Кислородная маска|object|кислород;кислородная;дышать;дыхание;задыхаюсь;воздух;oxygen;breathing
sleep|Сон|action|спит;спать;сон;сонный;дремота;пижама;sleep;sleeping;zzz;pajamas
exhausted|Усталость|mood|устал;усталость;усталый;уставший;выгоревший;выгорела;выгорел;не вывожу;изнеможение;изможденный;истощение;выжат;выгорел;выгорание;exhausted;tired;burnout
sad|Печаль|mood|грустно;грустный;печаль;печальный;огорчение;обида;расстройство;разочарование;sad;sadness;disappointed
cry|Плач|action|плачет;плакать;плач;рыдает;рыдание;слезы;слеза;cry;crying;tears;sobbing
angry|Злость|mood|злится;злой;злость;ярость;гнев;возмущение;раздражение;бесит;angry;rage;furious
joy|Радость|mood|радость;радуется;радостный;счастье;счастливый;веселье;восторг;joy;happy;delight
smile|Улыбка|action|улыбка;улыбается;улыбаюсь;улыбнулся;smile;smiling;grin
laugh|Смех|action|смеется;смех;смешно;смешок;хихикаю;laugh;laughing;chuckle
shock|Шок|mood|удивление;удивился;удивлен;удивленный;офигел;охуел;wtf;шок;ошеломление;ошарашен;испуг;паника;ужас;surprise;shock;panic;scared
love|Нежность|mood|любовь;люблю;нежность;влюбленность;обожаю;умиление;романтика;love;affection;adoration
shy|Смущение|mood|смущение;стесняюсь;стыдно;румянец;робкий;застенчивый;shy;blush;blushing;flustered
skeptical|Скепсис|mood|скепсис;сомнение;подозрение;недоверие;осуждение;осуждает;осуждающий;осуждаю;подозрительно;скептический;judgmental;judgment;skeptical;suspicious;unimpressed
smug|Самодовольство|mood|самодовольство;самодовольный;ехидство;ухмылка;ехидный;smug;smirk;gloating
confused|Недоумение|mood|недоумение;непонимание;растерянность;растерялся;озадаченность;confused;confusion;puzzled
thinking|Раздумье|mood|думает;думать;раздумье;задумчивость;сосредоточенность;план;гипотеза;thinking;contemplation;scheming
calm|Спокойствие|mood|спокойствие;спокойный;расслабленность;расслаблен;умиротворение;безмятежный;calm;relaxed;peaceful
food|Еда|topic|еда;ест;есть;обед;голод;аппетит;сытый;жую;лакомство;food;eating;hungry;meal
pizza|Пицца|object|пицца;пепперони;сыр;pizza;pepperoni;cheese
popcorn|Попкорн|object|попкорн;popcorn
burger|Бургер|object|бургер;burger
fruit|Фрукты|topic|фрукты;фрукт;ягода;арбуз;манго;лимон;банан;виноград;груша;персик;апельсин;клубника;вишня;ананас;лайм;fruit;watermelon;lemon;banana;grapes;pear;mango;peach;strawberry;cherry;pineapple;lime
music|Музыка|topic|музыка;музыкант;концерт;гитара;саксофон;наушники;плеер;певица;music;guitar;saxophone;headphones;earbuds
glasses|Очки|object|очки;оправа;очках;glasses;spectacles;goggles
brow|Бровь|object|бровь;брови;eyebrow;brow
tongue|Язык|object|язык;язычок;tongue
teeth|Зубы|object|зубы;зубастый;резцы;оскал;teeth;toothy;incisors
drool|Слюна|object|слюна;слюни;слюной;drool;drooling
thumbsup|Лайк|action|лайк;одобряю;одобрение;поддерживаю;зачет;thumbs up;approved
thumbsdown|Отказ|action|отказ;браковка;неодобрение;thumbs down;disapprove
heart|Сердце|object|сердце;сердца;сердечко;heart;hearts
kiss|Поцелуй|action|поцелуй;целую;поцеловаться;целуется;kiss;kissing
hug|Объятие|action|объятие;обнимает;обнимаю;прижались;прижимает;обнимание;hug;cuddling
baby|Малыш|object|малыш;маленькая копия;ребенок;миниатюра;baby;mini-me;miniature
shower|Душ|action|душ;моется;мыться;купается;мыло;пена;shower;soap;bubbles
flower|Цветы|object|цветы;цветок;букет;цветочек;flower;flowers;bouquet
gift|Подарок|topic|подарок;поздравляю;поздравление;гостинец;gift;congratulations
party|Праздник|topic|праздник;праздничный;колпак;конфетти;торт;party;celebration;confetti;birthday
christmas|Новый год|topic|рождество;новогодний;елка;санта;гирлянда;снеговик;2025;2026;Christmas;Santa;New Year
halloween|Хэллоуин|topic|хэллоуин;тыква;привидение;вампир;зомби;скелет;Halloween;pumpkin;ghost;vampire;zombie
cold|Холод|topic|холод;замерз;замерзает;мороз;снег;сосульки;cold;freezing;snow
hot|Жара|topic|жара;жарко;перегрев;плавится;плавлюсь;солнце;heat;hot;melting;sun
magic|Магия|topic|магия;магический;волшебник;фокусник;колдунья;ведьма;палочка;wizard;magic;witch;magician
money|Деньги|topic|деньги;доллары;богатство;прибыль;жадность;money;dollars;rich
phone|Телефон|object|телефон;переписка;чат;phone;Discord;chat
book|Учёба|topic|учеба;конспект;тетрадь;блокнот;ученик;студент;выпускник;диплом;study;school;graduation;notebook
brain|Мозг|object|мозг;извилины;интеллект;гениально;brain;genius
cube|Головоломка|object|кубик;рубика;головоломка;puzzle;Rubik;cube
scissors|Ножницы|object|ножницы;стрижка;стричь;scissors;haircut
pirate|Пират|topic|пират;треуголка;абордаж;YARG;pirate
devil|Чёртик|topic|чертик;черт;рожки;вилы;трезубец;devil;pitchfork
angel|Ангел|topic|ангел;нимб;невинность;angel;halo
cat|Кошачьи гости|topic|кот;котенок;кошка;кошачий;кошачьи;cat;kitten
alien|Пришелец|topic|инопланетянин;пришелец;антенны;инопланетный;alien;antennae
profile|Профиль|composition|профиль;боком;profile;side view
letterbox|Чёрные поля|composition|вертикальный;черные полосы;черные поля;letterbox;letterboxed
pixel|Пиксели|composition|пиксельный;пикселизация;pixel;pixelated
lowres|Маленький исходник|quality|маленький исходник;низкое разрешение;low resolution;tiny source
shadow|Тень|composition|тень;полутень;черная штриховка;shadow;scribble
bow|Бант|object|бант;бантик;bow
hat|Шляпа|object|шляпа;цилиндр;берет;каска;hat;helmet;beret
candle|Свеча|object|свеча;подсвечник;candle
leaving|Уходит|action|уходит;уход;прощание;узелок;изгнание;leaving;bindle
stop|Стоп|action|стоп;ладонь;подожди;остановка;stop;palm
shush|Тишина|action|тсс;тишина;секрет;тихо;shush;silence
smoking|Курение|action|курит;сигарета;курение;перекур;smoking;cigarette
weapon|Оружие|object|оружие;пистолет;дубинка;меч;gun;weapon;sword
hospital|Болезнь|topic|болеет;болезнь;болею;температура;градусник;кислородная;маска;hospital;fever;thermometer'''
CONCEPTS=[dict(zip(['id','label','kind','synonyms'],s.split('|'))) for s in RAW.splitlines()]
for c in CONCEPTS:c['synonyms']=c['synonyms'].split(';')
CONFIG={'stopwords':STOP,'suffixes':SUFFIXES,'concepts':CONCEPTS,'version':'1.0.0'}
def concept_ids(text):
 t=set(tokens(text));out=[]
 for c in CONCEPTS:
  if any((st:=set(tokens(s))) and st.issubset(t) for s in c['synonyms']):out.append(c['id'])
 return out
def expanded_tokens(text):
 ts=tokens(text)
 # Synthetic concept markers provide inspectable bilingual bridges.
 return ts+['concept_'+c for c in concept_ids(text)]*2
