
# Model de Dades - Actuador i Sensor GPS

Aquest projecte recull dades d’un **sensor GPS** connectat a una Raspberry i les envia mitjançant **Cloudflare Tunnel**. També es pot controlar un **relé** com actuador.

## Components

- Mòdul d’alimentació MB102  
- Cable pila → mòdul d’alimentació  
- Relé  
- Sensor GPS  
- Cloudflare Tunnel  
- Simulació inicial amb sensor de temperatura  

## Taules del Model de Dades

### 1️⃣ Lectures GPS

Registra la posició del GPS al llarg del temps.

| Camp        | Tipus          | Descripció                               |
|------------|---------------|-----------------------------------------|
| id_lectura | INT PK        | Clau primària auto_incremental          |
| latitud    | DECIMAL(10,7) | Latitud del dispositiu                   |
| longitud   | DECIMAL(10,7) | Longitud del dispositiu                  |
| data_hora  | DATETIME      | Moment de la lectura                     |

### 2️⃣ Actuador

Registra l’estat dels relés o altres actuadors.

| Camp         | Tipus        | Descripció                     |
|-------------|-------------|--------------------------------|
| id_actuador | INT PK      | Clau primària                  |
| tipus       | VARCHAR(50) | Tipus d’actuador (ex: relé)   |
| estat       | TINYINT     | 0 = apagat, 1 = encès         |
| data_hora   | DATETIME    | Moment de l’últim canvi       |

## Relacions

- Un actuador pot tenir moltes lectures associades.  
- Cada lectura pertany a un actuador (opcional si només es recullen GPS).  

## Exemple de SQL MariaDB

```sql
CREATE TABLE actuador (
    id_actuador INT AUTO_INCREMENT PRIMARY KEY,
    tipus VARCHAR(50),
    estat TINYINT,
    data_hora DATETIME
);

CREATE TABLE lectura_gps (
    id_lectura INT AUTO_INCREMENT PRIMARY KEY,
    latitud DECIMAL(10,7) NOT NULL,
    longitud DECIMAL(10,7) NOT NULL,
    data_hora DATETIME NOT NULL,
    id_actuador INT,
    FOREIGN KEY (id_actuador) REFERENCES actuador(id_actuador)
);

## Diagrama ASCII del Model

+-------------+                +-------------+
|  Actuador   |----------------|  Lectura    |
|-------------|                |    GPS      |
| id_actuador |                | id_lectura  |
| tipus       |                | latitud     |
| estat       |                | longitud    |
| data_hora   |                | data_hora   |
+-------------+                | id_actuador |
                               +-------------+
