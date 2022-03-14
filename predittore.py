# -*- coding: utf-8 -*-
import csv
import os

def predittore(path): #input:path della cartella che contiene i database
    infop={}  #dizionario per mappare l'id dell'entrata in ps con i dati
    anagrafici={} #dizionario per mappare subject_id con i relativi dati anagrafici(sesso,età)
    terapiaintens=set()  #set dove verranno inseriti gli hadm_id delle persone entrate in terapia intensiva
    dizstay={}   #mapping stay_id con hadm_id tra MIMIC IV e MIMIC ED
    for cartella, sottocartelle, files in os.walk(path):
        
        for i in files:
            if i[len(i)-4:] == ".csv":
                percorso= cartella + "\\" + i
                nome=i[:len(i)-4]
                if nome=="medrecon":  #prima tabelle i cui dati all'interno ci interessano (tabella che contiene i farmaci che i pazienti assumono prima dell'entrata in ps)
                    with open(percorso,encoding="utf-8") as csv_file:
                        lettore = csv.reader(csv_file, delimiter=',') 
                        header=next(lettore)
                        for row in lettore:
                            infop[row[1]]=[row[0]]  #inserisce all'interno del dizionario il subject_id
                            
                        
                if nome=="triage": #la tabella triage contiene tutti i dati sui segni vitali all'entrata del paziente in ps
                    with open(percorso,encoding="utf-8") as csv_file:
                        lettore = csv.reader(csv_file, delimiter=',') 
                        header=next(lettore)
                        for row in lettore:
                            if row[1] in infop: 
                                infop[row[1]].append(row[2])
                                infop[row[1]].append(row[3])
                                infop[row[1]].append(row[4])
                                if row[5]=="":
                                    row[5]=0
                                o2sat=round(float(row[5]),0)
                                if 50<=o2sat<=89:   #raggruppo tutto sotto la soglia critica del 90
                                    o2sat=90
                                infop[row[1]].append(o2sat)
                                infop[row[1]].append(row[6])
                                infop[row[1]].append(row[7])
                                infop[row[1]].append(row[8])
                                infop[row[1]].append(row[9])
                                
                                
                if nome=="edstays": #necessario per mappare i dati dei ricoveri (quando cambiano reparto lo stay_id varia) da MIMIC IV a MIMIC ED
                    with open(percorso,encoding="utf-8") as csv_file:
                        lettore = csv.reader(csv_file, delimiter=',') 
                        header=next(lettore)
                        for row in lettore:
                            dizstay[row[2]]=row[1]
                    
                if nome=="patients": #raccolta dei dati anagrafici in un dizionario per renderne la ricerca più veloce
                    with open(percorso,encoding="utf-8") as csv_file:
                        lettore = csv.reader(csv_file, delimiter=',') 
                        header=next(lettore)
                        for row in lettore:
                            anagrafici[row[0]]=[row[1],row[2]]
                            
                if nome=="icustays": #tabella che contiene tutti i ricoveri in terapia intensiva
                    with open(percorso,encoding="utf-8") as csv_file:
                        lettore = csv.reader(csv_file, delimiter=',') 
                        header=next(lettore)
                        for row in lettore:
                            terapiaintens.add(row[1])
                

    #creazione file csv per la predizione
    tabella=[]
    header=["gender","age","temperature","heartrate","resprate","o2sat","sbp","dbp","pain","acuity","icu"]
    for entrata in infop:
        riga=[]
        paziente=infop[entrata][0]
        riga.append(anagrafici[paziente][0])  #gender
        riga.append(anagrafici[paziente][1])  #age
        riga.append(infop[entrata][1])  #temperature
        riga.append(infop[entrata][2])  #heartrate
        riga.append(infop[entrata][3])  #resprate
        riga.append(infop[entrata][4])  #o2sat
        riga.append(infop[entrata][5])  #sbp
        riga.append(infop[entrata][6])  #dbp
        riga.append(infop[entrata][7])  #pain
        riga.append(infop[entrata][8])  #acuity
        if dizstay[entrata] in terapiaintens: #icu  "1"=terapia intensia "0"=no terapia intensiva
            riga.append("1")
        else:
            riga.append("0")
        if "" not in riga and 90<=riga[5]<=100:  #per evitare righe con valori vuoti e valori falsati (ossigenazione non può essere sopra ai 100)
            tabella.append(riga)
        
    
        
    with open("result.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow (header)
        writer.writerows(tabella)
