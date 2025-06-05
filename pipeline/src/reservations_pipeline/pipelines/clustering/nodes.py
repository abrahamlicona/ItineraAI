import pandas as pd
import numpy as np
import torch

from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import silhouette_score
from pytorch_tabnet.pretraining import TabNetPretrainer

# ---------- 1) LIMPIEZA ----------
def clean_reservations(df: pd.DataFrame) -> pd.DataFrame:
    """
    1. Selección de columnas relevantes
    2. Conversión de tipos
    3. Eliminar registros con tarifa negativa
    4. Eliminar registros con h_num_per = 0, h_num_noc = 0 y h_tot_hab = 0
    5. Limpiar outliers extremos (percentil 0.05% / 99.95%) para ciertas columnas
    6. Resetear índice y retornar df limpio
    """

    # 1. Selección de columnas relevantes ───────────────────────────────
    cols_keep = [
        "ID_Reserva", "Fecha_hoy", "h_num_per", "h_num_adu", "h_num_men",
        "h_num_noc", "h_tot_hab", "ID_Programa", "ID_empresa", "ID_Paquete",
        "ID_Segmento_Comp", "ID_Agencia", "ID_Tipo_Habitacion", "ID_canal",
        "h_fec_lld", "h_fec_reg", "h_fec_sda", "ID_Pais_Origen",
        "Reservacion", "ID_estatus_reservaciones", "h_edo", "h_tfa_total",
        "moneda_cve", "h_ult_cam_fec"
    ]
    df = df[cols_keep].copy()

    # 2. Conversión de tipos ─────────────────────────────────────────────
    # 2.1) A datetime
    date_cols = ["Fecha_hoy", "h_fec_lld", "h_fec_reg", "h_fec_sda"]
    df[date_cols] = df[date_cols].apply(lambda col: pd.to_datetime(col, errors="coerce"))

    # 2.2) A enteros (Int64 permite nulos)
    int_cols = ["h_tot_hab", "h_num_per", "h_num_adu", "h_num_men", "h_num_noc"]
    df[int_cols] = df[int_cols].astype("Int64")

    # 2.3) A string
    str_cols = [
        "ID_Programa", "ID_empresa", "ID_Paquete",
        "ID_Segmento_Comp", "ID_Agencia", "ID_Tipo_Habitacion",
        "ID_canal", "ID_Pais_Origen", "moneda_cve"
    ]
    df[str_cols] = df[str_cols].astype("string")

    # 3. Eliminar registros con tarifa negativa ─────────────────────────
    df = df[df["h_tfa_total"] >= 0].copy()

    # 4. Eliminar registros con h_num_per = 0, h_num_noc = 0 y h_tot_hab = 0
    df = df[df["h_num_per"] > 0]
    df = df[df["h_num_noc"] > 0]
    df = df[df["h_tot_hab"] > 0]

    # 5. Limpieza de outliers extremos (percentil 0.05% / 99.95%)
    columnas_a_limpiar = ["h_num_per", "h_num_noc", "h_tfa_total"]
    for col in columnas_a_limpiar:
        low = df[col].quantile(0.0005)
        high = df[col].quantile(0.9995)
        df = df[(df[col] >= low) & (df[col] <= high)]

    # 6. Resetear índice y retornar
    return df.reset_index(drop=True)


