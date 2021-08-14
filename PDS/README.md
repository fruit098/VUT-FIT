The aim of this project is to use features of TLS client hello packets in order to fingerprint the fraffic during using various mobile apps like (TikTok, Instagram, Facebook).
The generated database is used then to predict the apps in network mobile trafic.


### Slovak part
Skripty boli pouzivane s pythonom 3.6.
Pozadovane packages su v requirements.txt.

Pustenie jednotlivych skriptov je nasledovne:

python ./meno-skriptu

parser.py [-t] ./path.pcap ./output.csv = rozparsuje pcap do csv databazi, prepinac -t anotuje vystupny dataset na zaklade keywords inak je meno aplikacie pridelene podla nazvu pcapu, 
    na vstupe ocakava vstupny cestu k vstupnemu pcapu a vystupnu cestu pre csv
classifier.py = zoberie cestu pre databazovi csv a test csv a spocita confusion matrix spolu s metrikami, cesty k suborom su ako zadani ako stringy v programe, ktore treba pozmenit
ja3.py = upraveny oficialny skript z https://github.com/salesforce/ja3/tree/master/python/ja3, ktory vyuziva parser.py
db_fp.csv = vysledna databaza odtlackov
test.csv = pouzita testovacia sada odtlackov

Pre vytvorenie databazi je potrebne pustit parser.py nad kazdym pcapom. Fingerprinty su postupne appendovane.
