import os
import pandas as pd
import numpy as np
import joblib
from datetime import date
from django.utils import timezone
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from ventas.models import DetailNote
from productos.models import Product

# 1️⃣ FUNCIONES DE APOYO

def obtener_temporada(mes: int) -> str:
    if mes in [12, 1, 2]:
        return "verano"
    elif mes in [3, 4, 5]:
        return "otoño"
    elif mes in [6, 7, 8]:
        return "invierno"
    elif mes in [9, 10, 11]:
        return "primavera"
    return "desconocido"


def ruta_modelo():
    """Ruta absoluta del modelo guardado"""
    carpeta = os.path.join(settings.BASE_DIR, "apps", "reportes", "ml_models", "modelos_guardados")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "modelo_demanda_rf.pkl")

# 2️⃣ CREACIÓN DE DATASET

def generar_dataset():

    data = []
    detalles = DetailNote.objects.select_related("nota", "producto", "producto__categoria").all()

    for d in detalles:
        mes = d.nota.fecha.month
        data.append({
            "producto_id": d.producto.id,
            "categoria": d.producto.categoria.descripcion,
            "precio": float(d.producto.precio),
            "stock": d.producto.stock,
            "cantidad_vendida": d.cantidad,
            "mes": mes,
            "anio": d.nota.fecha.year,
            "temporada": obtener_temporada(mes),
            "dia_semana": d.nota.fecha.weekday(),
            "tipo_pago": getattr(d.nota, "tipo_pago", "desconocido"),
        })

    if not data:
        raise ValueError("No hay datos suficientes en DetailNote para entrenar el modelo")

    df = pd.DataFrame(data)
    print(f"✅ Dataset generado con {len(df)} registros")
    return df

# 3️⃣ ENTRENAMIENTO DEL MODELO

def entrenar_modelo():

    df = generar_dataset()

    # Convertir categóricas
    df = pd.get_dummies(df, columns=["categoria", "temporada", "tipo_pago"], drop_first=True)

    X = df.drop(["cantidad_vendida"], axis=1)
    y = df["cantidad_vendida"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo = RandomForestRegressor(n_estimators=200, random_state=42)
    modelo.fit(X_train, y_train)

    # Evaluación
    y_pred = modelo.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("📈 Modelo entrenado correctamente")
    print(f"🔹 R²: {r2:.3f}")
    print(f"🔹 MAE: {mae:.3f}")

    # Guardar modelo
    joblib.dump(modelo, ruta_modelo())
    print(f"💾 Modelo guardado en: {ruta_modelo()}")

    return {
        "registros": len(df),
        "r2_score": round(r2, 3),
        "mae": round(mae, 3),
        "modelo_guardado": ruta_modelo()
    }

# 4️⃣ PREDICCIÓN CON MODELO ENTRENADO
def predecir_demanda_rf(producto_id: int, dias_futuro: int = 30):
    
    modelo_path = ruta_modelo()
    if not os.path.exists(modelo_path):
        raise FileNotFoundError("No existe el modelo entrenado. Ejecute entrenar_modelo() primero.")

    modelo = joblib.load(modelo_path)
    producto = Product.objects.select_related("categoria").get(id=producto_id)

    mes = timezone.now().month
    temporada = obtener_temporada(mes)
    tipo_pago = "efectivo"  # valor neutral por ahora

    df = pd.DataFrame([{
        "producto_id": producto.id,
        "categoria": producto.categoria.descripcion,
        "precio": float(producto.precio),
        "stock": producto.stock,
        "mes": mes,
        "anio": timezone.now().year,
        "temporada": temporada,
        "dia_semana": date.today().weekday(),
        "tipo_pago": tipo_pago,
    }])

    # Variables dummy
    df = pd.get_dummies(df, columns=["categoria", "temporada", "tipo_pago"], drop_first=True)

    # Alinear columnas con el modelo entrenado
    columnas_entrenadas = modelo.feature_names_in_
    for col in columnas_entrenadas:
        if col not in df.columns:
            df[col] = 0
    df = df[columnas_entrenadas]

    prediccion = modelo.predict(df)[0]

    return {
        "producto_id": producto.id,
        "nombre": producto.nombre,
        "categoria": producto.categoria.descripcion,
        "prediccion_unidades": round(float(prediccion), 2),
        "dias_proyeccion": dias_futuro,
        "fecha_prediccion": timezone.now().isoformat(),
        "modelo_usado": "RandomForestRegressor"
    }
