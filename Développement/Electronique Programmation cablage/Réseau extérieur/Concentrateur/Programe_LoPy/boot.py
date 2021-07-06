#
#
#	CoolRoof - Concentrateur réseau intérieur
#	Programme de démarrage
#
#	Version 1.1
#
#
#	mai 2021
#
#	Laurent MARCHAL, Leila MERZAC et Arthur PIGNALET
#
#
#



# ***********************************************************************
#       IMPORTATIONS

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



# ***********************************************************************
#       DECLARATIONS

# suppression du "battement de coeur" (flash périodique de la led bleue
pycom.heartbeat(False)

# Initialisation de la liaison avec le concentrteur Xbee
# liaison UART par défaut P4=Rx ; Tx non utilisé
UART = UART(1, 9600)
UART.init(9600, bits=8, parity=None, stop=1)



# initialisation des différents tableaux contenant les informations des terminaux
liste_adresses=[0x0013a20041AB2186,0x0013a20041C86BDD,0x0013a20041C86E7F,0x0013a20041C86E7E,0x0013a20041C86E4A,0x0013a20041C86C5B,0x0013a20041CD9223,0x0013a20041C870EA,0x0013a20041CD9302,0x0013a20041AB21DD]
liste_terminaux=['EXT_A1','EXT_A2','EXT_A3','EXT_B1','EXT_B2','EXT_B3','EXT_C1','EXT_C2','EXT_C3','EXT_N']
nb_de_terminaux=len(liste_adresses)

# nombre de capteurs pa terminal.
# 2 pour le réseau intérieur
# 3 pour le réseau extérieur
nb_capteur_par_terminal = 3


# intervalle de temps entre deux émissions LoRa
#en minutes
interval_emission_lora = 4

# tableau regroupant les valeurs de tous les capteurs de tous les terminaux.
# les valeurs sont rangées par terminal :
tableau_envoi_lora = [''] * nb_de_terminaux* nb_capteur_par_terminal

# initialisation de l'horloge temps réel.
# elle n'est pas mise à l'heure.
# elle sert uniquement de chronomètre pour définir les émissions LoRa
rtc = RTC()

# heure à laquelle à eu lieu la dernière émission LoRa
derniere_emission_lora=rtc.now()[4]

# definition de deux flags permettant la reconnaissance
# des trames qui seront reçues du Xbee concentrateur
flags_chaine_commencee = False
flags_longueur = False

# variable pour mémoriser la longueur d'une trame
# cette valeur sera extraite du début de la trame
longueur_trame = 0

# liste pour mémoriser les caractères reçus dans une trame
# remise à zéro après la réception et le traitement d'une trame
liste_caracteres_recus = []


def cherche_index_terminal():
    # extrait l'adresse de la liste "liste_caracteres_recus"
    # cherche l'index de l'adresse dans le tableau "liste_adresses"
    # s'il le trouve : renvoie l'index
    # sinon renvoie -1
    global liste_adresses
    global liste_caracteres_recus

    #resultat de la recherche (par défaut)
    res = -1

    # changement de nom de variable par facilité
    cr=liste_caracteres_recus

    # déclaration de l'adresse qui va être cherchée dans la "liste_caracteres_recus"
    adresse_source=0

    # lecture des 8 octets de l'adresse et calcul de celle-ci
    for i in range(1,9) :
        adresse_source=adresse_source+((cr[i])*(256**(8-i)))

    # cherche l'adresse dans la liste "liste_adresses"
    if (adresse_source  in liste_adresses):
        #si on la trouve on place son index dans la variable de retour "res"
        res=liste_adresses.index(adresse_source)

    return res

def conversion_temperature_en_chaine(valcan):
    #convertit la température "temp" qui est une valeur brute fournie par le CAN
    # en une valeur de type chaine de caractère, sans la formater
    #la formule est donnée par le fabriquant du capteur utilisé (TMP36)
    T=''
    tension = (valcan * 1200 ) / 1023
    temperature = (tension - 500) / 10
    T = "%.2f"%temperature
    return T

