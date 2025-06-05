from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union, Any

# Cargar variables de entorno
load_dotenv()
print("[DEBUG] Entorno completo desde Netlify:")
for key in ["DEEPSEEK_API_KEY", "LAMBDA_URL"]:
    print(f"{key}: {os.getenv(key)}")

# Verificar si la API key está cargada
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("[ERROR] DEEPSEEK_API_KEY no está configurada en el archivo .env")
else:
    print("[DEBUG] API Key cargada correctamente (primeros 4 caracteres):", api_key[:4] + "..." if api_key else "No disponible")

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar los diccionarios JSON
def load_json_file(filename: str) -> Dict:
    with open(f"data/{filename}", "r", encoding="utf-8") as f:
        data = json.load(f)
        print(f"[DEBUG] Estructura de {filename}:", json.dumps(data[:2], indent=2))
        return data

# Cargar todos los diccionarios
agencias_dict = load_json_file("TCA_iar_Agencias.json")
canales_dict = load_json_file("TCA_iar_canales.json")
paises_dict = load_json_file("TCA_iar_Paises_origen.json")
segmentos_dict = load_json_file("TCA_iar_Segmentos_Comp.json")
tipos_habitacion_dict = load_json_file("TCA_iar_Tipos_Habitaciones.json")

def get_descriptive_value(dictionary: Union[Dict, List], id_value: Union[int, str]) -> str:
    """
    Convierte un ID a su valor descriptivo usando el diccionario o lista correspondiente.
    Si no se encuentra el valor, devuelve el ID como string.
    """
    try:
        # Convertir el ID de entrada a string para comparación
        id_value_str = str(id_value)
        if isinstance(dictionary, list):
            # Si es una lista, buscamos el elemento que tenga el ID
            for item in dictionary:
                if isinstance(item, dict):
                    # Intentar diferentes posibles claves para el ID según el tipo de diccionario
                    if 'ID_Tipo_Habitacion' in item:
                        if str(item['ID_Tipo_Habitacion']) == id_value_str:
                            return item.get('Tipo_Habitacion_nombre', id_value_str)
                    elif 'ID_canal' in item:
                        if str(item['ID_canal']) == id_value_str:
                            return item.get('CANAL', id_value_str)
                    elif 'ID_Segmento_Comp' in item:
                        if str(item['ID_Segmento_Comp']) == id_value_str:
                            return item.get('SEGMENTO ALTERNO', id_value_str)
                    elif 'ID_Agencia' in item:
                        if str(item['ID_Agencia']) == id_value_str:
                            return item.get('NOMBRE', id_value_str)
                    elif 'id' in item or 'ID' in item or 'Id' in item:
                        item_id = item.get('id') or item.get('ID') or item.get('Id')
                        if str(item_id) == id_value_str:
                            return item.get('name') or item.get('Name') or item.get('NOMBRE') or item.get('DESCRIPCION') or id_value_str
        else:
            # Si es un diccionario, buscamos la clave que tenga el valor
            for key, value in dictionary.items():
                if str(value) == id_value_str:
                    return key
    except (ValueError, TypeError) as e:
        print(f"[DEBUG] Error al convertir ID {id_value}: {str(e)}")
    return str(id_value)

