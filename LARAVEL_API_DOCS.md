# API de Temperatura IoT — Documentación para Laravel

## Información de conexión

| Campo    | Valor                                                    |
| -------- | -------------------------------------------------------- |
| Base URL | `http://IP-DEL-SERVIDOR:8008`                            |
| Auth     | Header `X-API-Key` en **todas** las peticiones           |
| API Key  | La misma definida en `.env` → `API_KEY`                  |
| Formato  | JSON (`Content-Type: application/json`)                  |
| Docs     | Swagger UI en `http://IP-DEL-SERVIDOR:8008/docs`         |

---

## Configuración en Laravel

### .env de Laravel

```env
IOT_API_URL=http://IP-DEL-SERVIDOR:8008
IOT_API_KEY=mi-api-key-secreta-cambiar-en-produccion
```

### config/services.php

```php
'iot_api' => [
    'url' => env('IOT_API_URL', 'http://localhost:8008'),
    'key' => env('IOT_API_KEY', ''),
],
```

### Ejemplo de Service (app/Services/IoTApiService.php)

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class IoTApiService
{
    protected string $baseUrl;
    protected string $apiKey;

    public function __construct()
    {
        $this->baseUrl = config('services.iot_api.url');
        $this->apiKey = config('services.iot_api.key');
    }

    protected function request()
    {
        return Http::baseUrl($this->baseUrl)
            ->withHeaders(['X-API-Key' => $this->apiKey])
            ->acceptJson();
    }

    // Ver ejemplos de cada endpoint más abajo
}
```

---

## Endpoints disponibles

### 1. Listado paginado de temperaturas

```
GET /api/laravel/temperatures
```

**Query params:**

| Param        | Tipo     | Default | Descripción                        |
| ------------ | -------- | ------- | ---------------------------------- |
| `page`       | int      | 1       | Número de página (mínimo 1)        |
| `per_page`   | int      | 20      | Resultados por página (1-100)      |
| `start_date` | datetime | null    | Filtrar desde fecha (ISO 8601)     |
| `end_date`   | datetime | null    | Filtrar hasta fecha (ISO 8601)     |

**Respuesta (200):**

```json
{
    "total": 150,
    "page": 1,
    "per_page": 20,
    "data": [
        {
            "_id": "69a08b65a708e1e29d57f219",
            "adc_value": 128,
            "voltage": 1.65,
            "temperature_c": 25.5,
            "timestamp": "2026-02-26T10:30:00Z"
        }
    ]
}
```

**Laravel:**

```php
// Todas las lecturas (paginadas)
$response = $this->request()->get('/api/laravel/temperatures', [
    'page' => 1,
    'per_page' => 20,
]);

// Filtrado por rango de fechas
$response = $this->request()->get('/api/laravel/temperatures', [
    'page' => 1,
    'per_page' => 50,
    'start_date' => '2026-02-26T00:00:00Z',
    'end_date' => '2026-02-26T23:59:59Z',
]);

$data = $response->json();
// $data['total'], $data['page'], $data['per_page'], $data['data']
```

---

### 2. Última lectura de temperatura

```
GET /api/laravel/temperatures/latest
```

**Sin parámetros.**

**Respuesta (200):**

```json
{
    "_id": "69a08b65a708e1e29d57f219",
    "adc_value": 128,
    "voltage": 1.65,
    "temperature_c": 25.5,
    "timestamp": "2026-02-26T10:30:00Z"
}
```

**Laravel:**

```php
$response = $this->request()->get('/api/laravel/temperatures/latest');
$latest = $response->json();
// $latest['temperature_c'], $latest['timestamp'], etc.
```

---

### 3. Lectura por ID

```
GET /api/laravel/temperatures/{id}
```

**Path params:**

| Param | Tipo   | Descripción         |
| ----- | ------ | ------------------- |
| `id`  | string | ObjectId de MongoDB |

**Respuesta (200):**

```json
{
    "_id": "69a08b65a708e1e29d57f219",
    "adc_value": 128,
    "voltage": 1.65,
    "temperature_c": 25.5,
    "timestamp": "2026-02-26T10:30:00Z"
}
```

**Laravel:**

```php
$id = '69a08b65a708e1e29d57f219';
$response = $this->request()->get("/api/laravel/temperatures/{$id}");
$reading = $response->json();
```

---

### 4. Estadísticas (para dashboards)

```
GET /api/laravel/temperatures/stats/summary
```

**Query params:**

| Param        | Tipo     | Default | Descripción                    |
| ------------ | -------- | ------- | ------------------------------ |
| `start_date` | datetime | null    | Filtrar desde fecha (ISO 8601) |
| `end_date`   | datetime | null    | Filtrar hasta fecha (ISO 8601) |

**Respuesta (200):**

```json
{
    "count": 150,
    "avg_temperature": 24.35,
    "min_temperature": 18.20,
    "max_temperature": 32.10,
    "last_reading": {
        "_id": "69a08b65a708e1e29d57f219",
        "adc_value": 128,
        "voltage": 1.65,
        "temperature_c": 25.5,
        "timestamp": "2026-02-26T10:30:00Z"
    }
}
```

**Laravel:**

```php
// Stats generales
$response = $this->request()->get('/api/laravel/temperatures/stats/summary');

// Stats de un día específico
$response = $this->request()->get('/api/laravel/temperatures/stats/summary', [
    'start_date' => '2026-02-26T00:00:00Z',
    'end_date' => '2026-02-26T23:59:59Z',
]);

$stats = $response->json();
// $stats['count'], $stats['avg_temperature'], $stats['min_temperature'],
// $stats['max_temperature'], $stats['last_reading']
```

---

### 5. Eliminar lecturas por rango de fechas

```
DELETE /api/laravel/temperatures
```

**Query params (al menos uno obligatorio):**

| Param        | Tipo     | Descripción                    |
| ------------ | -------- | ------------------------------ |
| `start_date` | datetime | Eliminar desde fecha (ISO 8601)|
| `end_date`   | datetime | Eliminar hasta fecha (ISO 8601)|

**Respuesta (200):**

```json
{
    "message": "15 lecturas eliminadas",
    "status": "ok"
}
```

**Laravel:**

```php
$response = $this->request()->delete('/api/laravel/temperatures', [
    'start_date' => '2026-01-01T00:00:00Z',
    'end_date' => '2026-01-31T23:59:59Z',
]);
```

---

## Health check

```
GET /
```

Respuesta: `{"status": "ok", "service": "Subsistema IoT API"}`

```
GET /health
```

Respuesta: `{"status": "ok", "mongodb": "connected"}`

---

## Códigos de error

| Código | Significado                                   |
| ------ | --------------------------------------------- |
| 200    | OK                                            |
| 400    | Parámetros inválidos (ej: ID mal formado)     |
| 401    | API Key inválida o no enviada                 |
| 404    | Recurso no encontrado                         |
| 503    | Base de datos no disponible                   |

**Formato de error:**

```json
{
    "detail": "API Key inválida o no proporcionada"
}
```

---

## Probar con curl

```bash
# Health check
curl http://IP:8008/

# Listar temperaturas
curl -H "X-API-Key: TU_API_KEY" "http://IP:8008/api/laravel/temperatures?page=1&per_page=10"

# Última lectura
curl -H "X-API-Key: TU_API_KEY" "http://IP:8008/api/laravel/temperatures/latest"

# Estadísticas
curl -H "X-API-Key: TU_API_KEY" "http://IP:8008/api/laravel/temperatures/stats/summary"
```