def traitement_trame():
    #
    #   Uniquement si une trame a été reçue correctement.
    #   Les octets reçus sont stockés dans la liste "liste_caracteres_recus"
    #       Extraction de l'adresse du module émetteur
    #       recherche de l'adresse dans la liste "liste_adresses"
    #       Si l'adresse est connue
    #           Extraction de 2 ou 3 températures
    #           mémorisation dans le tableau "tableau_envoi_lora"
    #       Sinon : pas de traitement
    global liste_adresses
    global nb_de_terminaux
    global nb_capteur_par_terminal
    global tableau_envoi_lora
    global liste_test
    #global T
    global liste_caracteres_recus

    # extraction de l'adresse
    index_terminal = cherche_index_terminal()
    if (index_terminal != -1):
        # l'adresse contenue dans la trame reçue est connue et son index trouvé dans le tableau "liste_adresses"
        #print('     Trame reçue de ',liste_terminaux[index_terminal])
        #
        #   Récupère les informations de température et les stocke dans le tableau "tableau_envoi_lora"
        #
        #
        temperature1 = liste_caracteres_recus[16]*256 + liste_caracteres_recus[17]
        temperature2 = liste_caracteres_recus[18]*256 + liste_caracteres_recus[19]
        if (nb_capteur_par_terminal == 3):
            temperature3 = liste_caracteres_recus[20]*256 + liste_caracteres_recus[21]

        # conversion des températures du format analogique au format chaine de caractère
        s_temperature1 = conversion_temperature_en_chaine(temperature1)
        s_temperature2 = conversion_temperature_en_chaine(temperature2)
        if (nb_capteur_par_terminal == 3):
            s_temperature3 = conversion_temperature_en_chaine(temperature3)

        #
        #TODO ecrire les températures dans la liste "tableau_envoi_lora"
        tableau_envoi_lora[index_terminal * nb_capteur_par_terminal] = s_temperature2
        tableau_envoi_lora[index_terminal * nb_capteur_par_terminal + 1 ] = s_temperature3
        if (nb_capteur_par_terminal == 3):
            tableau_envoi_lora[index_terminal * nb_capteur_par_terminal + 2 ] = s_temperature1

        print (tableau_envoi_lora)

        for i in range(0, nb_de_terminaux*nb_capteur_par_terminal):
            tableau_envoi_lora[i]=str(tableau_envoi_lora[i])



        T=tableau_envoi_lora
        for i in range(0,nb_de_terminaux*nb_capteur_par_terminal):
            if T[i]>='0':
                B=T[i]
                if ('.' in T[i]):
                    index=B.index('.')
            # print(index)
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
                T[i]=T[i].replace("-","")
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

                    # print(T[i])
        # print('*******************************')

        B=T[0]
        for i in range(1,nb_de_terminaux*nb_capteur_par_terminal):
            B=B+T[i]
            i=i+1
        # print(B)
        L=B.split('.')
        # print(L)
        T= "".join(map(str, L))
        return T