def get_reservation_description(reservation_data: Dict) -> Dict:
    """
    Convierte los IDs de la reserva a valores descriptivos.
    """
    try:
        return {
            "h_num_per": reservation_data.get("h_num_per"),
            "h_num_adu": reservation_data.get("h_num_adu"),
            "h_num_men": reservation_data.get("h_num_men"),
            "h_num_noc": reservation_data.get("h_num_noc"),
            "h_tot_hab": reservation_data.get("h_tot_hab"),
            "h_tfa_total": reservation_data.get("h_tfa_total"),
            "tipo_habitacion": get_descriptive_value(tipos_habitacion_dict, reservation_data.get("ID_Tipo_Habitacion")),
            "canal": get_descriptive_value(canales_dict, reservation_data.get("ID_canal")),
            "pais_origen": get_descriptive_value(paises_dict, reservation_data.get("ID_Pais_Origen")),
            "segmento": get_descriptive_value(segmentos_dict, reservation_data.get("ID_Segmento_Comp")),
            "agencia": get_descriptive_value(agencias_dict, reservation_data.get("ID_Agencia"))
        }
    except Exception as e:
        print(f"[DEBUG] Error al obtener descripción de reserva: {str(e)}")
        print(f"[DEBUG] Datos de reserva: {json.dumps(reservation_data, indent=2)}")
        # En caso de error, devolver los datos originales
        return {
            "h_num_per": reservation_data.get("h_num_per"),
            "h_num_adu": reservation_data.get("h_num_adu"),
            "h_num_men": reservation_data.get("h_num_men"),
            "h_num_noc": reservation_data.get("h_num_noc"),
            "h_tot_hab": reservation_data.get("h_tot_hab"),
            "h_tfa_total": reservation_data.get("h_tfa_total"),
            "tipo_habitacion": f"ID {reservation_data.get('ID_Tipo_Habitacion')}",
            "canal": f"ID {reservation_data.get('ID_canal')}",
            "pais_origen": f"ID {reservation_data.get('ID_Pais_Origen')}",
            "segmento": f"ID {reservation_data.get('ID_Segmento_Comp')}",
            "agencia": f"ID {reservation_data.get('ID_Agencia')}"
        }

# Definir descripciones de clusters
CLUSTER_DESCRIPTIONS = {
    0: {
        "name": "Viajeros frecuentes y leales",
        "description": """
        Perfil: Reservas de una o dos personas con estadías prolongadas (alrededor de 7 noches)
        Características: 1 habitación, canal DIRECTO o INTERNET, agencias PARTICULAR o BOOKING.COM
        Habitación típica: LUXURY 2Q
        Segmento: INDIVIDUAL BUSINESS/LOYALTY
        Perfil típico: viajeros frecuentes que ya conocen el hotel o clientes con programas de lealtad
        """
    },
    1: {
        "name": "Clientes de negocios premium",
        "description": """
        Perfil: Reservas de 1-2 personas con estadías cortas (2-3 noches) y tarifas altas
        Características: canales SITIO PROPIO o agencias especializadas (BTC, CORAD, BOOKING.COM)
        Habitaciones típicas: SUITE PRESIDENCIAL, MASTER SUITE, JR SUITE
        Segmento: GRO. & CONV. MEETINGS o INCENTIVE SOC.
        Perfil típico: asistentes a eventos, convenciones o clientes de negocios premium
        """
    },
    2: {
        "name": "Grupos y familias",
        "description": """
        Perfil: Grupos o familias de 3-5 personas con 2 habitaciones
        Características: estadías de 4-6 noches, tarifas medias, agencias BESTDAY, APPLE VACATIONS, CHEAP CARIBBEAN
        Canales: MULTIVACACIONES
        Habitaciones típicas: JR SUITE, LUXURY 2Q SB
        Segmento: TOUR OPERATORS DOMESTIC/INTERNATIONALS
        Perfil típico: familias o grupos turísticos organizados por agencias
        """
    },
    3: {
        "name": "Parejas y celebraciones",
        "description": """
        Perfil: Dos personas buscando experiencias especiales
        Características: estancias medias (3-5 noches)
        Habitaciones típicas: HONEYMOON, MASTER SUITE
        Canales: INTERNET, DIRECTO HOTEL, PARTICULAR
        Segmento: INDIVIDUAL LEISURE/PACKAGE
        Perfil típico: parejas en plan vacacional o celebración personal
        """
    },
    4: {
        "name": "Familias con niños",
        "description": """
        Perfil: Reservas para familias con niños, típicamente 2 personas (1 adulto y 1 menor)
        Características: estadías cortas (2-3 noches), múltiples habitaciones
        Canales: INTERNET, agencias como BESTDAY TRAVEL GROUP
        Habitaciones típicas: ESTD S/REAL
        Segmento: INDIVIDUAL EP/VAC. CLUB
        Perfil típico: familias que buscan comodidad y espacio para sus hijos
        """
    }
}

class UserMessage(BaseModel):
    userMessage: str

class ClusterPrediction(BaseModel):
    message: str
    clusters: List[int]
    explanation: str

class PredictionResponse(BaseModel):
    prediction: Dict[str, Any]

