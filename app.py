import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Archivo para guardar reservas
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
    
    # Fechas disponibles (hoy hasta 14 días)
    hoy = datetime.today().date()
    fechas_disponibles = [hoy + timedelta(days=i) for i in range(14)]
    fecha = st.selectbox("Elige fecha", fechas_disponibles)
    
    # Franjas horarias
    franjas = ["08:00-12:00","12:00-16:00","16:00-20:00","20:00-00:00"]
    franja = st.selectbox("Elige franja", franjas)
    
    submit = st.form_submit_button("Reservar")

if submit:
    # Validar que la habitación no tenga turno esa semana
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
            # Guardar reserva
            nuevas = pd.DataFrame([[habitacion,str(fecha),franja]], columns=["habitacion","fecha","franja"])
            reservas = pd.concat([reservas,nuevas], ignore_index=True)
            reservas.to_csv(archivo_reservas,index=False)
            st.success(f"Turno reservado para {fecha} {franja} ✔️")

# Mostrar disponibilidad visual
st.subheader("Disponibilidad de los próximos 14 días")
for f in fechas_disponibles:
    st.write(f"**{f}**")
    for fr in franjas:
        cupo = reservas[(reservas["fecha"]==str(f)) & (reservas["franja"]==fr)]
        st.write(f"{fr}: {len(cupo)}/3 ocupados")
