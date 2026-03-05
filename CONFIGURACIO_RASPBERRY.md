## Configuració de la Raspberry Pi per connectar-se amb el servidor FastAPI

## 1. Iniciar el contenidor Docker amb FastAPI

Primer cal iniciar el contenidor de **Docker** on s’està executant el servidor **FastAPI**.

Es important assegurar que el contenidor està en execució abans de continuar.

---
## 2. Modificar la configuració del programa a la Raspberry Pi

A la **Raspberry Pi**, localitzarem el programa `sensor`.

Obrirem aquest programa i modificarem la variable on es defineix la **IP del servidor**.

En aquesta variable introduirrem **la IP de l’ordinador on s’està executant el servidor FastAPI**.

Exemple:

```python
SERVER_IP = "192.168.X.X"
```

A mes haurem de afegir l'enllaç del MongoDB per a que es pugi conectar en la base de dade. En el nostre cas:
```bash
MONGO_URI=mongodb+srv://llorencmoreno_db_user:2a3cDbLH3QU35kMm@rasperry.qwwwbgw.mongodb.net/raspberry?retryWrites=true&w=majority
```
## 3. Preparar l’entorn de Python

Obrirem una terminal a la Raspberry Pi i navegarem fins a la carpeta on es troba l’script de Python que executarem.

```bash
cd ruta/a/la/carpeta/del/projecte
```
## 4. Crear un entorn virtual (només la primera vegada per a crear)

Crearem un entorn virtual per gestionar les dependències del projecte:

```bash
python3 -m venv venv
```
## 5. Activar l’entorn virtual (cada vegada que treballem amb el projecte)

Activarem l’entorn virtual abans d’instal·lar les dependències:

```bash
source venv/bin/activate
```

## 6. Instal·lar les dependències del projecte (només la primera vegada o si canvien)

Instal·la totes les llibreries necessàries utilitzant el fitxer `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 7. Executar el programa 

Un cop instal·lades totes les dependències, ja pots executar l’script de Python:

```bash
python nom_del_script.py
```
