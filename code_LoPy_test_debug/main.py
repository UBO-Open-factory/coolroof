#
#           Programe modifier et annoter par Arthur
#
import pycom
import time
import socket
import ubinascii
import math
import gc #gestion de la RAM évite l'overload
import machine
from machine import Pin
from machine import UART
from machine import RTC
from network import LoRa

LORA_FREQUENCY = 868100000
LORA_GW_DR = "SF7BW125" #DR_5
LORA_NODE_DR = 5
#
#### initialize_LoRa_in_LORAWAN_mode ####
# Please pick the region that matches where you are using the device:
# norme_hf = Asia = LoRa.AS923
# norme_hf = Australia = LoRa.AU915
norme_hf = Europe = LoRa.EU868
# norme_hf = United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=norme_hf)
# # # create an OTA authentication params
dev_eui = ubinascii.hexlify(lora.mac(),":")
print(dev_eui)
app_eui = ubinascii.unhexlify('6a65737569736c65')
app_key = ubinascii.unhexlify('A4456138421ABB55321832941218CC55')
# # # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
# # # join a network using OTAA
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key), timeout=0)
# # # wait until the module has joined the network
while not lora.has_joined():
     time.sleep(5)
     print('Not joined yet...')
print("Joined")
# #
# # # remove all the non-default channels
# for i in range(3, 16):
#     lora.remove_channel(i)
# # # create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
# # # set the LoRaWAN data rate
# s.setsockopt(socket.SOL_LORA, socket.SO_DR, LORA_NODE_DR)
# # # make the socket blocking
s.setblocking(True)
# time.sleep(5.0)
rtc = RTC()
# print('*******************************')
previoustime=rtc.now()[4] # [4] = hh:mm
# print('*******************************')
dif=(rtc.now()[4])-previoustime
#########################################

##### activation_LoRa ####
# initialisation uart
uart = UART(1, 9600) # init with given baudrate
# liaison UART par défaut P4=Rx ; =Tx
uart.init(9600, bits=8, parity=None, stop=1)
pycom.heartbeat(False)
# initialisation liste adresses Xbees capteurs
liste_adresses=[0x0013a20041ab21bf,0x0013a20041c86e34,0x0013a20041c870cf,0x0013a2004106ad08,0x0013a20041ab21e2,0x0013a20041ab2181,0x0013a20041ab21b5,0x0013a20041ab216e,0x0013a20041ab21ca,0x0013a20041c86e52]
taille_liste_adresses=len(liste_adresses)
# initialisation compteur donnees et tableau
compteur_donnees=0
compteur_timeout=0
tableau_envoi_lora = ['+99.99'] * taille_liste_adresses*2 # 2 octets par capteur
##########################

#### boucle_principal ####
while True:
    while (dif<1) :
        gc.collect()
        #print ('gc.mem_free()')
        #print(gc.mem_free())
        dataReceived=uart.read()
        pycom.rgbled(0x808000) #faible alumage de la led en blanc
        time.sleep(0.5)# en s

        while dataReceived == None :
            #print("pas de donnees")
            #time.sleep(4)m
            dataReceived=uart.read()
            nowtime=rtc.now()[4]
            pycom.rgbled(0x101010) #faible alumage de la led en blanc
####################################################

# début de trame (1 o) + longueur (2 o)=
# dataReceived[0]+dataReceived[1] + checksum (1 o) car la longueur est
# datareceived[1]*2^8+dataReceived[2]=0x0012 apres on la traduit on decimal
        longueur=dataReceived[1]*256+dataReceived[2]+4
        print('longueur_trame_reçu (en octets) :', longueur)
# si la taille de la trame n'est pas égale a la longeur
        if len(dataReceived)!=longueur:
# afficher le code erreur hssl
            print('hssl_1 : ', longueur)
            print('len_dataReceived',len(dataReceived))
            #longueur2=dataReceived[2]+4
            #print('hssl_2 : ',longueur2)
        else:
            trame=longueur*[0]#On construit la trame qu'on va traiter elle a la longueur de la trame qu'on a recu en uart
            gc.collect()
            for i in range(0,longueur) :
                trame[i]=hex(dataReceived[i])
                print(i,' : ',trame[i])

            # traitement de la donnee
            if trame[3]=='0x92' : # envoi donnée analogique
                adresse_source_raw=trame[4:12]#ca marche pas avec 11 et ca marche avec 13
                print('adresse_source_raw : ',adresse_source_raw)
                adresse_source=0

                # mise en forme adresse du xbee source
                for i in range(0,8) :
                    adresse_source=adresse_source+((int(adresse_source_raw[i]))*(256**(7-i)))

                # test de l'adresse source
                if (adresse_source  in liste_adresses):