@app.post("/api/process", response_model=PredictionResponse)
async def process_message(message: UserMessage):
    try:
        print("[DEBUG] Mensaje recibido:", message.userMessage)
        # Verificar API key antes de hacer la llamada
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key no configurada")
        
        # Construir el prompt para Deepseek
        prompt = f"""
Eres un modelo LLM especializado en reservas hoteleras y predicciones de clúster.
Debes seguir estas reglas de conversación:

1. Consultas sobre clusters:
   - Si el usuario pregunta sobre un cluster específico (ej: "qué es el cluster 1?"), responde con la descripción completa del cluster.
   - Si el usuario pregunta "qué son los clusters?", explica brevemente el sistema de clusters y lista los 5 tipos.
   - NO devuelvas campos faltantes en estos casos, solo responde la información solicitada.

2. Saludos y cortesía:
   - Si el usuario te saluda (ej: hola, buenos días, cómo estás), responde de manera amigable y breve.
   - Si el usuario te agradece o se despide, responde de manera cortés.
   - Si el usuario pregunta cómo estás, responde que estás bien y listo para ayudarle con su reserva.
   - NO devuelvas campos faltantes en estos casos, solo responde el saludo o agradecimiento.

3. Temas no relacionados:
   - Si el usuario pregunta algo que NO sea sobre reservas hoteleras, predicciones o los campos requeridos, responde: "Lo siento, solo puedo ayudarte con temas de reservas hoteleras y predicciones. ¿En qué puedo ayudarte con tu reserva?"

4. Reservas:
   - SOLO si el usuario describe una reserva, sigue las instrucciones para extraer los campos y devolver el JSON.
   - Si el país de origen NO es México, devuelve un mensaje de error: "Lo siento, solo puedo hacer predicciones para clientes mexicanos."
   - Si faltan campos, devuelve un objeto {{"missing": [ ... ]}}.

Campos obligatorios para reservas:
- h_num_per
- h_num_adu
- h_num_men
- h_num_noc
- h_tot_hab
- h_tfa_total
- ID_Tipo_Habitacion
- ID_canal
- ID_Pais_Origen
- ID_Segmento_Comp
- ID_Agencia

IMPORTANTE: Usa SOLO los valores exactos de los diccionarios. NO hagas suposiciones ni interpretaciones.

Diccionarios (normalized key → ID):
AgenciasDict = {json.dumps(agencias_dict)};
CanalesDict = {json.dumps(canales_dict)};
PaisesOrigenDict = {json.dumps(paises_dict)};
SegmentosCompDict = {json.dumps(segmentos_dict)};
TiposHabitacionDict = {json.dumps(tipos_habitacion_dict)};

Reglas para campos:
1. Para el campo "ID_Pais_Origen":
   - Si el país NO es México, devuelve el mensaje de error: "Lo siento, solo puedo hacer predicciones para clientes mexicanos."
   - Si el país es México, usa el ID 157.
   - Si no se especifica el país, considera que falta este campo.

2. Para el campo "ID_Tipo_Habitacion":
   - Si detectas un valor de texto, normalízalo y búscalo en TiposHabitacionDict.
   - Si el usuario escribe directamente un número que coincide con uno de los valores en TiposHabitacionDict, entonces úsalo tal cual.
   - Si no coincide ni con un nombre ni con un ID válido del diccionario, considera que falta este campo.

3. Para los campos "ID_canal", "ID_Segmento_Comp" y "ID_Agencia":
   - Aplica la misma lógica de normalización y búsqueda en sus respectivos diccionarios.
   - Usa SOLO los valores exactos del diccionario, NO hagas suposiciones.

4. Convierte números literales a sus respectivos campos.

5. Si falta algún campo, devuelve {{ "missing": ["h_tfa_total", ...] }}.

6. Devuelve **solo** el JSON bien formado, sin texto adicional ni explicaciones.

7. Tu nombre es "Abraham Licona" y eres un asistente de reservas hoteleras.

IMPORTANTE: 
- Solo devuelve JSON cuando el usuario describe una reserva.
- Para saludos, agradecimientos y otros mensajes, responde con texto normal.
- Si el país NO es México, devuelve el mensaje de error: "Lo siento, solo puedo hacer predicciones para clientes mexicanos."
- Usa SOLO los valores exactos de los diccionarios. NO hagas suposiciones ni interpretaciones.

Mensaje de usuario:
{message.userMessage}
"""
        
        # Llamar a Deepseek
        async with httpx.AsyncClient() as client:
            print("[DEBUG] Preparando llamada a Deepseek...")
            print("[DEBUG] URL:", "https://api.deepseek.com/v1/chat/completions")
            print("[DEBUG] Headers:", {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key[:4]}..."  # Solo mostramos los primeros 4 caracteres por seguridad
            })
            
            try:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0,
                        "top_p": 1.0,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                    },
                    timeout=30.0
                )
                print("[DEBUG] Status Deepseek:", response.status_code)
                print("[DEBUG] Respuesta cruda Deepseek:", response.text)
                
                if response.status_code != 200:
                    error_detail = f"Error al llamar a Deepseek. Status: {response.status_code}, Response: {response.text}"
                    print(f"[ERROR] {error_detail}")
                    raise HTTPException(status_code=500, detail=error_detail)

                # Procesar la respuesta de Deepseek
                deepseek_response = response.json()
                try:
                    raw_text = deepseek_response["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    print("[DEBUG] Error accediendo a choices/text en respuesta Deepseek:", deepseek_response)
                    raise e

                print("[DEBUG] Texto crudo extraído:", raw_text)
                
                # Limpiar la respuesta de Deepseek
                def clean_json_response(text):
                    # Eliminar los marcadores de código markdown si existen
                    if text.startswith("```json"):
                        text = text[7:]  # Eliminar ```json
                    if text.startswith("```"):
                        text = text[3:]  # Eliminar ```
                    if text.endswith("```"):
                        text = text[:-3]  # Eliminar ```
                    # Eliminar cualquier espacio en blanco al inicio y final
                    text = text.strip()
                    # Asegurarse de que el texto comienza con { y termina con }
                    if not text.startswith("{"):
                        text = "{" + text
                    if not text.endswith("}"):
                        text = text + "}"
                    return text
                
                cleaned_text = clean_json_response(raw_text)
                print("[DEBUG] Texto limpio:", cleaned_text)
                
                # Intentar parsear como JSON, si falla, tratar como texto normal
                try:
                    parsed = json.loads(cleaned_text)
                    print("[DEBUG] JSON parseado:", parsed)
                    
                    # Si es un mensaje de error o campos faltantes, devolverlo directamente
                    if "missing" in parsed:
                        print("[DEBUG] Faltan campos:", parsed["missing"])
                        return {"prediction": {
                            "message": f"Faltan los siguientes campos: {', '.join(parsed['missing'])}",
                            "clusters": [],
                            "explanation": "",
                            "status": "error"
                        }}
                    
                    # Validar campos requeridos
                    required_fields = [
                        "h_num_per",
                        "h_num_adu",
                        "h_num_men",
                        "h_num_noc",
                        "h_tot_hab",
                        "h_tfa_total",
                        "ID_Tipo_Habitacion",
                        "ID_canal",
                        "ID_Pais_Origen",
                        "ID_Segmento_Comp",
                        "ID_Agencia",
                    ]
                    missing_fields = [
                        field for field in required_fields
                        if field not in parsed or parsed[field] is None
                    ]
                    if missing_fields:
                        print("[DEBUG] Faltan campos tras validación:", missing_fields)
                        return {"prediction": {
                            "message": f"Faltan los siguientes campos: {', '.join(missing_fields)}",
                            "clusters": [],
                            "explanation": "",
                            "status": "error"
                        }}
                    
                    # Convertir IDs a enteros y asegurar que sean números válidos
                    try:
                        parsed["h_num_per"] = int(parsed["h_num_per"])
                        parsed["h_num_adu"] = int(parsed["h_num_adu"])
                        parsed["h_num_men"] = int(parsed["h_num_men"])
                        parsed["h_num_noc"] = int(parsed["h_num_noc"])
                        parsed["h_tot_hab"] = int(parsed["h_tot_hab"])
                        parsed["h_tfa_total"] = float(parsed["h_tfa_total"])
                        parsed["ID_Tipo_Habitacion"] = int(parsed["ID_Tipo_Habitacion"])
                        parsed["ID_canal"] = int(parsed["ID_canal"])
                        parsed["ID_Pais_Origen"] = int(parsed["ID_Pais_Origen"])
                        parsed["ID_Segmento_Comp"] = int(parsed["ID_Segmento_Comp"])
                        parsed["ID_Agencia"] = int(parsed["ID_Agencia"])
                    except (ValueError, TypeError) as e:
                        print(f"[DEBUG] Error al convertir valores: {str(e)}")
                        return {"prediction": {
                            "message": f"Error en el formato de los datos: {str(e)}",
                            "clusters": [],
                            "explanation": "",
                            "status": "error"
                        }}
                    
                    # Si llegamos aquí, es un JSON válido con todos los campos
                    print("[DEBUG] Preparando llamada a Lambda...")
                    print("[DEBUG] Lambda URL:", os.getenv("LAMBDA_URL"))
                    print("[DEBUG] Datos a enviar a Lambda:", json.dumps(parsed, indent=2))
                    
                    try:
                        lambda_response = await client.post(
                            os.getenv("LAMBDA_URL"),
                            json=parsed,
                            headers={"Content-Type": "application/json"},
                            timeout=30.0
                        )
                        print("[DEBUG] Status Lambda:", lambda_response.status_code)
                        print("[DEBUG] Respuesta Lambda:", lambda_response.text)
                        
                        if lambda_response.status_code != 200:
                            error_detail = f"Error al llamar a Lambda. Status: {lambda_response.status_code}, Response: {lambda_response.text}"
                            print(f"[ERROR] {error_detail}")
                            raise HTTPException(status_code=500, detail=error_detail)
                        
                        lambda_data = lambda_response.json()
                        print("[DEBUG] Datos Lambda parseados:", lambda_data)
                        
                        # Formatear la respuesta para que sea amigable con React
                        if "clusters" in lambda_data:
                            cluster_info = lambda_data["clusters"]
                            if isinstance(cluster_info, list):
                                cluster_id = cluster_info[0]
                            else:
                                cluster_id = cluster_info

                            # Verificar si el cluster existe en nuestras descripciones
                            if cluster_id not in CLUSTER_DESCRIPTIONS:
                                return {"prediction": {
                                    "message": f"La predicción del cluster es: {cluster_id}",
                                    "clusters": [cluster_id] if isinstance(cluster_id, int) else cluster_info,
                                    "explanation": f"Este es un nuevo cluster ({cluster_id}) que aún no tiene una descripción detallada. Analizando el perfil de la reserva...",
                                    "status": "success"
                                }}

                            # Llamar a Deepseek para analizar el perfil
                            reservation_description = get_reservation_description(parsed)
                            analysis_prompt = f"""
Analiza brevemente por qué la siguiente reserva coincide con el cluster {cluster_id}.
Máximo 3 párrafos cortos. Enfócate en las coincidencias más importantes.
Usa SOLO los valores exactos de los diccionarios. NO hagas suposiciones ni interpretaciones.

Datos de la reserva:
- Número total de personas: {reservation_description['h_num_per']}
- Adultos: {reservation_description['h_num_adu']}
- Menores: {reservation_description['h_num_men']}
- Noches de estancia: {reservation_description['h_num_noc']}
- Número de habitaciones: {reservation_description['h_tot_hab']}
- Tarifa total: ${reservation_description['h_tfa_total']}
- Tipo de habitación: {reservation_description['tipo_habitacion']}
- Canal de reserva: {reservation_description['canal']}
- País de origen: {reservation_description['pais_origen']}
- Segmento: {reservation_description['segmento']}
- Agencia: {reservation_description['agencia']}

Descripción del cluster {cluster_id}:
{CLUSTER_DESCRIPTIONS[cluster_id]['description']}

Proporciona un análisis conciso de por qué esta reserva coincide con este cluster.
Usa SOLO los valores exactos proporcionados. NO hagas suposiciones ni interpretaciones.
"""
                            try:
                                analysis_response = await client.post(
                                    "https://api.deepseek.com/v1/chat/completions",
                                    json={
                                        "model": "deepseek-chat",
                                        "messages": [
                                            {"role": "system", "content": analysis_prompt}
                                        ],
                                        "max_tokens": 500,
                                        "temperature": 0.7,
                                        "top_p": 1.0,
                                    },
                                    headers={
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                                    },
                                    timeout=30.0
                                )
                                
                                if analysis_response.status_code == 200:
                                    analysis_data = analysis_response.json()
                                    cluster_explanation = analysis_data["choices"][0]["message"]["content"].strip()
                                    # Limpiar la explicación de caracteres especiales y formato markdown
                                    cluster_explanation = cluster_explanation.replace("**", "").replace("*", "")
                                    # Eliminar saltos de línea múltiples y asegurar que la explicación termine correctamente
                                    cluster_explanation = " ".join(cluster_explanation.split())
                                    if not cluster_explanation.endswith("."):
                                        cluster_explanation += "."
                                else:
                                    # Si falla el análisis, generar una explicación básica
                                    cluster_explanation = f"Esta reserva coincide con el cluster {cluster_id} debido a sus características principales: {reservation_description['h_num_per']} personas, {reservation_description['h_num_noc']} noches de estancia, y segmento {reservation_description['segmento']}."
                                
                                # Asegurarnos de que la respuesta tenga exactamente el formato esperado
                                response_data = {
                                    "prediction": {
                                        "message": f"La predicción del cluster es: {cluster_id}",
                                        "clusters": [cluster_id] if isinstance(cluster_id, int) else cluster_info,
                                        "explanation": cluster_explanation.strip(),
                                        "status": "success"
                                    }
                                }
                                print("[DEBUG] Respuesta final:", json.dumps(response_data, indent=2))
                                return response_data
                            except Exception as e:
                                print(f"[ERROR] Error al generar análisis del cluster: {str(e)}")
                                # En caso de error, proporcionar una explicación básica
                                basic_explanation = f"Esta reserva coincide con el cluster {cluster_id} debido a sus características principales: {reservation_description['h_num_per']} personas, {reservation_description['h_num_noc']} noches de estancia, y segmento {reservation_description['segmento']}."
                                response_data = {
                                    "prediction": {
                                        "message": f"La predicción del cluster es: {cluster_id}",
                                        "clusters": [cluster_id] if isinstance(cluster_id, int) else cluster_info,
                                        "explanation": basic_explanation,
                                        "status": "success"
                                    }
                                }
                                print("[DEBUG] Respuesta final (error):", json.dumps(response_data, indent=2))
                                return response_data
                        else:
                            # Si no hay clusters en la respuesta de Lambda, devolver un mensaje simple
                            return {"prediction": {
                                "message": "No se pudo determinar el cluster",
                                "clusters": [],
                                "explanation": "No se pudo determinar el cluster para esta reserva.",
                                "status": "success"
                            }}
                            
                    except httpx.RequestError as e:
                        print(f"[ERROR] Error en la petición HTTP a Lambda: {str(e)}")
                        print(f"[ERROR] URL Lambda: {os.getenv('LAMBDA_URL')}")
                        raise HTTPException(status_code=500, detail=f"Error en la petición HTTP a Lambda: {str(e)}")
                    except httpx.TimeoutException as e:
                        print(f"[ERROR] Timeout en la petición a Lambda: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"Timeout en la petición a Lambda: {str(e)}")
                    except Exception as e:
                        print(f"[ERROR] Error inesperado en Lambda: {str(e)}")
                        print(f"[ERROR] Tipo de error: {type(e)}")
                        import traceback
                        print(f"[ERROR] Traceback completo:\n{traceback.format_exc()}")
                        raise HTTPException(status_code=500, detail=f"Error inesperado en Lambda: {str(e)}")
                    
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Error al decodificar JSON: {str(e)}")
                    print(f"[ERROR] Texto que causó el error: {cleaned_text}")
                    # Si no es JSON, es un mensaje de texto normal
                    return {"prediction": {
                        "message": cleaned_text,
                        "clusters": [],
                        "explanation": "",
                        "status": "success"
                    }}
            except httpx.RequestError as e:
                print(f"[ERROR] Error en la petición HTTP: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error en la petición HTTP: {str(e)}")
            except httpx.TimeoutException as e:
                print(f"[ERROR] Timeout en la petición: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Timeout en la petición: {str(e)}")
            except Exception as e:
                print(f"[ERROR] Error inesperado: {str(e)}")
                print(f"[ERROR] Tipo de error: {type(e)}")
                import traceback
                print(f"[ERROR] Traceback completo:\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    except Exception as e:
        print("[DEBUG] Excepción atrapada:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 