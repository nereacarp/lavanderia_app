import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

archivo_reservas = "reservas.csv"

# Cargar reservas existentes
try:
    reservas = pd.read_csv(archivo_reservas)
except:
    reservas = pd.DataFrame(columns=["habitacion","fecha","franja"])

st.title("Reserva Lavandería")

# Formulario de reserva
with st.form("reserva_form"):
    habitacion = st.text_input("Número de habitación")
    hoy = datetime.today().date()
    fechas_disponibles = [hoy + timedelta(days=i) for i in range(14)]
    fecha = st.selectbox("Elige fecha", fechas_disponibles)
    franjas = ["08:00-12:00","12:00-16:00","16:00-20:00","20:00-00:00"]
    franja = st.selectbox("Elige franja", franjas)
    submit = st.form_submit_button("Reservar")

if submit:
    # Validar máximo 1 reserva por semana por habitación
    semana = fecha.isocalendar()[1]
    reservas["semana"] = pd.to_datetime(reservas["fecha"]).dt.isocalendar().week
    if ((reservas["habitacion"]==habitacion) & (reservas["semana"]==semana)).any():
        st.warning("Esta habitación ya tiene un turno esta semana.")
    else:
        # Validar que haya menos de 3 reservas en esa fecha y franja
        cupo = reservas[(reservas["fecha"]==str(fecha)) & (reservas["franja"]==franja)]
        if len(cupo) >= 3:
            st.warning("Esta franja ya está completa.")
        else:
            nuevas = pd.DataFrame([[habitacion,str(fecha),franja]], columns=["habitacion","fecha","franja"])
            reservas = pd.concat([reservas,nuevas], ignore_index=True)
            reservas.to_csv(archivo_reservas,index=False)
            st.success(f"Turno reservado para {fecha} {franja} ✔️")

# Mostrar calendario visual con ocupación por habitación
st.subheader("Disponibilidad de los próximos 14 días (3 huecos por franja)")
tabla = []

for f in fechas_disponibles:
    fila = {"Fecha": f}
    for fr in franjas:
        cupo = reservas[(reservas["fecha"]==str(f)) & (reservas["franja"]==fr)]
        # Mostrar los números de habitación ocupando cada hueco, hasta 3
        ocupacion = cupo["habitacion"].tolist()
        while len(ocupacion) < 3:
            ocupacion.append("Libre")
        fila[fr] = " | ".join(ocupacion)
    tabla.append(fila)

st.table(pd.DataFrame(tabla))
st.caption("Cada franja muestra las 3 máquinas. 'Libre' indica hueco disponible.")