def reception_trame():
    #
    #   Vérifie si une trame est disponible par scrutation du buffer de l'UART
    #   Si un début de trame est détécté :
    #           lit la longueur puis le reste de la trame
    #           vérifie la corruption par l'exploitation du checskum
    #           appelle la fonction de traitement de la trame si tout est correct
    #
    global liste_caracteres_recus
    global flags_chaine_commencee
    global flags_longueur
    global longueur_trame

    # Si on n'est pas commencé à lire une trame sur le port UART
    if (flags_chaine_commencee == False):
        # si au moins un caractère est présent dans le buffer de l'UART
        if (UART.any() >= 1):
            #on lit le caractère présent dans le buffer de l'UART
            caractere_lu = UART.read(1)
            #S'il est égal à 0x7E on a peut être détecté un début de trame
            if (ord(caractere_lu) == 0x7E):
                # on indique que la lecture d'une trame est commencée
                flags_chaine_commencee = True
    else:
        # on a cemmencé à lire une trame
        # si on ne connait pas la longuer attendue de la trame
        if (flags_longueur == False):
            # y a t il au moins 2 caractères disponibles dans le buffer de l'UART
            if (UART.any() >=2 ):
                #on lit les 2 caractères
                MSB_longueur = ord(UART.read(1))
                LSB_longueur = ord(UART.read(1))
                # Calcul de la longueur attendue de la trame (nb de caractères à lire)
                longueur_trame = MSB_longueur * 256 + LSB_longueur + 1 #+1 pour le checksum
                # on indique que la longueur de trame attendue est connue.

                if (longueur_trame < 30):
                    flags_longueur=True
                else:
                    flags_chaine_commencee=False

        else :
            #une trame est commencée et on connait sa longueur attendue
            if (UART.any() >= longueur_trame ):
                control = 0
                i=0
                #on lit le nombre de caractère -1 (pour ne pas lire le check sum tout de suite)
                while (i<longueur_trame-1):     #-1 pour ne pas lire le checksum
                    caractere_lu = UART.read(1)
                    #on place ces valeurs dans la liste "liste_caracteres_recus"
                    liste_caracteres_recus.append(ord(caractere_lu))
                    # on additionne les valeurs des caractères pour la comparer plus tard au checksum
                    control = control + ord(caractere_lu)
                    i = i + 1
                # on ne garde que les 8 LSBits du total
                control = control & 0xff
                # on lit le check sum dans l'UART
                check_sum = ord(UART.read(1))

                # vérification du check_sum
                if (control ^ check_sum == 0xFF):      #on fait un ou exclusif entre le controle et le CS. S'il est nul on a tout bon
                    # check sum ok
                    # print ('     Trame recu correcte')
                    traitement_trame()
                    # vide la liste des caractères reçus
                    del liste_caracteres_recus[:]
                # remet les flags à False pour permettre la réception de la trame suivante
                flags_chaine_commencee = False
                flags_longueur = False

def raz_tableau_envoi_lora():
    #
    # remet toutes les valeurs de la liste "tableau_envoi_lora" à +99.99
    # ceci permet de savoir si un capteur n'émet plus
    #
    global nb_de_terminaux
    global nb_capteur_par_terminal
    global tableau_envoi_lora

    tableau_envoi_lora = ['+99.99'] * nb_de_terminaux*nb_capteur_par_terminal

def envoi_lora():
    #
    # A une fréquence définie par "interval_emission_lora" (en minutes)
    #   on envoie les valeurs de la liste "T" qui est une recopie de la liste "tableau_envoi_lora"
    #
    global derniere_emission_lora
    dif=(rtc.now()[4])-derniere_emission_lora
    if (dif<0):
        dif+=60

    if (dif>interval_emission_lora):
        derniere_emission_lora = rtc.now()[4]
        LORA_FREQUENCY = 868100000
        LORA_GW_DR = "SF7BW125" #DR_5
        LORA_NODE_DR = 5
        #
        # # initialize LoRa in LORAWAN mode.
        # # Please pick the region that matches where you are using the device:
        # # Asia = LoRa.AS923
        # # Australia = LoRa.AU915
        Europe = LoRa.EU868
        # # # United States = LoRa.US915
        lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
        # # # create an OTA authentication params
        dev_eui = ubinascii.hexlify(lora.mac(),":")
        print(dev_eui)
        app_eui = ubinascii.unhexlify('6a65737569736c61')
        app_key = ubinascii.unhexlify('A1B46FE2B456D666E778A2ABBFAECD00')
        # # # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
        # #
        # # # join a network using OTAA
        lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key), timeout=0)
        # # # wait until the module has joined the network
        while not lora.has_joined():
             time.sleep(5)
             print('Not joined yet...')
        print("Joined")
        # #
        # # # remove all the non-default channels
        # # # create a LoRa socket
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        # # # set the LoRaWAN data rate
        # s.setsockopt(socket.SOL_LORA, socket.SO_DR, LORA_NODE_DR)
        # # # make the socket blocking
        s.setblocking(True)
        print ('Emission du tableau LoRa :',T)
        s.send(T)
        # pycom.rgbled(0xff00)
        #time.sleep(2)
        raz_tableau_envoi_lora()

# effacement du tableau des valeurs à envoyer en LoRa
raz_tableau_envoi_lora()
