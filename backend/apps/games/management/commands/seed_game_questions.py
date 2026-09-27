"""Qo'lda yozilgan savollar bankini o'yinlar omboriga (PooledQuestion) joylaydi.

O'yinlar va duellar savollarni bitta `PooledQuestion` omboridan oladi, shuning
uchun bu command bankni qo'lda to'ldirish uchun yozilgan.

Sinf biriktirilmagan (`school_class=None`) savollar — bu fanning umumiy banki:
shu fanni o'qituvchi har bir sinf va har bir o'yin shundan o'z savolini oladi.
Shuning uchun default shu tarzda ishlaydi — bir marta yozilgan savol butun
fanning o'quvchilariga xizmat qiladi, o'z-o'zidan takrorlanmaydi va hech qanday
sinfga bog'lanmaydi. Maxsus sinf uchun savol kerak bo'lsa `--school-class`
beriladi va faqat o'sha sinfga qo'shiladi.

Ishlatish:
    python manage.py seed_game_questions                        # har bir fanning umumiy banki
    python manage.py seed_game_questions --subject Matematika
    python manage.py seed_game_questions --school-class "9-A"    # faqat 9-A uchun

Qayta ishga tushirsa ham xavfsiz (idempotent): bir xil matnli savol bitta
(sinf, fan) pool'iga takror joylanmaydi.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.academics.models import Subject
from apps.games.models import PooledQuestion
from apps.schools.models import SchoolClass

# Bank kalitlari fan nomining kichik harf varianti bilan taqqoslanadi.
# Agar fan nomi kalitni "o'z ichiga olsa" (masalan "Matematika-Demo"),
# o'sha bank ishlatiladi.
QUESTIONS_BANK: dict[str, list[dict]] = {
    "matematika": [
        {"text": "a² − b² ni ko'paytuvchilarga ajrating", "options": ["(a−b)(a+b)", "(a−b)²", "(a+b)²", "a−b"], "correct": 0},
        {"text": "30° li burchak qarshisidagi katet gipotenuzaning qaysi qismini tashkil qiladi?", "options": ["Yarmini", "Uchdan birini", "To'rtdan birini", "Ikkiga bo'linmaydi"], "correct": 0},
        {"text": "Kvadrat tenglama ax²+bx+c=0 ning diskriminanti qaysi formula bilan topiladi?", "options": ["D = b² − 4ac", "D = b² + 4ac", "D = 4ac − b²", "D = √(b²−4ac)"], "correct": 0},
        {"text": "π sonining taqribiy qiymati qanday?", "options": ["3,14", "2,71", "1,41", "1,73"], "correct": 0},
        {"text": "Radiusi r bo'lgan aylana uzunligi qanday hisoblanadi?", "options": ["C = 2πr", "C = πr", "C = πr²", "C = 4πr"], "correct": 0},
        {"text": "15% ni o'nli kasr ko'rinishida ifodalang", "options": ["0,15", "1,5", "15", "0,015"], "correct": 0},
        {"text": "x² = 49 tenglamaning ildizlari qaysilar?", "options": ["7 va −7", "Faqat 7", "Faqat −7", "49 va −49"], "correct": 0},
        {"text": "Arifmetik progressiyaning n-hadi qaysi formula bilan topiladi?", "options": ["aₙ = a₁ + (n−1)d", "aₙ = a₁ · dⁿ", "aₙ = a₁ + nd", "aₙ = a₁ − (n−1)d"], "correct": 0},
        {"text": "To'g'ri to'rtburchakning yuzasi qanday topiladi?", "options": ["S = a·b", "S = 2(a+b)", "S = a : b", "S = (a+b)/2"], "correct": 0},
        {"text": "0,5 sonni foizda ifodalang", "options": ["50%", "5%", "0,5%", "500%"], "correct": 0},
        {"text": "Kvadratning diagonallari kesishish nuqtasida qanday bo'linadi?", "options": ["Teng ikkiga", "Teng uchga", "To'rtga", "Bo'linmaydi"], "correct": 0},
        {"text": "2³ + 3² ni hisoblang", "options": ["17", "13", "29", "15"], "correct": 0},
        {"text": "12 va 18 sonlarining eng katta umumiy bo'luvchisini toping", "options": ["6", "3", "12", "36"], "correct": 0},
        {"text": "4 va 6 sonlarining eng kichik umumiy karralisini toping", "options": ["12", "24", "8", "6"], "correct": 0},
        {"text": "Uchburchak ichki burchaklarining yig'indisi necha gradus?", "options": ["180°", "90°", "360°", "270°"], "correct": 0},
        {"text": "(−3)² ni hisoblang", "options": ["9", "−9", "6", "−6"], "correct": 0},
        {"text": "25% ni oddiy kasr ko'rinishida ifodalang", "options": ["1/4", "1/3", "1/5", "1/2"], "correct": 0},
        {"text": "y = kx funksiyaning grafigi qanday nomlanadi?", "options": ["To'g'ri proportsionallik", "Parabola", "Giperbola", "Sinusoida"], "correct": 0},
        {"text": "7/100 ni o'nli kasr ko'rinishida yozing", "options": ["0,07", "0,7", "7,0", "0,007"], "correct": 0},
        {"text": "Pifagor teoremasi qaysi figuraga taalluqli?", "options": ["To'g'ri burchakli uchburchak", "Teng yonli uchburchak", "Kvadrat", "Romb"], "correct": 0},
    ],
    "fizika": [
        {"text": "Tezlik qaysi formula bilan topiladi?", "options": ["v = S/t", "v = S·t", "v = t/S", "v = m·t"], "correct": 0},
        {"text": "Jismga ta'sir qiluvchi og'irlik kuchi formulasi qaysi?", "options": ["F = mg", "F = ma", "F = m/g", "F = m·V"], "correct": 0},
        {"text": "Elektr tok kuchining o'lchov birligi qaysi?", "options": ["Amper", "Volt", "Om", "Vatt"], "correct": 0},
        {"text": "Kuchning o'lchov birligi nima?", "options": ["Nyuton", "Paskal", "Joul", "Metr"], "correct": 0},
        {"text": "Mexanik ish qaysi formula bilan hisoblanadi?", "options": ["A = F·S", "A = F/S", "A = P·S", "A = m·g"], "correct": 0},
        {"text": "Jismning zichligi qaysi formula bilan topiladi?", "options": ["ρ = m/V", "ρ = m·V", "ρ = V/m", "ρ = m + g"], "correct": 0},
        {"text": "Ovoz vakuumda tarqaladimi?", "options": ["Yo'q", "Ha", "Faqat baland ovoz", "Faqat past ovoz"], "correct": 0},
        {"text": "Bosimning o'lchov birligi qaysi?", "options": ["Paskal", "Nyuton", "Joul", "Gramm"], "correct": 0},
        {"text": "Yer sirtida erkin tushish tezlanishi (g) taxminan qancha?", "options": ["9,8 m/s²", "8,9 m/s²", "10,8 m/s²", "9,0 m/s²"], "correct": 0},
        {"text": "Elektr qarshilikning o'lchov birligi qaysi?", "options": ["Om", "Volt", "Amper", "Vatt"], "correct": 0},
        {"text": "Ishqalanish kuchi qaysi tomonga yo'nalgan bo'ladi?", "options": ["Harakatga qarshi", "Harakat yo'nalishida", "Doimo yuqoriga", "Doimo pastga"], "correct": 0},
        {"text": "Kuchni o'lchaydigan asbob qanday nomlanadi?", "options": ["Dinamometr", "Termometr", "Manometr", "Ampermetr"], "correct": 0},
        {"text": "Muzning erish harorati qancha?", "options": ["0°C", "−10°C", "100°C", "10°C"], "correct": 0},
        {"text": "Yorug'likning vakuumdagi tezligi taxminan qancha?", "options": ["300 000 km/s", "150 000 km/s", "3 000 km/s", "30 000 km/s"], "correct": 0},
        {"text": "Jismning inertlik xossasi qaysi kattalik bilan xarakterlanadi?", "options": ["Massa", "Og'irlik", "Hajm", "Tezlik"], "correct": 0},
        {"text": "Metall o'tkazgichning qarshiligi harorat oshishi bilan qanday o'zgaradi?", "options": ["Ortadi", "Kamayadi", "O'zgarmaydi", "Nolga teng bo'ladi"], "correct": 0},
        {"text": "Qaynash jarayonida suyuqlikda nima sodir bo'ladi?", "options": ["Suv bug'iga aylanadi", "Muzga aylanadi", "Sovuqlashadi", "Hech narsa o'zgarmaydi"], "correct": 0},
        {"text": "Atom yadrosidagi musbat zarracha qaysi?", "options": ["Proton", "Elektron", "Neytron", "Ion"], "correct": 0},
    ],
    "kimyo": [
        {"text": "Suvning kimyoviy formulasi qaysi?", "options": ["H₂O", "CO₂", "O₂", "H₂O₂"], "correct": 0},
        {"text": "Havodagi kislorodning hajm ulushi taxminan qancha?", "options": ["21%", "78%", "50%", "1%"], "correct": 0},
        {"text": "Eng yengil gaz qaysi?", "options": ["Vodorod", "Kislorod", "Azot", "Karbonat angidrid"], "correct": 0},
        {"text": "Kimyoviy elementlar davriy sistemasi muallifi kim?", "options": ["D.I. Mendeleyev", "A. Avogadro", "J. Dalton", "L. Paster"], "correct": 0},
        {"text": "Osh tuzining kimyoviy formulasi qaysi?", "options": ["NaCl", "NaClO", "KCl", "CaCl₂"], "correct": 0},
        {"text": "Atom yadrosidagi neytral zarracha qaysi?", "options": ["Neytron", "Proton", "Elektron", "Pozitron"], "correct": 0},
        {"text": "Kislotalar eritmasining pH qiymati qanday bo'ladi?", "options": ["pH < 7", "pH = 7", "pH > 7", "pH = 14"], "correct": 0},
        {"text": "Kislorodning molekulyar formulasi qaysi?", "options": ["O₂", "O", "O₃", "O₂⁻"], "correct": 0},
        {"text": "Na₂CO₃ qanday modda?", "options": ["Soda", "Osh tuzi", "Kislota", "Asos (ishqor)"], "correct": 0},
        {"text": "Qaysi birikma asos (ishqor) hisoblanadi?", "options": ["NaOH", "HCl", "CO₂", "SO₂"], "correct": 0},
        {"text": "Suvning elektrolizida katodda qaysi gaz ajraladi?", "options": ["Vodorod", "Kislorod", "Azot", "Xlor"], "correct": 0},
        {"text": "Kimyoviy reaksiya natijasida nima hosil bo'ladi?", "options": ["Yangi moddalar", "Faqat issiqlik", "Faqat yorug'lik", "Hech narsa"], "correct": 0},
        {"text": "Davriy sistemada qaysi element tartib raqami 20 ga teng?", "options": ["Kaltsiy", "Natriy", "Temir", "Mis"], "correct": 0},
        {"text": "Quyidagilardan qaysi biri metall hisoblanmaydi?", "options": ["Oltingugurt", "Mis", "Temir", "Alyuminiy"], "correct": 0},
        {"text": "CO₂ — bu qanday modda?", "options": ["Uglerod (IV) oksidi", "Uglerod (II) oksidi", "Karbonat kislota", "Metan"], "correct": 0},
        {"text": "Davriy sistemada elementning tartib raqami nimani ko'rsatadi?", "options": ["Yadrodagi protonlar sonini", "Neytronlar sonini", "Molekuladagi atomlar sonini", "Elektron qavatlar sonini"], "correct": 0},
    ],
    "biologiya": [
        {"text": "Fotosintez jarayoni o'simlikning qaysi organoidida kechadi?", "options": ["Xloroplast", "Mitoxondriya", "Yadro", "Vakuola"], "correct": 0},
        {"text": "Inson yuragi necha kameradan iborat?", "options": ["4", "2", "3", "5"], "correct": 0},
        {"text": "Qaysi organ qonni kislorod bilan boyitadi?", "options": ["O'pka", "Jigar", "Buyrak", "Oshqozon"], "correct": 0},
        {"text": "Eritrotsitlar asosan qanday moddani tashiydi?", "options": ["Kislorod", "Vodorod", "Azot", "Uglerod (II) oksidi"], "correct": 0},
        {"text": "Hujayraning genetik axboroti qayerda saqlanadi?", "options": ["Yadro", "Sitoplazma", "Membrana", "Ribosoma"], "correct": 0},
        {"text": "Mitoxondriyalarning asosiy vazifasi nima?", "options": ["Energiya ishlab chiqarish", "Oqsil sintezi", "Suv saqlash", "Bo'yalish"], "correct": 0},
        {"text": "O'simlik hujayra devori asosan qaysi moddadan iborat?", "options": ["Tsellyuloza", "Oqsil", "Kraxmal", "Moy"], "correct": 0},
        {"text": "Qandli diabet qaysi organ funksiyasining buzilishi bilan bog'liq?", "options": ["Oshqozon osti bezi", "Jigar", "Buyrak usti bezi", "Qalqonsimon bez"], "correct": 0},
        {"text": "Inson skeletida taxminan nechta suyak bor?", "options": ["206", "150", "300", "365"], "correct": 0},
        {"text": "Gemoglobin tarkibida qaysi element bor?", "options": ["Temir", "Kalsiy", "Mis", "Kaliy"], "correct": 0},
        {"text": "Buyrakning struktura-funksional birligi qanday nomlanadi?", "options": ["Nefron", "Neyron", "Alveola", "Nefrit"], "correct": 0},
        {"text": "Odam organizmidagi eng katta organ qaysi?", "options": ["Teri", "Jigar", "Oshqozon", "Miya"], "correct": 0},
        {"text": "Qon plazmasining asosiy tarkibiy qismi nima?", "options": ["Suv", "Oqsil", "Temir", "Glyukoza"], "correct": 0},
        {"text": "Nerv hujayrasi qanday nomlanadi?", "options": ["Neyron", "Nefron", "Limfotsit", "Eritrotsit"], "correct": 0},
        {"text": "Ildiz o'simlikka qanday vazifani bajaradi?", "options": ["Suv va mineral moddalarni so'radi", "Fotosintez qiladi", "Mevani yetiltiradi", "Gullar chiqaradi"], "correct": 0},
        {"text": "Oqsillar qanday monomerlardan tuzilgan?", "options": ["Aminokislotalar", "Nukleotidlar", "Glyukoza", "Yog' kislotalari"], "correct": 0},
        {"text": "Hujayra bo'linishining asosiy usuli qaysi?", "options": ["Mitoz", "Meioz", "Fagotsitoz", "Gametogenez"], "correct": 0},
        {"text": "Vaksinaning asosiy vazifasi nima?", "options": ["Yuqumli kasalliklarga qarshi immunitet shakllantirish", "Kasalliklarni davolash", "Jarohatlarni bitirish", "Ovqat hazm qilish"], "correct": 0},
    ],
    "informatika": [
        {"text": "Kompyuterning asosiy hisoblash qurilmasi qaysi?", "options": ["Protsessor", "Monitor", "Sichqoncha", "Printer"], "correct": 0},
        {"text": "101₂ sonining o'nlik ko'rinishi qancha?", "options": ["5", "4", "6", "3"], "correct": 0},
        {"text": "1 KB necha baytdan iborat?", "options": ["1024", "1000", "512", "2048"], "correct": 0},
        {"text": "Axborotning eng kichik o'lchov birligi qaysi?", "options": ["Bit", "Bayt", "Kilobayt", "Megabayt"], "correct": 0},
        {"text": "1 bayt necha bitga teng?", "options": ["8", "16", "2", "4"], "correct": 0},
        {"text": "HTML nima uchun ishlatiladi?", "options": ["Veb-sahifalarni belgilash uchun", "Grafik chizish uchun", "Video montaj uchun", "O'yin o'ynash uchun"], "correct": 0},
        {"text": "Quyidagilardan qaysi biri operatsion tizim?", "options": ["Windows", "Photoshop", "Word", "Chrome"], "correct": 0},
        {"text": "Veb-sahifalarni ko'rish uchun qaysi dasturdan foydalaniladi?", "options": ["Brauzer", "Arxivator", "Kompilyator", "Defragmentator"], "correct": 0},
        {"text": "Elektron pochta manzilida qaysi belgi majburiy ishlatiladi?", "options": ["@", "#", "&", "$"], "correct": 0},
        {"text": "Algoritm nima?", "options": ["Masalani yechish bo'yicha aniq ketma-ketlik", "Dastur oynasi", "Qurilma drayveri", "Xotira hajmi"], "correct": 0},
        {"text": "Qaysi qurilma axborotni kiritish uchun xizmat qiladi?", "options": ["Klaviatura", "Printer", "Monitor", "Kolonka"], "correct": 0},
        {"text": "Rasm tarkibidagi eng kichik nuqta qanday ataladi?", "options": ["Piksel", "Bayt", "Klaster", "Graf"], "correct": 0},
        {"text": "Zararli dasturlardan himoya qiluvchi dastur qaysi?", "options": ["Antivirus", "Brauzer", "Arxivator", "Muharrir"], "correct": 0},
        {"text": "Ma'lumotlarni jadvallar ko'rinishida saqlaydigan tur qaysi?", "options": ["Ma'lumotlar bazasi", "Matn muharriri", "O'yin dasturi", "Operatsion tizim"], "correct": 0},
        {"text": "Fayl kengaytmasi .docx qaysi dasturga tegishli?", "options": ["Word", "Excel", "PowerPoint", "Access"], "correct": 0},
        {"text": "Internet orqali yuboriladigan keraksiz reklama xatlari qanday ataladi?", "options": ["Spam", "Virus", "Kuki", "Fayl"], "correct": 0},
        {"text": "Binar sanoq sistemasida qaysi raqamlar ishlatiladi?", "options": ["0 va 1", "0 dan 9 gacha", "1 va 2", "−1 va 1"], "correct": 0},
        {"text": "Veb-sahifaning manzili qanday ataladi?", "options": ["URL", "PDF", "CPU", "CD"], "correct": 0},
    ],
    "ona tili": [
        {"text": "O'zbek alifbosida nechta harf bor?", "options": ["29", "30", "31", "28"], "correct": 0},
        {"text": "'Kitob' so'zida nechta bo'g'in bor?", "options": ["2", "1", "3", "4"], "correct": 0},
        {"text": "Fe'l qanday savollarga javob beradi?", "options": ["Nima qildi?", "Kim? nima?", "Qanday?", "Qachon?"], "correct": 0},
        {"text": "'Qalam' so'zi qaysi so'z turkumiga mansub?", "options": ["Ot", "Fe'l", "Sifat", "Ravish"], "correct": 0},
        {"text": "Gapning bosh bo'laklari qaysilar?", "options": ["Ega va kesim", "To'ldiruvchi va aniqlovchi", "Hol va aniqlovchi", "Ega va to'ldiruvchi"], "correct": 0},
        {"text": "Ma'nodosh so'zlar qanday ataladi?", "options": ["Sinonim", "Antonim", "Omonim", "Paronim"], "correct": 0},
        {"text": "Qarama-qarshi ma'noli so'zlar qanday ataladi?", "options": ["Antonim", "Sinonim", "Omonim", "Dialektizm"], "correct": 0},
        {"text": "'O'quvchi' so'zining ildizi qaysi?", "options": ["o'qi", "vchi", "o'quv", "chi"], "correct": 0},
        {"text": "So'roq gap oxiriga qanday tinish belgisi qo'yiladi?", "options": ["?", "!", ".", ":"], "correct": 0},
        {"text": "'Dars' so'zi nechta harfdan iborat?", "options": ["4", "3", "5", "6"], "correct": 0},
        {"text": "Kelasi zamon fe'li qaysi?", "options": ["o'qiydi", "o'qidi", "o'qiyapti", "o'qigan"], "correct": 0},
        {"text": "O'zbek tilida nechta unli harf bor?", "options": ["6", "5", "7", "8"], "correct": 0},
        {"text": "'Katta' so'zining antonimi qaysi?", "options": ["Kichik", "Ulug'", "Go'zal", "Baland"], "correct": 0},
        {"text": "'Men maktabga boryapman' gapidagi kesim qaysi?", "options": ["boryapman", "men", "maktabga", "maktab"], "correct": 0},
        {"text": "Otlar necha kelishikda tuslanadi?", "options": ["6", "3", "5", "7"], "correct": 0},
        {"text": "Yozma nutqda gap qaysi harf bilan boshlanadi?", "options": ["Bosh harf", "Kichik harf", "Ixtiyoriy", "Raqam bilan"], "correct": 0},
    ],
    "ingliz tili": [
        {"text": "'Book' so'zining o'zbekcha ma'nosi qaysi?", "options": ["Kitob", "Daftar", "Maktab", "Qalam"], "correct": 0},
        {"text": "'Child' so'zining ko'plik shakli qaysi?", "options": ["Children", "Childs", "Childes", "Childsen"], "correct": 0},
        {"text": "'I ___ a student.' — bo'sh joyga nima qo'yiladi?", "options": ["am", "is", "are", "be"], "correct": 0},
        {"text": "'Go' fe'lining o'tgan zamon shakli qaysi?", "options": ["went", "goed", "gone", "going"], "correct": 0},
        {"text": "'Good' sifatining qiyosiy darajasi qaysi?", "options": ["better", "gooder", "more good", "best"], "correct": 0},
        {"text": "'Big' so'zining antonimi qaysi?", "options": ["small", "large", "huge", "tall"], "correct": 0},
        {"text": "'She ___ to school every day.' — bo'sh joyga nima qo'yiladi?", "options": ["goes", "go", "going", "went"], "correct": 0},
        {"text": "'Thank you' so'zining ma'nosi qaysi?", "options": ["Rahmat", "Salom", "Xayr", "Ha"], "correct": 0},
        {"text": "Haftaning birinchi kuni qaysi?", "options": ["Sunday", "Monday", "Saturday", "Friday"], "correct": 0},
        {"text": "'Red' rangining o'zbekcha ma'nosi qaysi?", "options": ["Qizil", "Ko'k", "Yashil", "Sariq"], "correct": 0},
        {"text": "'An' artikali qaysi so'z oldidan keladi?", "options": ["apple", "book", "car", "dog"], "correct": 0},
        {"text": "'I like ___ football.' — bo'sh joyga nima qo'yiladi?", "options": ["playing", "play", "played", "plays"], "correct": 0},
        {"text": "'Three' so'zining o'zbekcha ma'nosi qaysi?", "options": ["Uch", "To'rt", "Besh", "Olti"], "correct": 0},
        {"text": "'Where' so'roq so'zi qanday ma'noni beradi?", "options": ["Qayerda", "Qachon", "Nima", "Kim"], "correct": 0},
        {"text": "'Run' fe'lining o'tgan zamon shakli qaysi?", "options": ["ran", "runned", "runs", "running"], "correct": 0},
        {"text": "'Parents' so'zining ma'nosi qaysi?", "options": ["Ota-ona", "Do'stlar", "O'qituvchilar", "Qo'shnilar"], "correct": 0},
        {"text": "'Five plus three is ___.'", "options": ["eight", "seven", "nine", "six"], "correct": 0},
        {"text": "'Good morning' qachon aytiladi?", "options": ["Ertalab", "Kechqurun", "Tunda", "Tushda"], "correct": 0},
    ],
    "geografiya": [
        {"text": "Dunyodagi eng katta okean qaysi?", "options": ["Tinch okeani", "Atlantika okeani", "Hind okeani", "Shimoliy Muz okeani"], "correct": 0},
        {"text": "O'zbekiston poytaxti qaysi shahar?", "options": ["Toshkent", "Samarqand", "Buxoro", "Andijon"], "correct": 0},
        {"text": "Dunyodagi eng uzun daryo qaysi?", "options": ["Nil", "Amazonka", "Amudaryo", "Volga"], "correct": 0},
        {"text": "O'zbekistonning shimolida qaysi davlat joylashgan?", "options": ["Qozog'iston", "Qirg'iziston", "Turkmaniston", "Tojikiston"], "correct": 0},
        {"text": "Jahondagi eng baland cho'qqi qaysi?", "options": ["Everest (Jomolungma)", "Elbrus", "Xan Tengri", "Fudziyama"], "correct": 0},
        {"text": "Qizilqum cho'li asosan qaysi davlat hududida joylashgan?", "options": ["O'zbekiston", "Qozog'iston", "Rossiya", "Xitoy"], "correct": 0},
        {"text": "Amudaryo va Sirdaryo qaysi suv havzasiga quyiladi?", "options": ["Orol dengiziga", "Kaspiy dengiziga", "O'rta yer dengiziga", "Qora dengizga"], "correct": 0},
        {"text": "O'zbekistonning eng katta viloyati qaysi?", "options": ["Buxoro", "Namangan", "Qashqadaryo", "Xorazm"], "correct": 0},
        {"text": "Yer shari o'z o'qi atrofida qancha vaqtda bir marta aylanadi?", "options": ["24 soatda", "365 kunda", "12 soatda", "7 kunda"], "correct": 0},
        {"text": "O'zbekiston Respublikasida nechta viloyat bor?", "options": ["12", "9", "14", "10"], "correct": 0},
        {"text": "Dunyodagi eng katta qit'a qaysi?", "options": ["Osiyo", "Afrika", "Shimoliy Amerika", "Yevropa"], "correct": 0},
        {"text": "O'zbekistondagi eng baland cho'qqi qaysi?", "options": ["Hazrat Sulton", "Chatqol", "Qurama", "Nurota"], "correct": 0},
        {"text": "Janubiy qutbda joylashgan materik qaysi?", "options": ["Antarktida", "Afrika", "Avstraliya", "Janubiy Amerika"], "correct": 0},
        {"text": "Dunyodagi eng katta cho'l qaysi?", "options": ["Sahroi Kabir", "Qizilqum", "Gobi", "Qoraqum"], "correct": 0},
        {"text": "Yil fasllari almashinuvining asosiy sababi nima?", "options": ["Yerning Quyosh atrofida aylanishi", "Yerning o'z o'qi atrofida aylanishi", "Oyning tortish kuchi", "Shamol"], "correct": 0},
        {"text": "O'zbekistonda qaysi tog'li hudud mashhur?", "options": ["Hisor", "Ural", "Qrim", "Alp"], "correct": 0},
    ],
    "adabiyot": [
        {"text": "'Alpomish' dostoni qanday janrga kiradi?", "options": ["Doston", "Hikoya", "Ertak", "Masal"], "correct": 0},
        {"text": "Alisher Navoiyning 'Xamsa'si nechta dostondan iborat?", "options": ["5", "3", "7", "9"], "correct": 0},
        {"text": "'Oq kema' asari muallifi kim?", "options": ["Chingiz Aytmatov", "Abdulla Qodiriy", "O'tkir Hoshimov", "Erkin Vohidov"], "correct": 0},
        {"text": "'O'tkan kunlar' romanining muallifi kim?", "options": ["Abdulla Qodiriy", "Said Ahmad", "Askad Muxtor", "G'afur G'ulom"], "correct": 0},
        {"text": "'Shum bola' asarining muallifi kim?", "options": ["G'afur G'ulom", "Said Ahmad", "Abdulla Qahhor", "Cho'lpon"], "correct": 0},
        {"text": "Zahiriddin Muhammad Boburning mashhur asari qaysi?", "options": ["Boburnoma", "Xamsa", "Mehrobdan chayon", "O'tkan kunlar"], "correct": 0},
        {"text": "'Anor' hikoyasining muallifi kim?", "options": ["Abdulla Qahhor", "Said Ahmad", "Pirimqul Qodirov", "O'tkir Hoshimov"], "correct": 0},
        {"text": "Alisher Navoiy asosan qaysi tilda ijod qilgan?", "options": ["Eski o'zbek (chig'atoy)", "Arab", "Fors", "Rus"], "correct": 0},
        {"text": "Hikoya qanday adabiy janr?", "options": ["Kichik hajmdagi nasriy asar", "Sahnaviy asar", "Yirik roman", "She'riy asar"], "correct": 0},
        {"text": "Drama asarlari odatda qayerda namoyish etiladi?", "options": ["Teatrda", "Kitobda", "Gazetada", "Radio orqali"], "correct": 0},
        {"text": "'Dunyoning ishlari' romani muallifi kim?", "options": ["O'tkir Hoshimov", "Said Ahmad", "Abdulla Qahhor", "G'afur G'ulom"], "correct": 0},
        {"text": "Xalq og'zaki ijodi janrlaridan biri qaysi?", "options": ["Ertak", "Roman", "Qissa", "Drama"], "correct": 0},
    ],
    "jahon tarixi": [
        {"text": "Ikkinchi Jahon urushi qaysi yillarda bo'lgan?", "options": ["1939—1945", "1914—1918", "1929—1933", "1950—1953"], "correct": 0},
        {"text": "Amir Temur davlati qaysi yillarda mavjud bo'lgan?", "options": ["1370—1507", "1200—1300", "1500—1600", "1300—1370"], "correct": 0},
        {"text": "Qadimgi Misrda qurilgan mashhur piramidalar kimga bag'ishlangan?", "options": ["Faronlarga", "Savdochilarga", "Yozuvchilarga", "Tibbiyotchilarga"], "correct": 0},
        {"text": "Rim imperiyasi qaysi davrda hukmronlik qilgan?", "options": ["VIII asdan V asr boshigacha", "Faqat I asrda", "XIV—XV asrlar", "I asrdan oldin"], "correct": 0},
        {"text": "Qurilma insoniyat tarixidagi eng qadimiy yozuv tili hisoblanadi?", "options": ["Mix yozuvi", "Lotin yozuvi", "Grek yozuvi", "Arab yozuvi"], "correct": 0},
        {"text": "Kolumbning Amerikaga birinchi sayohati qaysi yilda bo'lgan?", "options": ["1492", "1442", "1519", "1600"], "correct": 0},
        {"text": "Sanoat inqilobi qaysi davlatda birinchi boshlandi?", "options": ["Angliya", "Frantsiya", "Germaniya", "Rossiya"], "correct": 0},
        {"text": "Qurilishdagi Ulug'ek osmoniyasi qaysi davrga mansub?", "options": ["XV asr", "XI asr", "XVIII asr", "VII asr"], "correct": 0},
        {"text": "Yaponiyada 1868-yilda boshlangan davlat modernizatsiyasi qanday ataladi?", "options": ["Meiji tiklanishi", "Sengoku davri", "Edo davri", "Taiko davri"], "correct": 0},
        {"text": "Insoniyatning Yer shari paydo bo'lishi to'g'risidagi eng mashhur ilmiy nazariya qaysi?", "options": ["Koinotsiya", "Geotsentr", "Antropotsentr", "Finikoteya"], "correct": 0},
        {"text": "Azteklarning poytaxti qaysi shahar edi?", "options": ["Tenochtitlan", "Tib", "Machu Pikchu", "Kairo"], "correct": 0},
        {"text": "Xitoyning buyuk qo'ldan qo'l g'alayotgan ellar davlati 221-yilda kim tomonidan barqarorlashtirilgan?", "options": ["Shi Huangdi", "Chu Xiongyu", "Kongzi", "Sun Tzu"], "correct": 0},
    ],

    "o'zbek tarixi": [
        {"text": "O'zbekiston mustaqilligi qaysi sana e'lon qilingan?", "options": ["1991-yil 31-avgust", "1991-yil 1-sentyabr", "1990-yil 24-mart", "1992-yil 2-mart"], "correct": 0},
        {"text": "Amir Temur qaysi davrda hukmronlik qilgan?", "options": ["1370—1405 yillar", "1300—1320 yillar", "1405—1420 yillar", "1450—1470 yillar"], "correct": 0},
        {"text": "Registon maydoni qaysi shaharda joylashgan?", "options": ["Samarqand", "Buxoro", "Xiva", "Toshkent"], "correct": 0},
        {"text": "O'zbekiston nechanchi yili BMTga a'zo bo'lgan?", "options": ["1992", "1991", "1995", "2000"], "correct": 0},
        {"text": "Buyuk ipak yo'li qaysi shaharlar orqali o'tgan?", "options": ["Samarqand va Buxoro", "Faqat Toshkent", "Moskva va Kiyev", "Pekin va Seul"], "correct": 0},
        {"text": "'Avesto' kitobi qaysi hududda yaratilgan?", "options": ["Markaziy Osiyo", "Misr", "Gretsiya", "Rim"], "correct": 0},
        {"text": "Ichan-qal'a qaysi shaharda joylashgan?", "options": ["Xiva", "Buxoro", "Samarqand", "Toshkent"], "correct": 0},
        {"text": "Jaloliddin Manguberdi kim edi?", "options": ["Mo'g'ul bosqinchilariga qarshi kurashgan sarkarda", "Buyuk rassom", "Shoir", "Olim"], "correct": 0},
        {"text": "O'zbekiston Respublikasining davlat tili qaysi?", "options": ["O'zbek tili", "Rus tili", "Ingliz tili", "Tojik tili"], "correct": 0},
        {"text": "O'zbekiston Konstitutsiyasi qaysi yil qabul qilingan?", "options": ["1992", "1991", "1994", "1996"], "correct": 0},
        {"text": "Qadimda O'zbekiston hududida qanday davlatlar bo'lgan?", "options": ["Buxoro amirligi, Xiva va Qo'qon xonliklari", "Bir yagona davlat", "Faqat shaharlar", "Mustamlakalar"], "correct": 0},
        {"text": "Afrosiyob qadimiy shahar qoldig'i qaysi shaharda?", "options": ["Samarqand", "Termiz", "Andijon", "Urganch"], "correct": 0},
    ],
    "algebra": [
        {"text": "2x + 7 = 19 tenglamasi yechimini toping", "options": ["x = 6", "x = 13", "x = −6", "x = 26"], "correct": 0},
        {"text": "x² − 5x + 6 = 0 tenglamasining ildizlari qaysilar?", "options": ["2 va 3", "1 va 6", "−2 va −3", "5 va 6"], "correct": 0},
        {"text": "Ikkita haddning yig'indisi 12, ko'paytuvchilari 27. Ular qancha?", "options": ["3 va 9", "6 va 6", "1 va 11", "4 va 8"], "correct": 0},
        {"text": "Ifoda 2(a − 3b) + 4(a − b) ning qiymati 10 bo'lsa, a − b qancha?", "options": ["5/3", "3", "10/3", "2"], "correct": 0},
        {"text": "Logarifm berilgan: log₂ 32 = ?", "options": ["5", "6", "16", "4"], "correct": 0},
        {"text": "Aritmetik progressiya: a₁ = 3, d = 4 bo'lsa, a₅ qancha?", "options": ["19", "23", "17", "15"], "correct": 0},
        {"text": "Geometrik progressiya: b₁ = 2, q = 3 bo'lsa, b₃ qancha?", "options": ["18", "12", "9", "6"], "correct": 0},
        {"text": "kvadrat tenglama tizimida D = 49 bo'lsa, |x| ning qiymati qancha?", "options": ["7", "49", "14", "3,5"], "correct": 0},
        {"text": "3x − 2 > 7 tengsizligi yechimini toping", "options": ["x > 3", "x < 3", "x > 9", "x < 9"], "correct": 0},
        {"text": "x⁴ − 16 = 0 tenglamasining haqiqiy ildizlari qaysilar?", "options": ["±2", "±4", "±8", "±1"], "correct": 0},
        {"text": "Birinchi darajali tenglama 5(x − 2) = 3x + 6 shaklida, uni soddalashtiring", "options": ["2x = 16", "2x = 6", "8x = 16", "x = 16"], "correct": 0},
        {"text": "y = 2x + 1 funksiya qaysi to'g'ri chiziqni tasvirlaydi?", "options": ["(0;1) nuqtadan o'tadigan, ko'tarilishli", "(0;0) nuqtadan o'tadigan, ko'tarilishli", "(0;1) nuqtadan o'tadigan, tushuvchi", "Parallel bo'ylash chizig'i"], "correct": 0},
        {"text": "x² + 4x + 9 ifodasi to'liq kvadratga yopish mumkinmi?", "options": ["Yo'q, D < 0", "Ha, D = 0", "Ha, D > 0", "Faqat x > 0 da"], "correct": 0},
        {"text": "Tenglamalar tizimi: x + y = 10, x − y = 4. x qancha?", "options": ["7", "5", "6", "3"], "correct": 0},
        {"text": "log₃ 1 + log₃ 27 natijasi qancha?", "options": ["3", "4", "1", "9"], "correct": 0},
        {"text": "Ifoda (a²)³ / a⁵ ni soddalashtirilgan shaklda yozing", "options": ["a", "a²", "1/a²", "a⁸"], "correct": 0},
        {"text": "O'xshash haddlarni keltirib, 3a/a ifodasi qanday soddalashadi?", "options": ["3", "1", "a", "0"], "correct": 0},
        {"text": "Kvadratning yuzasi 144 sm² bo'lsa, tomoni qancha sm?", "options": ["12", "24", "6", "144"], "correct": 0},
    ],
    "geometriya": [
        {"text": "Uchburchakning ichki burchaklari yig'indisi necha gradus?", "options": ["180°", "90°", "270°", "360°"], "correct": 0},
        {"text": "To'g'ri burchakli uchburchakning gipotenuzasi 5, bir o'tkir burchagi 30° bo'lsa, qarshi katet qancha?", "options": ["2,5", "5", "4,3", "3"], "correct": 0},
        {"text": "Aylaning radiusi 6 sm bo'lsa, yuzasi qancha sm²?", "options": ["36π", "12π", "6π", "18π"], "correct": 0},
        {"text": "Pifagor teoremasiga ko'ra 9 va 12 tomonli to'g'ri uchburchakning gipotenuzasi qancha?", "options": ["15", "21", "10,5", "18"], "correct": 0},
        {"text": "Ikki parallel to'g'ri chiziq kesuvchisi burchagi 65° bo'lsa, qo'shni burchak necha gradus?", "options": ["115°", "65°", "25°", "130°"], "correct": 0},
        {"text": "Do'g'orning ikki qirrasi tekislikda kesishda hosil bo'lgan burchak yumshoqligi 90° bo'lsa, u qanday nomlanadi?", "options": ["To'g'ri burchak", "O'tkir burchak", "Yassi burchak", "Butun burchak"], "correct": 0},
        {"text": "Teng yonli uchburchakning asosi 8, yon tomoni 10 bo'lsa, perimetri qancha?", "options": ["28", "20", "36", "18"], "correct": 0},
        {"text": "Doira markazining radiusi 5 sm. Uning ichida joylashgan nuqtadan markazgacha masofa 3 sm. Nuqta doirada yoki uning tashqarisidami?", "options": ["Ichida", "Tashqarisida", "Doiraga tegib turibdi", "Aniqlab bo'lmaydi"], "correct": 0},
        {"text": "Sahnaviy uchburchakning ichki burchaklaridan biri 90° bo'lsa, uni qanday ataladi?", "options": ["To'g'ri burchakli", "O'tkir", "Yassi", "Teng yonli"], "correct": 0},
        {"text": "Silindrning radiusi 3, balandligi 10 bo'lsa, asosining yuzasi qancha?", "options": ["9π", "30π", "10π", "6π"], "correct": 0},
        {"text": "Ikki parallel tekislik orasidagi masofa 4 sm. Perpendikulyar kesimida bu masofa qanday ataladi?", "options": ["Balandlik", "Asos", "Yon qirra", "Diagonal"], "correct": 0},
        {"text": "Ko'pburchakning ichki burchaklari yig'indisi 1080° bo'lsa, nechta tomoni bor?", "options": ["8", "6", "7", "9"], "correct": 0},
        {"text": "To'g'ri to'rtburchakning diagonali 13, bir tomoni 5 bo'lsa, ikkinchi tomoni qancha?", "options": ["12", "8", "18", "√44"], "correct": 0},
        {"text": "Xarakterli nuqta (nazorat nuqtasi) nima uchun ishlatiladi?", "options": ["Desinxroniyani tuzatish uchun", "Kuzatishni osonlashtirish uchun", "Chizishni tezlashtirish uchun", "Massani o'lchash uchun"], "correct": 0},
        {"text": "To'rtburchakning ichki burchaklari yig'indisi nechaga teng?", "options": ["360°", "180°", "270°", "540°"], "correct": 0},
        {"text": "Uchburchakning bitta tomoni 7, ikkinchisi 9. Uchinchi tomak uchun mumkin bo'lgan eng katta qiymat qancha?", "options": ["15", "16", "17", "2"], "correct": 0},
        {"text": "Sharning markazidan r teng masofadagi nuqtalar to'plami qanday nomlanadi?", "options": ["Sfera", "K atmosfera", "Doira", "Silindr"], "correct": 0},
        {"text": "Tenglamalar: 2x = 3y va x + y = 10. x qancha?", "options": ["6", "4", "5", "7"], "correct": 0},
    ],
}

# Fan nomi bank kalitini "o'z ichiga olmaydigan" holatlar uchun. Masalan
# "O'zbekiston tarixi" ichida "o'zbek tarixi" satri yo'q, shu bilan birga
# savollar aynan bir xil — ikkala nom ham bitta fanni bildiradi.
QUESTIONS_BANK["o'zbekiston tarixi"] = QUESTIONS_BANK["o'zbek tarixi"]


class Command(BaseCommand):
    help = "O'yinlar omboriga (PooledQuestion) qo'lda yozilgan savollarni joylaydi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            action="append",
            default=[],
            help="Faqat shu fan uchun seed qilish. Bir necha marta ishlatish mumkin.",
        )
        parser.add_argument(
            "--school-class",
            action="append",
            default=[],
            help=(
                "Faqat shu sinf uchun seed qilish. Berilmasa — fanning umumiy banki "
                "(barcha sinflar uchun), bu odatiy holat."
            ),
        )
        parser.add_argument("--dry-run", action="store_true", help="Hech narsa saqlamay, faqat hisoblaydi.")

    def handle(self, *args, **options):
        subjects = self._resolve_subjects(options["subject"])
        classes = self._resolve_classes(options["school_class"])
        if not subjects:
            raise CommandError("Hech bir fan topilmadi. --subject bilan aniqroq nom bering.")
        if options["school_class"] and not classes:
            raise CommandError("Hech bir sinf topilmadi. --school-class bilan aniqroq nom bering.")

        total_created = 0
        for school_class in classes:
            for subject in subjects:
                created = self._seed_pool(subject, school_class, dry_run=options["dry_run"])
                if created or options["dry_run"]:
                    scope = "barcha sinflar" if school_class is None else school_class.name
                    self.stdout.write(f"{subject.name} ({scope}): +{created} ta savol")
                total_created += created

        self.stdout.write(self.style.SUCCESS(f"Jami {total_created} ta savol qo'shildi."))

    def _resolve_subjects(self, filters: list[str]) -> list[Subject]:
        """Filter berilsa — o'sha bank kalitlariga mos fanlar, aks holda bankdagi
        barcha fanlarga mos keluvchi fanlar. Kalit fan nomi tarkibidan qidiriladi
        (masalan "matematika" — "Matematika-Demo"ni ham topadi).
        """
        bank_names = set(QUESTIONS_BANK)
        wanted = [name.lower() for name in filters if name.lower() in bank_names]
        if filters and not wanted:
            raise CommandError(
                "Berilgan fan nomi savollar bankida yo'q. Mavjud fanlar: "
                + ", ".join(sorted(bank_names))
            )
        keys = wanted or sorted(bank_names)

        matches = []
        for subject in Subject.objects.all():
            lower = subject.name.lower()
            if any(key in lower for key in keys):
                matches.append(subject)
        return matches

    def _resolve_classes(self, filters: list[str]) -> list[SchoolClass | None]:
        """Sinflarni seed qilish uchun. Filtr berilmasa — bitta `None`, ya'ni
        fanning umumiy banki: bir marta yozilgan savol har bir sinfga xizmat
        qiladi, shuning uchun har bir sinfni alohida to'ldirish shart emas."""
        if not filters:
            return [None]
        return list(SchoolClass.objects.filter(name__in=filters).order_by("name"))

    def _bank_for(self, subject: Subject) -> list[dict] | None:
        lower = subject.name.lower()
        for key, bank in QUESTIONS_BANK.items():
            if key in lower:
                return bank
        return None

    def _seed_pool(self, subject: Subject, school_class: SchoolClass | None, *, dry_run: bool) -> int:
        questions = self._bank_for(subject)
        if not questions:
            return 0

        existing_texts = set(
            PooledQuestion.objects.filter(subject=subject, school_class=school_class).values_list(
                "text", flat=True
            )
        )
        new_questions = [q for q in questions if q["text"] not in existing_texts]
        if dry_run or not new_questions:
            return len(new_questions)

        with transaction.atomic():
            PooledQuestion.objects.bulk_create(
                PooledQuestion(
                    subject=subject,
                    school_class=school_class,
                    text=q["text"],
                    options=q["options"],
                    correct_index=q["correct"],
                )
                for q in new_questions
            )
        return len(new_questions)