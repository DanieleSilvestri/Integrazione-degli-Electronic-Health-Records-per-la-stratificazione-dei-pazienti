# -*- coding: utf-8 -*-

import csv
import os


def csvToNeo(path): #input:path della cartella che contiene i database
    relazioni={} #dizionario con chiave campo e valori tutte le tabelle dove compare 
    tabelle={} #dizonario con chiave i nomi delle tabelle e come valori i campi delle stesse
    nodi="" #stringa per le query in linguaggio Cypher
    salvalori={} #dizionario per registrare tutti i diversi valori presenti nei campi
    for cartella, sottocartelle, files in os.walk(path):
        
        for i in files:
            if i[len(i)-4:] == ".csv":
                percorso= cartella + "\\" + i
                with open(percorso,encoding="utf-8") as csv_file:
                    lettore = csv.reader(csv_file, delimiter=',') 
                    tabella=i[:len(i)-4]
                    header=next(lettore)
                    contarighe=0
                    for row in lettore:
                        c=0       #contatore per le colonne
                        contarighe+=1 #contatore per le righe
                        nodi+="CREATE(" + "n:" + tabella + "{"
                        for h in header: #per poter visitare tutte le colonne
                            if "'" in row[c]:   #casi che vanno corretti per evitare errore in query cypher(i caratteri "" e \ in cypher sono speciali)
                                row[c]=row[c].replace("'","\"")
                            if "\\" in row[c] and len(row[c])== 1:
                                row[c]=row[c].replace("\\","\\\\")
                            if h not in salvalori.keys():
                                salvalori[h]=set()     #qui salvo tutti i valori di ogni attributo,poichè successivamente serviranno per i nodi che si andranno a creare
                            if c < len(row) -1 :
                                nodi+= h + ":" + "'" +  row[c] + "',"
                            else: #l'ultima proprietà non ha bisogno delle "," alla fine
                                nodi+= h + ":" + "'" +  row[c] + "'"  #per ultimo attributo la virgola non serve                           
                            salvalori[h].add(row[c])
                            c+=1
                        nodi+="})\nWITH 1 as dummy \n"
                        if contarighe > 29: #per il limite impostato a 30 istanze per ogni file excel letto
                            break
                    nome=i[:len(i)-4]
                    tabelle[nome]=header #nel dizionario tabella troveremo come chiave i nomi delle tabelle e come valori i propri attributi
                    for attributo in header:  #ciclo for per trovare le relazioni
                        if attributo[len(attributo)-3:] == "_id" or attributo == "code" or attributo=="icd_code" or attributo=="itemid": #cerco i campi che finiscono con _id perchè sono loro a relazionare le tabelle e per gli altri tre identificatori "speciali"
                            if attributo not in relazioni:
                                relazioni[attributo]=[nome]
                            else:
                                relazioni[attributo].append(nome)
                   

    #ora le chiavi del dizionario relazioni sono i vari identificatori presenti nel db e i valori le tabelle nelle quali compaiono
    #ora le chiavi del dizionario tabelle sono i nomi delle tabelle e i valori tutti i loro campi
    #adesso cerchiamo i campi doppi 
    
    visti=[]
    ripetuti=[]                     
    for chiave in tabelle.keys():
        for campo in tabelle[chiave]:
            if campo not in visti:
                visti.append(campo)
            elif campo[len(campo)-3:] != "_id" and campo != "code" and campo != "icd_code" and campo != "itemid" and campo not in ripetuti:
                campo+="_a" #identificativo per capire che l'attributo deve trasformarsi in un nodo
                ripetuti.append(campo) #tutti gli attributi che diventano nodi
                
    #aggiungiamo gli attributi ripetuti al
    #ora per ogni ripetuto vediamo le tabelle a cui devono essere collegati
    
    for tab in tabelle.keys():
        for att in ripetuti:
            a=att[:len(att)-2]
            if a in tabelle[tab]:
                if att not in relazioni:
                    relazioni[att]=[tab]
                else:
                    relazioni[att].append(tab)
                    
    
    #ora anche gli attributi ripetuti sono aggiunti nelle relazioni

    for l in relazioni.keys():
        if l[len(l)-3:] != "_id" and l != "code" and l != "icd_code" and l != "itemid":
            chiave=l[:len(l)-2]+"_id"
            tabelle[l]=[chiave]

    #ora creiamo il grafo,con diverso comportamento se il nodo deriva da una tabella esistente o da un attributo "ripetuto"
    grafo={}
    riprel= []
    for nometab in tabelle.keys(): 
        if nometab[len(nometab)-2:]!="_a": #nodi tabelle
            grafo[nometab]=set()
            for campo in relazioni:
                if nometab in relazioni[campo] and nometab!=campo and campo[len(campo)-2:]!="_a":
                    for t in relazioni[campo]:
                        arco=nometab + "_" + t  #nome dell'arco che collega le tabella (semplice formato nometabella1_nometabella2)
                        doppia=t + "_" + nometab
                        if arco not in riprel and doppia not in riprel and nometab!=t:
                            grafo[nometab].add((t,arco))
                            riprel.append(arco)       
        else:   #nodi attributo
            nome=nometab[:len(nometab)-2]
            grafo[nome]=set()
            for campo in relazioni:
                if campo==nometab:
                    for t in relazioni[campo]:
                        arco=nome + "_" + t  #nome dell'arco che collega le tabella (semplice formato nometabella1_nometabella2)
                        doppia=t + "_" + nome
                        if arco not in riprel and doppia not in riprel:
                            grafo[nome].add((t,arco))
                            riprel.append(arco) 
                        
                    
             
    #scriviamo in linguaggio Cypher i nodi e li salviamo sul file grafo.CYPHER e successivamente le relazioni
    rela="" #stringa per le relazioni in cypher
    for t in tabelle: #aggiunta dei nuovi nodi derivanti dagli attributi doppi nel file cypher
        if t[len(t)-2:] == "_a":
            valori=salvalori[t[:len(t)-2]]
            for v in valori:
                nodi+="CREATE(" + "n:" + t[:len(t)-2] + "{"
                for at in tabelle[t]:
                    nodi+=at + ":" + "'" + v + "'"
                nodi+="})\nWITH 1 as dummy \n"
    for nodo in grafo:
        for rel in grafo[nodo]:
            rela+="MATCH(a:" + nodo + "),(b:" + rel[0] + ") CREATE(a)-[r:" + rel[1] +"]->(b);\nWITH 1 as dummy \n"
    cypher=nodi+rela
    file= open("grafo.cypher", "w",encoding="utf-8")
    file.write(cypher)
    file.close()



            
            
        
    
          


            