# ItineraAI

ItineraAI es una aplicación web inteligente que interpreta lenguaje natural relacionado con reservaciones hoteleras, convierte el texto en datos estructurados y predice a qué perfil de cliente (cluster) pertenece la persona usando un modelo de machine learning desplegado en AWS Lambda.

---

## Tecnologías Usadas

- **Deepseek API** – Para interpretar texto en lenguaje natural
- **FastAPI (Python)** – Para construir el backend
- **AWS Lambda** – Donde vive el modelo de predicción
- **Next.js (React + TypeScript)** – Para construir el frontend
- **Render** – Para el despliegue en la nube

---

## Estructura del Proyecto

```
ItineraAI/
├── app/                   # Componentes frontend en Next.js App Router
├── models/                # Carpeta con el modelo y el preprocesado de datos
├── data/                  # Diccionarios de traducción (JSON)
├── styles/                # Estilos globales (Tailwind CSS)
├── api.py                 # Backend en FastAPI (puente entre frontend y Lambda)
├── .env.local             # Variables de entorno (crear manualmente)
├── public/                # Recursos estáticos
├── README.md              # Este archivo
└── package.json           # Configuración y dependencias del frontend
```

---

## Requisitos Previos

Antes de iniciar, asegúrate de tener:

- Node.js >= 16
- Python >= 3.8
- pip + virtualenv
- Cuenta en [Render](https://render.com)
- Claves de API para:
  - Deepseek
  - URL pública de AWS Lambda con tu modelo
  - URL pública de la API montada en render.com

---

## Instalación Local (Desarrollo)

### 1. Clona el repositorio

```bash
git clone https://github.com/abrahamlicona/ItineraAI.git
cd ItineraAI
```

---

### 2. Configura las variables de entorno

Crea un archivo `.env.local` en la raíz del proyecto con el siguiente contenido:

```env
# Para el frontend
NEXT_PUBLIC_API_URL=https://itineraai-backend.onrender.com

# Para el backend (usado dentro de api.py)
DEEPSEEK_API_KEY=sk-xxxx
LAMBDA_URL=https://xxx.lambda-url.us-east-2.on.aws/
```

---

### 3. Instala las dependencias

#### Backend (Python)

```bash
pip install -r requirements.txt
```

#### Frontend (Next.js)

```bash
npm install
```

---

## Ejecutar en Desarrollo

### Backend (FastAPI)

```bash
uvicorn api:app --reload
# Servirá en http://localhost:8000
```

### Frontend (Next.js)

```bash
npm run dev
# Servirá en http://localhost:3000
```

---

## Despliegue en Producción

### 1. Despliegue del Backend en Render

1. Entra a [render.com](https://render.com)
2. Crea un nuevo servicio "Web Service"
3. Elige el repositorio y selecciona:
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port 10000`
   - **Python build:** usa `requirements.txt`
4. Configura las variables de entorno:
   - `DEEPSEEK_API_KEY`
   - `LAMBDA_URL`
   - `PORT` → `10000`

> El backend estará disponible en una URL como `https://itineraai-backend.onrender.com`

---

### 2. Despliegue del Frontend en Render

- Render:

  1. Crea otro Web Service para el frontend.
  2. Usa `npm run build && npm start` como comando de inicio.
  3. Variables de entorno:
     - `NEXT_PUBLIC_API_URL=https://itineraai-backend.onrender.com`

---

## Cómo Funciona

1. El usuario escribe en lenguaje natural una solicitud (ej. "El cliente hizo una reserva para 2 adultos por 3 noches").
2. El frontend envía este mensaje al backend (`/api/process`).
3. El backend construye un prompt con los diccionarios TCA + reglas de validación y llama a Deepseek.
4. Deepseek estructura el texto en un JSON con los campos requeridos.
5. Este JSON se envía a AWS Lambda.
6. Lambda devuelve el cluster al que pertenece el cliente.
7. El backend interpreta el resultado y genera una explicación.
8. El frontend muestra el mensaje final al usuario con la predicción y su razonamiento.

---

## Pruebas

Puedes probar el frontend directamente en:  
**https://itinerai-b7e1.onrender.com**

Y el backend en:  
**https://itineraai-backend.onrender.com/api/process**

Usa `curl` si deseas probar manualmente:

```bash
curl --ssl-no-revoke -i -X POST "https://vfr76hdfy6orj34fdgcpgfnyfa0ibrbo.lambda-url.us-east-2.on.aws/" -H "Content-Type: application/json" -d "{\"h_num_per\":2,\"h_num_adu\":2,\"h_num_men\":0,\"h_num_noc\":3,\"h_tot_hab\":1,\"h_tfa_total\":1200,\"ID_Tipo_Habitacion\":25,\"ID_canal\":10,\"ID_Pais_Origen\":157,\"ID_Segmento_Comp\":14,\"ID_Agencia\":112}"
```

---

## Notas Técnicas

- El archivo `api.py` controla todo el flujo backend:

  - Carga diccionarios de datos (`/data/*.json`)
  - Construye prompts personalizados para Deepseek
  - Verifica campos obligatorios
  - Llama al modelo en Lambda
  - Formatea una respuesta explicativa

- El frontend (`app/page.tsx`) es un chat UI tipo WhatsApp con auto-scroll y cancelación de peticiones.

---

## Aviso Legal

Este recurso es propiedad exclusiva del **Equipo 5**.  
Queda **estrictamente prohibido su uso en producción sin consentimiento escrito o pago de regalías**.  
El uso no autorizado podrá derivar en **acciones legales** por parte del equipo titular del proyecto.

---

## Autores

**Abraham Licona** [github.com/abrahamlicona](https://github.com/abrahamlicona)

**Sabrina Carselle** [github.com/sabrinacarselle](https://github.com/sabrinacarselle)

**Juan Pablo Sada**

**Andres Morones**

**Juan Pablo Ramirez**


Asistente IA para reservas hoteleras