# ---------- 2) ENTRENAMIENTO ----------
def train_cluster(df: pd.DataFrame, n_clusters: int, random_state: int):
    """
    1) Fijar semilla en NumPy y PyTorch para reproducibilidad
    2) Codifica variables categóricas con LabelEncoder
    3) Pre-entrena TabNet (unsupervised)
    4) Extrae embeddings
    5) Busca el mejor K (4-5) con Silhouette y guarda KMeans
    6) Devuelve un diccionario con todo el pipeline
    """

    # ── 1) FIJAR SEMILLA EN NUMPY Y PYTORCH ─────────────────────────────
    np.random.seed(random_state)
    torch.manual_seed(random_state)
    torch.use_deterministic_algorithms(True)

    # ── 2) Definir variables numéricas y categóricas ───────────────────
    num_vars = [
        "h_num_per", "h_num_adu", "h_num_men",
        "h_num_noc", "h_tot_hab", "h_tfa_total"
    ]
    cat_vars = [
        "ID_Tipo_Habitacion", "ID_canal", "ID_Pais_Origen",
        "ID_Segmento_Comp", "ID_Agencia"
    ]

    # ── 3) LabelEncode ─────────────────────────────────────────────────
    X = df[num_vars + cat_vars].copy()
    encoders: dict[str, LabelEncoder] = {}
    for col in cat_vars:
        enc = LabelEncoder().fit(X[col])
        X[col] = enc.transform(X[col])
        encoders[col] = enc

    # ── 3.5) Asegurarse de que no haya nulos (los rellenamos con -1) ────
    X = X.fillna(-1)

    # ── 4) Preparar matriz float32 para TabNet ──────────────────────────
    X_array = X.astype("float32").to_numpy()

    # ── 5) Preentrenar TabNet ────────────────────────────────────────────
    tabnet = TabNetPretrainer(
        optimizer_fn=torch.optim.Adam,
        optimizer_params=dict(lr=1e-3),
        seed=random_state,   # TabNet interno usará esta semilla también
        verbose=0,
    )
    tabnet.fit(
        X_train=X_array,
        eval_set=[X_array],
        max_epochs=100,
        patience=10,
        batch_size=256,
        virtual_batch_size=128,
    )

    # ── 6) Extraer embeddings ───────────────────────────────────────────
    embeddings, _ = tabnet.predict(X_array)

    # ── 7) Buscar K óptimo entre [4,5] usando Silhouette ───────────────
    best_score = -1.0
    best_k = None
    best_km = None
    for k in range(4, 6):  # sólo probamos k=4 y k=5
        km = KMeans(n_clusters=k,
                    random_state=random_state,
                    n_init="auto")
        km.fit(embeddings)
        score = silhouette_score(embeddings, km.labels_)
        if score > best_score:
            best_score, best_k, best_km = score, k, km

    # ── 8) Empaquetar todo en un diccionario para retornarlo ──────────
    pipeline_dict = {
        "encoders": encoders,
        "tabnet":   tabnet,
        "kmeans":   best_km,
        "num_vars": num_vars,
        "cat_vars": cat_vars,
        "best_k":   best_k,
        "sil_score": best_score,
    }
    return pipeline_dict


# ---------- 3) PREDICCIÓN ----------
def assign_clusters(df: pd.DataFrame, model: dict) -> pd.DataFrame:
    """
    Usa el diccionario `model` devuelto por train_cluster para:
    - codificar categóricas con los LabelEncoder entrenados
    - pasar por TabNet y obtener embeddings
    - asignar etiquetas de KMeans
    Devuelve df con una columna adicional `cluster`.
    """
    num_vars = model["num_vars"]
    cat_vars = model["cat_vars"]
    encoders = model["encoders"]
    tabnet   = model["tabnet"]
    kmeans   = model["kmeans"]

    # 1) Preparar X con las columnas numéricas + categóricas
    X = df[num_vars + cat_vars].copy()
    for col in cat_vars:
        X[col] = encoders[col].transform(X[col])

    X_array = X.values.astype(np.float32)

    # 2) Obtener embeddings con TabNet
    embeddings, _ = tabnet.predict(X_array)

    # 3) Predecir clusters usando KMeans
    labels = kmeans.predict(embeddings)

    df_out = df.copy()
    df_out["cluster"] = labels
    return df_out


# ---------- 4) PERFIL ----------
def profile_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada cluster, calcular:

    - La media (_mean_) únicamente de las variables numéricas originales que usamos:
        "h_num_per", "h_num_adu", "h_num_men", "h_num_noc", "h_tot_hab", "h_tfa_total"

    - La moda (_mode_) únicamente de las variables categóricas originales que usamos:
        "ID_Tipo_Habitacion", "ID_canal", "ID_Pais_Origen", "ID_Segmento_Comp", "ID_Agencia"

    No devuelve resumen de TODO el DataFrame, sino sólo de esas columnas de interés.
    """
    # Definimos exactamente las columnas que queremos resumir:
    num_vars = ["h_num_per", "h_num_adu", "h_num_men",
                "h_num_noc", "h_tot_hab", "h_tfa_total"]
    cat_vars = ["ID_Tipo_Habitacion", "ID_canal", "ID_Pais_Origen",
                "ID_Segmento_Comp", "ID_Agencia"]

    agg_specs = {}

    # Para cada variable numérica pedimos la media:
    for c in num_vars:
        agg_specs[c] = "mean"

    # Para cada variable categórica pedimos la moda (el valor más frecuente):
    for c in cat_vars:
        agg_specs[c] = (lambda x: x.mode(dropna=True).iat[0]
                        if len(x) else None)

    # Agrupamos por cluster y aplicamos las funciones:
    summary = (
        df
        .groupby("cluster", dropna=False)
        .agg(agg_specs)
        .round(2)
        .reset_index()
    )
    return summary