####             """a voir else"""
# Module source pas dans la liste -> on drop la trame et on n'incrémente pas le compteur
#determination de l'T pour placer la valeur au bon endroit dans le tableau
            # print(adresse_source)
                    index=liste_adresses.index(adresse_source)
                    print('#### comparaison adresse_source et liste_adresses ####')
                    print('adresse_source : ',adresse_source)
                    print('liste_adresses : ',liste_adresses)
                    print('######################################################')

                    if tableau_envoi_lora[index]!='+99.99':
                        data_raw=trame[19:21]

                #tableau_envoi_lora[index]=int(data_raw[0])
                #tableau_envoi_lora[index+1]=int(data_raw[1])
                    else:
                        data_raw=trame[19:21]
                        data_raw2=trame[21:23]
                        print('data_raw  :',data_raw)
                        print('data_raw2 :',data_raw2)
                        print('######################################################')
                        print()
                        mesure1=int(data_raw[0])*256|int(data_raw[1])
                        mesure2=int(data_raw2[0])*256|int(data_raw2[1])
                        tension1 = (mesure1 * 1200) / 1023
                        tension2 = (mesure2 * 1200) / 1023
                        temper1 = (tension1 - 500) / 10
                        temper2 = (tension2 - 500) / 10
                        temp1="%.2f" %temper1
                        temp2="%.2f" %temper2
                        tableau_envoi_lora[2*index]=str(temp1)
                        tableau_envoi_lora[2*index+1]=str(temp2)
                        # incrémentation compteur

                        for i in range(0, taille_liste_adresses*2):
                            tableau_envoi_lora[i]=str(tableau_envoi_lora[i])

                # print()
            #    compteur_donnees=compteur_donnees+1
        # print('*******************************')
            T=tableau_envoi_lora
            for i in range(0,taille_liste_adresses*2):
                if T[i]>='0':
                    B=T[i]
                    if ('.' in T[i]):
                        index=B.index('.')
                        #print(index)
                        if index==1 :
                            if (len(T[i])==3):
                                T[i] ="+" +"0"+T[i]+"0"
                                # print(T[i])
                            if len(T[i])==4 :
                                T[i] ="+"+"0"+T[i]
                                # print(T[i])
                        if index==2 :
                            if len(T[i])==5 :
                                T[i]="+"+T[i]
                                # print(T[i])
                            if len(T[i])==4:
                                T[i] ="+"+T[i]+"0"
                                # print(T[i])
                    if ('.' not in T[i]):
                        if len(T[i])==1:
                            T[i] = "+"+"0"+T[i]+"0"*2
                        if len(T[i])==2:
                            T[i] = "+"+T[i]+"0"*(4-len(T[i]))
                else :
                    # print(i)
                    T[i]=str(T[i])
                    T[i]=T[i].replace("-","") #remplace - par rien ?
                    # print(T[i])
                    B=T[i]
                    if ('.' in T[i]):
                        index=B.index('.')
                        # print(index)
                        if index==1 :
                            if (len(T[i])==3):
                                T[i] ="-" +"0"+T[i]+"0"
                                # print(T[i])
                            if len(T[i])==4 :
                                T[i] ="-"+"0"+T[i]
                                # print(T[i])
                        if index==2 :
                            if len(T[i])==5 :
                                T[i]="-"+T[i]
                                # print(T[i])
                            if len(T[i])==4:
                                T[i] ="-"+T[i]+"0"
                                # print(T[i])
                    if ('.' not in T[i]):
                        if len(T[i])==1:
                            T[i] = "-"+"0"+T[i]+"0"*2
                        if len(T[i])==2:
                            T[i] = "-"+T[i]+"0"*(4-len(T[i]))
                        print("**** tableau T[i]****")
                        print(T[i])
                        print("*****")
            # print('*******************************')
            B=T[0]
            for i in range(1,taille_liste_adresses*2):
                B=B+T[i]
                i=i+1
            #print("**** B ****")
            #print(B)
            #print("***********")
            L=B.split('.')
            #print("**** L ****")
            #print(L)
            #print("***********")
            T= "".join(map(str, L))
            rtc = RTC()
            nowtime=rtc.now()[4]
            dif=nowtime-previoustime

            if dif<0:
                dif=dif+59
            else:
                dif=dif
    print("#### tableau envoyée ####")
    print('tableau LORA:',T)
    print("#########################")
    print()
    s.send(T)
    pycom.rgbled(0x004000)
    time.sleep(0.1)
    pycom.heartbeat(False)
    del(T)
    del(L)
    del(B)
    tableau_envoi_lora = ['+99.99'] * taille_liste_adresses*2
    previoustime=nowtime
    dif=previoustime-nowtime
    gc.collect()
    gc.mem_free()
