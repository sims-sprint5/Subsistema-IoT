# Subsistema-IoT

## Diagrama subsistema

<img width="1403" height="632" alt="image" src="https://github.com/user-attachments/assets/f330616b-e0ee-4321-bbd2-e3339ab37bc5" />


---

## Model de dades



---

## Funcionalitats del subsistema IoT

- Recollida de la posició dels vehicles.
- Habilitar / Deshabilitar sistema d'arranc del vehicle a través del actuador.

ALTRES POSSIBLES FUNCIONALITATS

- Recollida d'imatge amb càmera.
- Detecció de proximitat amb sensor de proximitat.

---


## Actuador ON/OFF

En aquesta part del projecte tindrem un mòdul d'alimentació connectat a una pila que simularà la connexió amb la bateria del vehicle. Aquest mòdul alimentarà el sensor de Relé.

La raspberry enviarà la senyal ON/OFF al relé.

Per simular el sistema d'arranc del vehicle connectarem un botó al relé i si passa la corrent el led s'engegarà.

---

 ## Coses que necesitem demanar

 - Sensor GPS
 - Mòdul de Relé que soporte 10 A.

---


 ## Sensor GPS

 Ja que en una situació real, la SIM de les raspberry no es pot comunicar amb el nostre software al estar en xarxes diferents (Ja que el router de la companyia bloqueja aquestes comunicacions), utilitzarem cloudflare tunnel per a forçar aquestes comunicacions.

---


## Evolució del projecte

### Actuador

Aquests son els components que utilitzarem per crear l'actuador:

MÒDUL ALIMENTACIÓ MB102

<img src="https://github.com/user-attachments/assets/230dba04-4675-479f-89ec-66644cacaff9" width="250">


CABLE PILA -> MÒDUL ALIMENTACIÓ

<img src="https://github.com/user-attachments/assets/acb94a62-c9d6-43cb-913d-424f2243cb95" width="250">


RELÉ

<img src="https://github.com/user-attachments/assets/31478c03-d31c-4399-bbc1-37ff71c488ac" width="250">


---

## Sensor GPS

Fins ara hem utilitzar un sensor de temperatura per simular l'enviament de dades del GPS.
 
<img src="https://github.com/user-attachments/assets/dc28bb62-f148-4d9a-a74c-640afdca1672" width="350"> 

---

## Subsistema

Hem dockeritzat el microservei i hem comprovat si respon correctament.
<img src="https://github.com/user-attachments/assets/3ee63849-d0f6-4921-9e57-d05be67eefd8" width="1024"> 
<img src="https://github.com/user-attachments/assets/8e4259bc-5dab-4086-b730-5df9d75ab67c" width="1024"> 


Hem configurat un script a la raspberry per rebre les dades desde el sensor i enviar-les a la DB de MongoDB Atlas.

Execució del script:

<img src="https://github.com/user-attachments/assets/1def7280-dded-4a88-84c3-c8621debc21d" width="1024"> 


Recepció dades a la BD MongoDB Atlas:

<img src="https://github.com/user-attachments/assets/93cb58be-6d18-43a9-a4ea-e52b1e083a3c" width="1024"> 

---

## Següents pasos

- Fer que el microservei envie aquestes dades al backend del software.
- Crear una connexió entre la Raspberry i el Microservei amb Cloudflare Tunnel.
