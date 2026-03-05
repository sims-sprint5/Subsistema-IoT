# Model de Dades - Actuador i Sensor GPS (MongoDB)

Aquest projecte recull dades d’un **sensor GPS** connectat a una Raspberry Pi i les envia mitjançant **Cloudflare Tunnel**. També permet controlar un **relé** que actua com a actuador.

Inicialment el sistema s’ha provat amb un **sensor de temperatura**, i les dades es guarden a una base de dades **MongoDB**.

## Tecnologies utilitzades

- Raspberry Pi
- Sensor GPS
- Relé (actuador)
- Cloudflare Tunnel
- MongoDB

---

# Components del Sistema

- Mòdul d’alimentació MB102  
- Cable pila → mòdul d’alimentació  
- Relé  
- Sensor GPS  
- Raspberry Pi  
- Cloudflare Tunnel  
- Base de dades MongoDB  
- Simulació inicial amb sensor de temperatura  

---

# Model de Dades (MongoDB)

A MongoDB la informació s’organitza en **col·leccions** i **documents JSON**, en lloc de taules com en bases de dades SQL.

## 1️⃣ Col·lecció `lectures_gps`

Registra la posició del dispositiu al llarg del temps.

### Exemple de document

```json
{
  "_id": ObjectId("65f2c8c4e3a4c2f1c5a1b123"),
  "latitud": 41.387015,
  "longitud": 2.170047,
  "timestamp": "2026-02-26T16:41:21Z",
  "actuador_id": ObjectId("65f2c8c4e3a4c2f1c5a1b999")
}
```

### Diagrama del Model (ASCII)

|     actuadors     |
|-------------------|
| _id               |
| tipus             |
| estat             |
| timestamp         |
       
|   lectures_gps    |
|-------------------|
| _id               |
| latitud           |
| longitud          |
| timestamp         |
| actuador_id       |

|  lectures_sensor  |
|-------------------|
| _id               |
| adc_value         |
| voltage           |
| temperature_c     |
| timestamp         |
