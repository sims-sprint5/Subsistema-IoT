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

### MongoDB la informació s’organitza en **col·leccions** i **documents JSON**, en lloc de taules com en bases de dades SQL.
---
# Col·leccións

## Col·lecció `lectures_gps`

Registra la posició GPS del vehicle al llarg del temps.

| Camp | Tipus | Descripció |
|-----|-----|-----|
| `_id` | ObjectId | Identificador de la lectura |
| `vehicle_id` | ObjectId | Vehicle al qual pertany la lectura |
| `latitud` | Float | Coordenada de latitud |
| `longitud` | Float | Coordenada de longitud |
| `timestamp` | Date | Moment en què es va registrar la lectura |

### Exemple de document

```json
{
  "_id": ObjectId("65f2c8c4e3a4c2f1c5a1b123"),
  "vehicle_id": ObjectId("65f2c8c4e3a4c2f1c5a1b111"),
  "latitud": 41.387015,
  "longitud": 2.170047,
  "timestamp": "2026-02-26T16:41:21Z"
}
```
## 2. Col·lecció `vehicles`

Guarda la informació dels vehicles monitoritzats pel sistema.

| Camp | Tipus | Descripció |
|-----|-----|-----|
| `_id` | ObjectId | Identificador únic del vehicle |
| `nom` | String | Nom o identificador del vehicle |
| `matricula` | String | Matrícula del vehicle |
| `model` | String | Model del vehicle |
| `timestamp` | Date | Data de registre del vehicle |

## Exemple de document

```json
{
  "_id": ObjectId("65f2c8c4e3a4c2f1c5a1b111"),
  "nom": "Vehicle Proves",
  "matricula": "1234ABC",
  "model": "Cotxe IoT",
  "timestamp": "2026-02-26T16:40:00Z"
}
```
## 3. Col·lecció `actuadors`

Guarda els actuadors instal·lats al vehicle (per exemple un relé que permet activar o desactivar dispositius).

| Camp | Tipus | Descripció |
|-----|-----|-----|
| `_id` | ObjectId | Identificador de l’actuador |
| `vehicle_id` | ObjectId | Referència al vehicle al qual pertany |
| `tipus` | String | Tipus d’actuador (rele, interruptor, etc.) |
| `estat` | String | Estat actual de l’actuador (ON / OFF) |
| `timestamp` | Date | Moment de l’últim canvi d’estat |

### Exemple de document

```json
{
  "_id": ObjectId("65f2c8c4e3a4c2f1c5a1b999"),
  "vehicle_id": ObjectId("65f2c8c4e3a4c2f1c5a1b111"),
  "tipus": "rele",
  "estat": "OFF",
  "timestamp": "2026-02-26T16:41:00Z"
}
```
## 4. Col·lecció `lectures_sensor`

Guarda les lectures dels sensors connectats al sistema IoT (per exemple temperatura o valors analògics convertits mitjançant ADC).

| Camp | Tipus | Descripció |
|-----|-----|-----|
| `_id` | ObjectId | Identificador de la lectura |
| `vehicle_id` | ObjectId | Vehicle al qual pertany la lectura |
| `adc_value` | Integer | Valor digital llegit pel convertidor ADC |
| `voltage` | Float | Voltatge mesurat pel sensor |
| `temperature_c` | Float | Temperatura en graus Celsius |
| `timestamp` | Date | Moment en què es va registrar la lectura |

## Exemple de document

```json
{
  "_id": ObjectId("65f2c8c4e3a4c2f1c5a1b555"),
  "vehicle_id": ObjectId("65f2c8c4e3a4c2f1c5a1b111"),
  "adc_value": 523,
  "voltage": 2.56,
  "temperature_c": 26.4,
  "timestamp": "2026-02-26T16:42:10Z"
}
```
