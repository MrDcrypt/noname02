import tkinter as tk
from tkinter import Frame, Label, ttk, Button, IntVar, PhotoImage, Toplevel, Menu, StringVar, Entry, messagebox, Text, END, Checkbutton
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import serial
import speech_recognition as sr
import pyttsx3
import threading
import time
import pygame
import datetime
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import time
import requests
import hashlib
from tkinter import font as tkFont
import csv
import os
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
from flask import Flask, request, jsonify
import matplotlib.pyplot as plt








# Variable global para el puerto serial
ser = None
global engine
engine = pyttsx3.init()
  # para importar audio
min_h = 50  # Altura mínima del frame
max_h = 200  # Altura máxima del frame
cur_height = min_h  # La altura actual del frame (comienza en la altura mínima)
expanded = False  # Verifica si el frame está completamente expandido

#funcion alerta
global urgente 
urgente = False
alarmak = "alarmak.mp3"  # Nombre del archivo de sonido para la alarma




#fin funcion  alerta



##implementacion clima
def obtener_clima():
    api_key = "3f93b00f8d653e1322b85a8bc0a22ca3"
    ciudad = "Villa Berthet,AR"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        clima = data['weather'][0]['description'].capitalize()  # Descripción del clima
        temp = data['main']['temp']  # Temperatura actual
        prob_lluvia = data.get('rain', {}).get('1d', 0)  # Probabilidad de lluvia en la última hora
        
        # Actualizar el label con la información del clima
        clima_label.config(text=f"{clima}")
        clima_label_uno.config(text=f"{temp}°C")
        #clima_label_dos.config(text=f"{prob_lluvia} %")


    else:
        clima_label.config(text="Eror sin datos")
        clima_label_uno.config(text="Sin datos")
       # clima_label_dos.config(text=f"Sin datos")

###


# Configura la voz femenina
#voices = engine.getProperty('voices')
#for voice in voices:
    #if "female" in voice.name.lower():
      #  engine.setProperty('voice', voice.id)
      #  break


def speak(text):
    """Función para convertir texto a voz."""
    engine.say(text)
    engine.runAndWait()


is_listening = False


def play_audio(file_path):
    """Función para reproducir un archivo MP3."""
    if not pygame.mixer.get_init():  # Verificar si mixer no está inicializado
        pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()


# Inicializa la conexión serial
def init_serial(port='/dev/ttyUSB0', baudrate=9600):
    try:
        global ser
        ser = serial.Serial(port, baudrate)
        terminal.insert(END," Sensores: OK \t")
    except serial.SerialException as e:
        print(f"Error: {e}")
        terminal.insert(END," Sensores: FAIL \t")


def stop_audio():
    """Función para detener la reproducción de audio"""
    
    pygame.mixer.music.stop()
    audio_played_flag = False

def check_critical_levels(label, value, max_value, warning_text):
    """Verifica si una variable se sale del rango permitido y muestra alerta"""
    global urgente
    # Verifica si el valor supera el máximo permitido
    if value > max_value and urgente is False:
        # Muestra un mensaje de advertencia
       
        urgente = True
        threading.Thread(target=play_audio, args=(alarmak,)).start()  # Inicia el audio en un hilo separado
    elif value <= max_value and urgente is True:
        # Si los valores vuelven al rango normal, detiene la alarma
        urgente = False
        stop_audio()
def show_warning_message(warning_text):
    # Función para cerrar la ventana emergente después de 4 segundos
    def hide_message():
        mensaje_urgente.destroy()  # Destruye la ventana emergente

    # Crear una nueva ventana emergente
    mensaje_urgente = tk.Toplevel()
    mensaje_urgente.title("Advertencia")
    mensaje_urgente.attributes('-topmost', True)
    mensaje_urgente.lift()

    # Crear una etiqueta con el mensaje de advertencia
    message_label = tk.Label(mensaje_urgente, text=warning_text, font=label_style_large, bg="red", fg="white")
    message_label.pack(side="top")

    # Usar threading para destruir la ventana después de 4 segundos
    threading.Timer(4, hide_message).start()

# funciones_de_escucha
def act_label_hum_suelo(humedad, ph):
        textuno_var.set(f"Humedad de suelo: {humedad}%.\n pH: {ph}")
        #check_critical_levels(textuno_var, humedad, 70 ,"¡Urgente! Humedad de suelo fuera de rango" )
        if humedad > 70:
            text_labeluno.config(bg="#00008B")
        elif humedad < 15:
            text_labeluno.config(bg="#A52A2A")
        else:
            text_labeluno.config(bg="#90EE90")



def get_audio_devices():
    """Función para obtener los dispositivos de audio disponibles."""
    devices = []
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        devices.append(f"Device {index}: {name}")
    return devices


def listen_command(device_index=None):
    """Función para escuchar y reconocer comandos de voz."""   #confguracion de spechrecognition
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone(device_index=device_index) as source:
            print("Escuchando...")
            # Ajusta el ruido ambiente por 1 segundo
            recognizer.adjust_for_ambient_noise(source, duration=1)
            # Aumenta el tiempo de escucha
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
        command = recognizer.recognize_google(audio, language='es-ES')
        return command.lower()
    except sr.UnknownValueError:     #speech recognition nos presenta varios tipos de exepciones y errores 
        print("No se entendió el comando")
        return ""
    except sr.RequestError:
        print("Error de conexión")
       # speak("Error de conexión, por favor intente nuevamente")
        return ""
    except Exception as e:
        print(f"Error: {str(e)}")
        return ""


def process_command(command):
    """Procesa el comando reconocido y ejecuta la acción correspondiente."""
    # listas de sinónimos para comandos
    encender_riego_synonyms = ["encender gotas",
                               "encender riego", "riego on", "activar riego"]
    apagar_riego_synonyms = ["apagar riego", "riego off", "riego apagar",
                             "riego apagado", "quitar riego", "apagar friego", "apagar diego"]
    encender_luces_synonyms = ["encender luces", "luces on", "prender luces"]
    apagar_luces_synonyms = ["apagar luces",
                             "luces off", "luces apagar", "luces apagadas"]
    all_off_synonyms = ["luces y riego apagados", "todo apagado"]

    if any(keyword in command for keyword in encender_riego_synonyms):  #se usa listas por compresión y la función any incorporada de python
        if irrigation_var.get() == 0:
            toggle_irrigation()
    elif any(keyword in command for keyword in apagar_riego_synonyms): #command es lo que el usuario dijo
        if irrigation_var.get() == 1:
            toggle_irrigation()
    elif any(keyword in command for keyword in encender_luces_synonyms):# keyword es una palabra individual
        if estado_focos.get() == 0:
            control_luces()
    elif any(keyword in command for keyword in apagar_luces_synonyms):#tomamos cada valor de la lista y la comparamos con cada palabra de lo que dijo el usuario
        if estado_focos.get() == 1:
            control_luces()
    elif any(keyword in command for keyword in all_off_synonyms):
        if estado_focos.get() == 1:
            control_luces()
        if irrigation_var.get() == 1:
            toggle_irrigation()
        speak("Comando no reconocido, por favor intente nuevamente")


def stop_listening():
    global is_listening
    is_listening = False


def start_listening(event=None):
    global is_listening

    if is_listening:
        stop_listening()
        escucha_btn.config(image=microoff)
    else:
        is_listening = True
        escucha_btn.config(image=microon)
        #play_audio("teecuchoCol.mp3")

        def listen_loop():
            while is_listening:
                # Usa el dispositivo de audio predeterminado
                command = listen_command(device_index=None)
                if command:
                    process_command(command)
                time.sleep(0.1)

        listen_thread = threading.Thread(target=listen_loop)
        listen_thread.start()


##prueba recon




luces_timeout = 0
global luces_espera 
luces_espera = None
def control_luces(event=None):
    global ser, light_on, luces_timeout, luces_espera

    # delay de 40s
    delay_seconds = 10

    # verificar si ya paso el tiempo
    current_time = time.time() #tiempo actual hora, minuto, segundo.
    if current_time < luces_timeout:
        print("Espera unos segundos para volver a ejecutar.") 
        luces_espera = True
        return


    luces_timeout = current_time + delay_seconds #adelantamos el tiempo de comprobacion 40 s ahora activará la bandera luces_espera 
    try:
        # Function logic
        if estado_focos.get() == 0:
            estado_focos.set(1)
            lucesex_btn.config(image=icono_led_on)
            label_iconoluz.config(image=iconluzmapon)
            dibujo_frame.config(bg="#A0A0A0")
            frame_icons.config(bg="#A0A0A0")
            play_audio("lucesoncol.mp3")
            light_on = True
            luces_espera = False

            # comprobamso q la conexion arduino esta activa y funcional
            if ser is not None and ser.is_open:
                ser.write(b"LUZ_ON\n")   #mandamos por el puerto serie un coomando textual que arduino espera recibir 
            else:
                print("Sin conexión al puerto serial, no se pudo ejecutar el comando")

        else:
            estado_focos.set(0)
            dibujo_frame.config(bg="#2E2E2E")
            frame_icons.config(bg="#2E2E2E")
            lucesex_btn.config(image=icono_led_off)
            label_iconoluz.config(image=iconluzmapoff)
            play_audio("lucesoffcol.mp3")
            light_on = False
            luces_espera = False

            # Send command to turn off the LED if the serial connection is open
            if ser is not None and ser.is_open:
                ser.write(b"LUZ_OFF\n")
            else:
                print("Sin conexión al puerto serial, no se pudo ejecutar el comando")

    except serial.SerialException as e:
        print(f"Serial exception occurred: {e}")
        # Optional: attempt to close and reopen the serial connection
        try:
            ser.close()
            time.sleep(1)  # Short delay before reopening
            ser.open()
            print("Serial connection reopened.")
        except Exception as reopen_error:
            print(f"Failed to reopen serial connection: {reopen_error}")
##

mp_hands = mp.solutions.hands 
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7) #configuraciones mediapipe 1 mano, detección rapida a la primera
mp_drawing = mp.solutions.drawing_utils

def reconocer_puno():
    global puno_detectado
    global riego_detectado
    riego_detectado = False
    puno_detectado = False
    # Crear una nueva ventana para el reconocimiento de puños
    reconocer_window = tk.Toplevel()
    reconocer_window.title("Reconocimiento de Gestos")
    reconocer_window.attributes('-topmost', True)
    reconocer_window.lift()

    # Añadimos un label donde se mostrará el video de la cámara
    video_label = Label(reconocer_window)
    video_label.pack()

    # Label para indicar si el puño está cerrado o no
    status_label = Label(reconocer_window, text="Puño no detectado", bg="green", font=("Helvetica", 16))
    status_label.pack(pady=10)

    # Inicializamos la cámara
    cap = cv2.VideoCapture(0)

    # Función para detectar si el puño está cerrado
    def is_fist_closed(hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]  # Pulgar
        index_tip = hand_landmarks.landmark[8]  # Índice se configuran los 5 dedos, sus posiciones con mano abierta
        middle_tip = hand_landmarks.landmark[12]  # Medio
        ring_tip = hand_landmarks.landmark[16]  # Anular
        pinky_tip = hand_landmarks.landmark[20]  # Meñique

        if (index_tip.y > hand_landmarks.landmark[6].y and
            middle_tip.y > hand_landmarks.landmark[10].y and
            ring_tip.y > hand_landmarks.landmark[14].y and      #se compara la punta de los dedos vs el punto medio 
            pinky_tip.y > hand_landmarks.landmark[18].y):
            return True
        return False

    def is_v_shape(hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]  # Punta del pulgar
        index_tip = hand_landmarks.landmark[8]  # Punta del índice
        middle_tip = hand_landmarks.landmark[12]  # Punta del medio
        ring_tip = hand_landmarks.landmark[16]  # Punta del anular
        pinky_tip = hand_landmarks.landmark[20]  # Punta del meñique

    # Verificar si el índice y el medio están arriba y los otros dedos están cerrados
        is_index_up = index_tip.y < hand_landmarks.landmark[6].y
        is_middle_up = middle_tip.y < hand_landmarks.landmark[10].y
        is_ring_closed = ring_tip.y > hand_landmarks.landmark[14].y
        is_pinky_closed = pinky_tip.y > hand_landmarks.landmark[18].y

        return is_index_up and is_middle_up and is_ring_closed and is_pinky_closed


    #funcion detectar l
    def is_L_shape(hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]  # Pulgar
        index_tip = hand_landmarks.landmark[8]  # Índice
        middle_tip = hand_landmarks.landmark[12]  # Medio
        ring_tip = hand_landmarks.landmark[16]  # Anular
        pinky_tip = hand_landmarks.landmark[20]  # Meñique

    # Verificar si el pulgar y el índice están arriba
        is_thumb_up = thumb_tip.y < hand_landmarks.landmark[2].y
        is_index_up = index_tip.y < hand_landmarks.landmark[6].y

    # Verificar si los otros dedos están cerrados
        is_middle_closed = middle_tip.y > hand_landmarks.landmark[10].y  # Medio cerrado
        is_ring_closed = ring_tip.y > hand_landmarks.landmark[14].y  # Anular cerrado
        is_pinky_closed = pinky_tip.y > hand_landmarks.landmark[18].y  # Meñique cerrado

        return is_thumb_up and is_index_up and is_middle_closed and is_ring_closed and is_pinky_closed


    def is_thumb_up_or_down(hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]  # Punta del pulgar
        thumb_base = hand_landmarks.landmark[2]  # Base del pulgar (primer articulación)

    # Landmarks de los otros dedos
        index_tip = hand_landmarks.landmark[8]  # Punta del índice
        middle_tip = hand_landmarks.landmark[12]  # Punta del medio
        ring_tip = hand_landmarks.landmark[16]  # Punta del anular
        pinky_tip = hand_landmarks.landmark[20]  # Punta del meñique

    # Verificar si los demás dedos están cerrados (puntas están por debajo de las articulaciones intermedias)
        if (index_tip.y > hand_landmarks.landmark[6].y and
            middle_tip.y > hand_landmarks.landmark[10].y and
            ring_tip.y > hand_landmarks.landmark[14].y and
            pinky_tip.y > hand_landmarks.landmark[18].y):
        
        # Determinar la dirección del pulgar
            if thumb_tip.y < thumb_base.y:
                return "up"  # Pulgar arriba
            else:
                return "down"  # Pulgar abajo

    # Si otros dedos no están cerrados, no considerar el estado del pulgar
        return None



    #fin detectar cuerno

    # Función para capturar y mostrar el video en el label de Tkinter
    
    def update_frame():
        global puno_detectado
        global riego_detectado
        ret, frame = cap.read()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    if is_fist_closed(hand_landmarks):
                        status_label.config(text="Puño detectado", bg="red")
                        if not puno_detectado:
                            control_luces()  # Llamar a control de luces solo cuando se detecta el puño por primera vez
                            puno_detectado = True  # Actualizar el estado a puño detectado
                    else:
                        status_label.config(text="Puño no detectado", bg="green")
                        if puno_detectado:
                            puno_detectado = False

                    #if is_L_shape(hand_landmarks):  # Cambia a is_open_hand si prefieres usar el gesto de mano abierta
                        #status_label.config(text="Riego activado", bg="blue")
                       # if not riego_detectado:
                           # toggle_irrigation()  # Llamar a toggle_irrigation solo cuando se detecta el gesto de riego por primera vez
                           # riego_detectado = True
                    #else:
                        #status_label.config(text="Riego no detectado", bg="green")
                        #if riego_detectado:
                          #  riego_detectado = False

                    
                    
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)

        video_label.after(10, update_frame)

    # Iniciamos la actualización del video
    update_frame()

    # Cerrar la cámara al cerrar la ventana
    def on_closing():
        cap.release()
        reconocer_window.destroy()

    reconocer_window.protocol("WM_DELETE_WINDOW", on_closing)



###
def control_refri(event=None):
    

    if estado_refri.get() == 0:
        estado_refri.set(1)
        refri_btn.config(image=fanon)
        play_audio("ventaprendida.mp3")


    else:
        
        estado_refri.set(0)
        refri_btn.config(image=fanoff)
        play_audio("ventaapagada.mp3")




# Controla el botón de encendido y apagado del sistema
def toggle_button(event=None):
    global ser

    if button_var.get() == 1:
        button_var.set(0)
        toggle_btn.config(bg="green")
        terminal.delete("1.0","1.end")
        terminal.insert("1.0","Sistema iniciado \t")
        init_serial()
        root.after(1000, update_graph)
    else:
        button_var.set(1)
        toggle_btn.config(bg="red")
        terminal.delete("1.0","1.end")
        terminal.insert("1.0","Sistema Apagado \t")
        
        if ser and ser.is_open:
            terminal.delete("1.0","1.end")
            terminal.insert("1.0","Sistema Apagado")
            ser.close()
            ser = None

# Controla el botón de riego


irrigation_timeout = 0
global riego_espera
riego_espera = None

def toggle_irrigation(event=None):
    global ser, irrigation_timeout, riego_espera, irrigation_var
    
    # delay
    delay_seconds = 10

    # verificar si ya es hora
    current_time = time.time()
    if current_time < irrigation_timeout:
        print("Espera unos segundos para volver a la acción")
        riego_espera = True
        return

    #actualizamos el tiempo mas los segundos de delay
    irrigation_timeout = current_time + delay_seconds

    try:
        # Toggle irrigation state
        if irrigation_var.get() == 0:
            irrigation_var.set(1)
            gota_btn.config(image=gotaon)
            label_iconoriego.config(image=iconriegomapon)
            play_audio("riegooncol.mp3")
            riego_espera = False

            # Send command to turn on irrigation if serial connection is open
            if ser is not None and ser.is_open:
                ser.write(b"RIEGO_ON\n")
            else:
                print("Serial connection not open. Cannot send RIEGO_ON command.")

        else:
            irrigation_var.set(0)
            gota_btn.config(image=gotaoff)
            label_iconoriego.config(image=iconriegomapoff)
            play_audio("riooffcol.mp3")
            riego_espera = False

            # Send command to turn off irrigation if serial connection is open
            if ser is not None and ser.is_open:
                ser.write(b"RIEGO_OFF\n")
            else:
                print("Serial connection not open. Cannot send RIEGO_OFF command.")

    except serial.SerialException as e:
        print(f"Serial exception occurred: {e}")
        # Optional: attempt to close and reopen the serial connection
        try:
            ser.close()
            time.sleep(1)  # Short delay before reopening
            ser.open()
            print("Serial connection reopened.")
        except Exception as reopen_error:
            print(f"Failed to reopen serial connection: {reopen_error}")
        
        

        
   

#funcion programar luces:
def open_light_schedule(event=None):
    global schedules
    schedules = []
    repetir_diariamente = IntVar()

    def obtener_datos_luz():
        fecha_selec_grafica = date_entry.get_date()
        hora_comienzo = hora_var.get()
        duracion_horas = duracion_var.get()
        repetir = repetir_diariamente.get()

        if not fecha_selec_grafica or not hora_comienzo or not duracion_horas:
            messagebox.showerror("Error", "Por favor complete todos los campos.")
            return

        try:
            # Convertir hora a formato datetime
            fecha_hora_comienzo_dt = datetime.datetime.strptime(f"{fecha_selec_grafica} {hora_comienzo}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            messagebox.showerror("Error", f"Formato de hora incorrecto: {e}")
            return

        schedules.append({"fecha": fecha_selec_grafica, "hora": hora_comienzo, "duracion": duracion_horas, "repetir": repetir})
        
        # Actualizar label_izq con la nueva programación
        label_izq.config(
            text=f"Programación de luces: \nInicia {fecha_selec_grafica} {hora_comienzo}, \nDuración: {duracion_horas} horas",
            fg="green"
        ) 

        print(f"Programación guardada: Fecha: {fecha_selec_grafica}, Hora: {hora_comienzo}, Duración: {duracion_horas}, Repetir diariamente: {repetir}")
        save_all_light_schedules()
        program_window.destroy()

    def save_all_light_schedules():
        for schedule in schedules:
            fecha_comienzo = schedule["fecha"]
            hora_comienzo = schedule["hora"]
            duracion_horas = schedule["duracion"]
            repetir = schedule["repetir"]
            print(f"Fecha de comienzo: {fecha_comienzo}, Hora: {hora_comienzo}, Duración: {duracion_horas} horas, Repetir: {repetir}")
            try:
                fecha_hora_comienzo_dt = datetime.datetime.strptime(f"{fecha_comienzo} {hora_comienzo}", "%Y-%m-%d %H:%M")
                check_luces(fecha_hora_comienzo_dt, int(duracion_horas))
            except ValueError as e:
                print(f"Error en el formato de fecha/hora: {e}")

    def check_luces(fecha_hora_comienzo_dt, duracion_horas):
        """Verifica la hora actual y enciende las luces si es la hora programada."""
        fecha_hora_actual = datetime.datetime.now()
        print(f"Fecha y hora actuales: {fecha_hora_actual}")
        if fecha_hora_comienzo_dt <= fecha_hora_actual:
            print("Encendiendo las luces...")
            
            #control_luces()
            estado_focos.set(1)
            lucesex_btn.config(image=icono_led_on)
            label_iconoluz.config(image=iconluzmapon)
            dibujo_frame.config(bg="#A0A0A0")
            frame_icons.config(bg="#A0A0A0")
            # comprobamso q la conexion arduino esta activa y funcional
            if ser is not None and ser.is_open:
                ser.write(b"LUZ_ON\n")   #mandamos por el puerto serie un coomando textual que arduino espera recibir 
            else:
                print("Sin conexión al puerto serial, no se pudo ejecutar el comando")
            root.after(duracion_horas * 3600000, apagar_luces)
        else:
            print("Aún no es la hora de encender las luces.")
            root.after(1000, check_luces, fecha_hora_comienzo_dt, duracion_horas)

    def apagar_luces():
        """Apaga las luces y restaura el label_izq al texto original."""
        print("Apagando las luces...")
        control_luces()  # Apagar las luces
        label_izq.config(text="Sin programación luces", fg="red")

    # Creación de la ventana para programar luces
    program_window = Toplevel(root)
    program_window.title("Programar Luces")
    program_window.attributes('-topmost', True)
    program_window.lift() 

    # Calendario para seleccionar la fecha
    Label(program_window, text="Seleccionar fecha:").grid(row=0, column=0, padx=10, pady=10)
    date_entry = DateEntry(program_window, date_pattern='y-mm-dd', width=20, background='darkblue', foreground='white', borderwidth=2)
    date_entry.grid(row=0, column=1, padx=10, pady=10)

    # Entrada para la hora de inicio
    hora_var = StringVar()
    Label(program_window, text="Hora de inicio (HH:MM):").grid(row=1, column=0, padx=10, pady=10)
    Entry(program_window, textvariable=hora_var).grid(row=1, column=1, padx=10, pady=10)

    # Entrada para la duración en horas
    duracion_var = StringVar()
    Label(program_window, text="Duración (horas):").grid(row=2, column=0, padx=10, pady=10)
    Entry(program_window, textvariable=duracion_var).grid(row=2, column=1, padx=10, pady=10)

    # Checkbutton para repetir diariamente
    Checkbutton(program_window, text="Repetir esta programación diariamente", variable=repetir_diariamente).grid(row=3, columnspan=2, padx=10, pady=10)

    # Botones de aceptar y cancelar
    Button(program_window, text="Aceptar", command=obtener_datos_luz).grid(row=4, column=0, padx=10, pady=10)
    Button(program_window, text="Cancelar", command=program_window.destroy).grid(row=4, column=1, padx=10, pady=10)

#hastaqui

# Variables globales para almacenar el estado del riego
#riego
riego_programado = None  # Aquí guardaremos la programación del riego
riego_id = None  # ID del riego para poder cancelarlo
riego_en_curso = False  # Para saber si el riego está activo

def open_program_schedule(event=None):
    global riego_programado, label_derecho  # Usamos la variable global
    schedules = []
    riegos_diarios = IntVar()
    repetir_diariamente = IntVar()
    global cancelar_riego

    def actualizar_label_derecho(texto):
        """Función para actualizar el label_derecho en la ventana principal."""
        label_derecho.config(text=texto)

    def obtener_datos_riego():
        global riego_programado  # Usamos la variable global para guardar la programación
        fecha_selec_grafica = date_entry.get_date()
        hora_comienzo = hora_var.get()
        duracion = duracion_var.get()
        repetir = repetir_diariamente.get()

        if not fecha_selec_grafica or not hora_comienzo or not duracion:
            messagebox.showerror("Error", "Por favor complete todos los campos.")
            return

        try:
            # Convertir hora a formato datetime
            fecha_hora_comienzo_dt = datetime.datetime.strptime(f"{fecha_selec_grafica} {hora_comienzo}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            messagebox.showerror("Error", f"Formato de hora incorrecto: {e}")
            return

        schedules.append({"fecha": fecha_selec_grafica, "hora": hora_comienzo, "duracion": duracion, "repetir": repetir})

        print(f"Programación guardada: Fecha: {fecha_selec_grafica}, Hora: {hora_comienzo}, Duración: {duracion}, Repetir diariamente: {repetir}")
        riego_programado = {"fecha": fecha_selec_grafica, "hora": hora_comienzo, "duracion": duracion, "repetir": repetir}  # Guardar en la variable global
        save_all_schedules()
        #actualizar_estado_riego(f"Riego programado para {fecha_selec_grafica} a las {hora_comienzo}")
        actualizar_label_derecho(f"Riego inicia: \n{fecha_selec_grafica} a las {hora_comienzo}")  # Actualizar el label_derecho
        program_window.destroy()

    def save_all_schedules():
        global riego_id  # Usamos `global` para modificar `riego_id`
        for schedule in schedules:
            fecha_comienzo = schedule["fecha"]
            hora_comienzo = schedule["hora"]
            duracion = schedule["duracion"]
            repetir = schedule["repetir"]
            print(f"Fecha de comienzo: {fecha_comienzo}, Hora: {hora_comienzo}, Duración: {duracion} minutos, Repetir: {repetir}")
            try:
                fecha_hora_comienzo_dt = datetime.datetime.strptime(f"{fecha_comienzo} {hora_comienzo}", "%Y-%m-%d %H:%M")
                riego_id = check_riego(fecha_hora_comienzo_dt, int(duracion))  # Guardar ID del riego programado
            except ValueError as e:
                print(f"Error en el formato de fecha/hora: {e}")

    def check_riego(fecha_hora_comienzo_dt, duracion):
        global riego_programado
        global riego_en_curso, riego_id  # Para controlar el estado y el ID
        fecha_hora_actual = datetime.datetime.now()
        print(f"Fecha y hora actuales: {fecha_hora_actual}")
        if fecha_hora_comienzo_dt <= fecha_hora_actual:
            if not riego_en_curso:  # Solo activar el riego si no está en curso
                print("Activando el riego...")
                irrigation_var.set(1)
                gota_btn.config(image=gotaon)
                label_iconoriego.config(image=iconriegomapon)
                if ser is not None and ser.is_open:
                    ser.write(b"RIEGO_ON\n")
                else:
                    print("Serial connection not open. Cannot send RIEGO_ON command.")
                #toggle_irrigation()  # Activar el riego
                riego_en_curso = True  # Indicar que el riego está activo
                riego_id = root.after(duracion * 60000, finalizar_riego)  # Programar el apagado del riego
        else:
            print("Aún no es la hora de activar el riego.")
            riego_id = root.after(1000, check_riego, fecha_hora_comienzo_dt, duracion)
            riego_programado = False  # Reprogramar el check cada segundo

    def finalizar_riego():
        global riego_en_curso, riego_programado
        print("Apagando el riego...")
        toggle_irrigation()  # Desactivar el riego
        riego_en_curso = False  # Riego ya no está activo
        if isinstance(riego_programado, dict):
            if not riego_programado.get("repetir", False):  # Si no se debe repetir el riego
                riego_programado = False  # Restablecer el riego programado
               # actualizar_estado_riego("Sin riego programado")
                actualizar_label_derecho("Sin riego programado")  # Actualizar el label
            else:
                print("Riego repetido diariamente.")
        else:
            print("No hay riego programado.")
            riego_programado = False  # Asegurarse de restablecer el riego programado en cualquier caso
            #actualizar_estado_riego("Sin riego programado")
            actualizar_label_derecho("Sin riego programado")  # Actualizar el label
    
    def cancelar_riego():
        global riego_programado, riego_id, riego_en_curso
        if riego_id or riego_en_curso:
            if riego_id:
                root.after_cancel(riego_id)  # Cancela el riego programado
                riego_id = None  # Restablecer el ID del riego
            
                
            if riego_en_curso:
                print("Riego en marcha, apagando...")
                toggle_irrigation()  # Desactivar el riego
                riego_en_curso = False  # Riego ya no está activo
            riego_programado = False  # Restablecer el riego programad
            actualizar_label_derecho("Sin riego programado")  # Actualizar el estado en el label principal
            print("Riego cancelado.")
        else:
            messagebox.showinfo("Información", "No hay riegos activos para cancelar.")

    def actualizar_estado_riego(texto):
        """Actualiza el estado del riego en la interfaz."""
        actualizar_label_derecho.config(text=texto)
        #estado_riego_label.config(text=texto)

    # Creación de la ventana principal
    program_window = Toplevel(root)
    program_window.title("Programar Riego")
    program_window.attributes('-topmost', True)
    program_window.lift()

    # Calendario para seleccionar la fecha
    Label(program_window, text="Seleccionar fecha:").grid(row=1, column=0, padx=10, pady=10)
    date_entry = DateEntry(program_window, date_pattern='y-mm-dd', width=20, background='darkblue', foreground='white', borderwidth=2)
    date_entry.grid(row=1, column=1, padx=10, pady=10)

    # Entrada para la hora del riego
    hora_var = StringVar()
    Label(program_window, text="Hora de comienzo (HH:MM):").grid(row=2, column=0, padx=10, pady=10)
    Entry(program_window, textvariable=hora_var).grid(row=2, column=1, padx=10, pady=10)

    # Entrada para la duración del riego
    duracion_var = StringVar()
    Label(program_window, text="Duración (minutos):").grid(row=3, column=0, padx=10, pady=10)
    Entry(program_window, textvariable=duracion_var).grid(row=3, column=1, padx=10, pady=10)

    # Checkbutton para repetir diariamente
    Checkbutton(program_window, text="Repetir esta programación diariamente", variable=repetir_diariamente).grid(row=4, columnspan=2, padx=10, pady=10)

    # Espacio para mostrar si hay riego programado
   # estado_riego_label = Label(program_window, text="No hay riegos programados", fg="red")
   # estado_riego_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    # Botones para aceptar o cancela
    Button(program_window, text="Aceptar", command=obtener_datos_riego).grid(row=7, column=0, padx=10, pady=10, sticky="e")
    Button(program_window, text="Salir", command=program_window.destroy).grid(row=7, column=1, padx=10, pady=10)
    


# Muestra el menú contextual


def show_menu(event):
    global menu  # Hacer que 'menu' sea accesible globalmente
    if menu.winfo_ismapped():
        # Si el menú ya está abierto, lo cerramos
        menu.unpost()
    else:
        # Si el menú no está abierto, lo mostramos en la posición del clic
        menu.post(event.x_root, event.y_root)

def on_enter(event):
    event.widget.config(bg='#E0C078')  # Cambia a un color de fondo cuando el ratón está sobre el botón

def on_leave(event):
    event.widget.config(bg='#654321')

def expand():
    global cur_height, expanded
    cur_height += 10  # Aumenta la altura del frame en 10 píxeles
    rep = root.after(5, expand)  # Repite esta función cada 5 ms
    frame_desplegable.config(height=cur_height)  # Cambia la altura del frame al nuevo valor aumentado
    if cur_height >= max_h:  # Si la altura es mayor o igual al máximo permitido
        expanded = True  # El frame está completamente expandido
        root.after_cancel(rep)  # Detiene la repetición de la función
        fill()

def contract():
    global cur_height, expanded
    cur_height -= 10  # Reduce la altura del frame en 10 píxeles
    rep = root.after(5, contract)  # Llama a esta función cada 5 ms
    frame_desplegable.config(height=cur_height)  # Cambia la altura del frame al nuevo valor reducido
    if cur_height <= min_h:  # Si la altura es menor o igual a la altura mínima
        expanded = False  # El frame ya no está expandido
        root.after_cancel(rep)  # Detiene la repetición de la función

def confirmar_cierre():
    
    respuesta = messagebox.askyesno("Confirmar cierre", "¿Desea cerrar la ventana?")
    if respuesta:  # Si el usuario responde 'Sí'
        root.destroy()  # Cierra la ventana
        
def cerrar_ventana(event=None):
     confirmar_cierre()

def update_clock():
    global update_clock_id
    current_time = time.strftime("%H:%M:%S")  # Formato de hora
    clock_label.config(text=current_time)  # Actualizar el texto del label
    #side_frame.after(1000, update_clock)  # Actualizar cada 1 segund
    update_clock_id = side_frame.after(1000, update_clock)
def stop_updates():
    global update_clock_id  # Asegurarse de que se accede a la variable global
    if update_clock_id is not None:
        side_frame.after_cancel(update_clock_id)  # Cancelamos la actualización pendiente
        
def actualizar_datos():
    # Simulamos la obtención de datos del sensor
    humedad = random.randint(0, 100)  # Generar un valor aleatorio para humedad
    ph = round(random.uniform(0, 14), 2)  # Generar un valor aleatorio para pH

    # Formatear los textos
    label_textuno.set(f"Humedad de suelo: {humedad}%.\n pH: {ph}")
    label_textdos.set(f"Humedad de suelo: {humedad}%.\n H: {ph}")
    label_texttres.set(f"Humedad de suelo: {humedad}%.\n pH: {ph}")
    label_textcuatro.set(f"Humedad de suelo: {humedad}%.\n pH: {ph}")

    # Llama a esta función nuevamente después de 1000 ms (1 segundo)
    root.after(1000, actualizar_datos)

# Global para las ventanas abiertas
global open_windows
open_windows = {}

def open_frame_window(frame, label_text, sector_num):
    global open_windows
    
    # Verificar si ya existe una ventana para este frame
    if frame in open_windows and open_windows[frame].winfo_exists():
        # Si la ventana ya está abierta, traerla al frente
        open_windows[frame].lift()
        return
    
    # Crear una nueva ventana secundaria
    new_window = tk.Toplevel()
    new_window.title(f"Detalle del Sector {sector_num}")
    new_window.attributes('-topmost', True)
    new_window.lift()
    
    # Almacenar la referencia de la nueva ventana
    open_windows[frame] = new_window
    
    # Obtener el color de fondo del frame original
    frame_bg = frame.cget("bg")

    # Crear un nuevo frame dentro de la ventana secundaria
    new_frame = tk.Frame(new_window, bg=frame_bg)
    new_frame.pack(expand=True, fill="both")

    # Crear un label dentro del nuevo frame con el mismo texto que el frame original
    label = tk.Label(new_frame, text=label_text, bg=frame_bg, font=("Arial", 16))
    label.pack(expand=True)

    # Leer los datos del archivo CSV para obtener la información del sector correspondiente
    try:
        with open('datos_cultivo.csv', mode='r') as file:
            reader = csv.DictReader(file)
            sector_data = None
            for row in reader:
                if row['sector'] == str(sector_num):
                    sector_data = row
                    break

            # Si encontramos los datos, los mostramos en la ventana
            if sector_data:
                extra_label = tk.Label(new_frame, text=f"Relación NPK: {sector_data['npk']} \nEspecie: {sector_data['especie']} \nFecha de Siembra: {sector_data['fecha']} \nEtapa: {sector_data['etapa']}", bg=frame_bg, font=("Arial", 16))
                extra_label.pack(pady=10)
            else:
                messagebox.showwarning("Advertencia", f"No se encontraron datos para el sector {sector_num}. Vuelva hacer click para ver una version reducida")

    except FileNotFoundError:
        messagebox.showerror("Error", "El archivo datos_cultivo.csv no fue encontrado.")
    
    # Si la ventana se cierra, eliminar la referencia de la misma en el diccionario y cerrar la ventana
    new_window.protocol("WM_DELETE_WINDOW", lambda: close_window(frame))


def close_window(frame):
    # Cerrar la ventana y eliminar la referencia en el diccionario
    if frame in open_windows:
        open_windows[frame].destroy()  # Cierra la ventana manualmente
        open_windows.pop(frame)  
#######################
def cargar_datos(frame):
    # Crear una nueva ventana para cargar los datos
    cargar_window = tk.Toplevel()
    cargar_window.title("Cargar Datos del Sector")
    cargar_window.attributes('-topmost', True)
    cargar_window.lift()

    # Variables para los datos
    especie_var = tk.StringVar()  #una clase que crea una variable tipo str
    fecha_var = tk.StringVar() #Asociar con un widget para reflejar automáticamente los cambios de datos.
    npk_var = tk.StringVar()
    etapa_var = tk.StringVar()
    sector_var = tk.StringVar()  # Nueva variable para el número de sector
    repetir_var = tk.BooleanVar()  # Variable para el Checkbutton

    # Crear entradas para los datos
    tk.Label(cargar_window, text="Número de Sector:").pack(pady=5)
    tk.Entry(cargar_window, textvariable=sector_var).pack(pady=5)

    tk.Label(cargar_window, text="Especie:").pack(pady=5)
    tk.Entry(cargar_window, textvariable=especie_var).pack(pady=5)

    tk.Label(cargar_window, text="Fecha de Siembra:").pack(pady=5)
    tk.Entry(cargar_window, textvariable=fecha_var).pack(pady=5)

    tk.Label(cargar_window, text="Relación NPK:").pack(pady=5)
    tk.Entry(cargar_window, textvariable=npk_var).pack(pady=5)

    tk.Label(cargar_window, text="Etapa:").pack(pady=5)
    tk.Entry(cargar_window, textvariable=etapa_var).pack(pady=5)

    # Checkbutton para repetir los datos
    tk.Checkbutton(cargar_window, text="Repetir en otros sectores", variable=repetir_var).pack(pady=10)

    # Botón para guardar los datos
    def guardar_datos():
        especie = especie_var.get()
        fecha = fecha_var.get()
        npk = npk_var.get()
        etapa = etapa_var.get()
        sector = sector_var.get()

        # Verificar que todos los campos estén completos
        if not all([especie, fecha, npk, etapa, sector]):
            messagebox.showwarning("Advertencia", "Por favor, complete todos los campos.")
            return

        datos_sector = {
            "especie": especie,
            "fecha": fecha,
            "npk": npk,
            "etapa": etapa
        }

        datos_existentes = []
        archivo_csv = 'datos_cultivo.csv'
        if os.path.exists(archivo_csv):
            with open(archivo_csv, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['sector'] != sector:
                        datos_existentes.append(row)  # Mantener todos menos el sector actual

        # Sobrescribir el archivo CSV con los datos actualizados
        with open(archivo_csv, mode='w', newline='') as file:
            fieldnames = ["sector"] + list(datos_sector.keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            # Escribir los datos existentes
            writer.writerows(datos_existentes)

            # Guardar los datos para el sector especificado
            writer.writerow({"sector": sector, **datos_sector})

            # Si el Checkbutton está marcado, guardar en cuatro sectores
            if repetir_var.get():
                for i in range(1, 5):  # Repetir para los sectores 1, 2, 3, 4
                    writer.writerow({"sector": f"{int(sector) + i}", **datos_sector})

        # Cerrar la ventana antes de mostrar el mensaje de éxito
        cargar_window.destroy()
        messagebox.showinfo("Éxito", "Datos guardados con éxito.")

    tk.Button(cargar_window, text="Guardar Datos", command=guardar_datos).pack(pady=20)

############vboooooooooooooo
def habilitar_funciones():
    options_button.config(state="normal")
    camara_btn.config(state="normal")
    escucha_btn.config(state="normal")
    gota_btn.config(state="normal")
    lucesex_btn.config(state="normal")
    menu.entryconfig(0, state="normal")
    menu.entryconfig(1, state="normal")
    menu.entryconfig(2, state="normal")
    menu.entryconfig(3, state="normal")
    cancelar_luces_panel.config(state="normal")
    actualizar_btn.config(state="normal")

            
        
def deshabilitar_funciones():
    options_button.config(state="disabled")
    camara_btn.config(state="disabled")
    escucha_btn.config(state="disabled")
    gota_btn.config(state="disabled")
    lucesex_btn.config(state="disabled")
    menu.entryconfig(0, state="disabled")
    menu.entryconfig(1, state="disabled")
    menu.entryconfig(2, state="disabled")
    menu.entryconfig(3, state="disabled")
    cancelar_luces_panel.config(state="disabled")
    actualizar_btn.config(state="disabled")


#reconocimeintoRostro
# Inicializar la variable para almacenar el rostro registrado
rostro_registrado = None
cerrar_despues_login_facial = None

# Función para cargar el rostro registrado desde el CSV

# Función para registrar el rostro y guardar los datos en un CSV
def registrar_rostro():
    global rostro_registrado
    username = user_label_txt.cget("text")  # Obtener el nombre de usuario del label

    # Verificar si el usuario ya tiene un rostro registrado
    try:
        with open("rostros.csv", "r") as f:
            reader = list(csv.reader(f))
            rostro_existente = None
            
            for row in reader:
                if row[0] == username:  # Asumiendo que el nombre de usuario está en la primera columna
                    rostro_existente = row[1:]  # Obtener el rostro registrado
                    break
            
            if rostro_existente:
                tk.messagebox.showinfo("Información", "Ya tienes tus datos cargados.")
                print("Rostro ya registrado para el usuario.")
                return

    except FileNotFoundError:
        print("No se encontró el archivo de rostros. Se creará uno nuevo.")
    
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(frame_rgb)
        face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

        if face_encodings:
            rostro_registrado = face_encodings[0]  # Tomar el primer rostro detectado

            # Agregar el nombre y el rostro al archivo CSV
            try:
                with open("rostros.csv", "a", newline="") as f:
                    writer = csv.writer(f)
                    # Escribir el nombre del usuario y el rostro registrado
                    row_to_update = [username] + rostro_registrado.tolist()  # Convertir a lista y agregar
                    writer.writerow(row_to_update)
                tk.messagebox.showinfo("Éxito", "Rostro registrado y guardado en rostros.csv.")
                print("Rostro registrado y guardado en rostros.csv.")
            except Exception as e:
                print(f"No se pudo registrar el rostro: {e}")
                tk.messagebox.showerror("Error", "No se pudo registrar el rostro.")

            break

    cap.release()
# Función para abrir una ventana de reconocimiento facial
def reconocer_rostro():
    global cerrar_despues_login_facial
    global rostro_registrado

    # Crear una nueva ventana para el reconocimiento facial
    reconocer_window = tk.Toplevel()
    reconocer_window.title("Reconocimiento Facial")
    reconocer_window.attributes('-topmost', True)
    reconocer_window.lift()

    # Label para mostrar el video en tiempo real
    video_label = Label(reconocer_window)
    video_label.pack()

    # Label para mostrar el estado del reconocimiento facial
    status_label = Label(reconocer_window, text="Rostro no registrado", bg="green", font=("Helvetica", 16))
    status_label.pack(pady=10)

    # Inicializar la cámara
    cap = cv2.VideoCapture(0)

    # Función para capturar y mostrar el video en el label de Tkinter
    def update_frame():
        ret, frame = cap.read()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Buscar rostros en el frame
            face_locations = face_recognition.face_locations(frame_rgb)
            face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

            for face_encoding in face_encodings:
                # Leer el archivo rostros.csv
                try:
                    with open("rostros.csv", "r") as f:
                        reader = csv.reader(f)
                        for row in reader:
                            # Obtener el rostro registrado
                            registered_faces = np.array(row[1:], dtype=float)  # Suponiendo que el rostro está a partir de la segunda columna
                            match = face_recognition.compare_faces([registered_faces], face_encoding)
                            
                            if match[0]:  # Si hay coincidencia
                                status_label.config(text="Rostro detectado y coincide", bg="blue")
                                
                                # Mostrar el mensaje de éxito antes de cerrar la ventana
                                messagebox.showinfo("Éxito", "¡Inicio de sesión exitoso!", parent=reconocer_window)

                                # Cerrar la cámara y la ventana
                                cap.release()  # Cerrar la cámara
                                reconocer_window.destroy()  # Cerrar la ventana

                                # Ejecutar el código de éxito
                                habilitar_funciones()
                                usuario_logueado.set(1)  # Actualiza el valor de la variable
                                user_label.config(image=userlog)  # Cambia la imagen de usernolog a userlog
                                user_btn.config(text="Salir")  # Cambia el texto del botón
                                user_label_txt.config(text=row[0])  # Muestra el nombre del usuario
                                cerrar_despues_login_facial = True
                                
                                
                                
                                return cerrar_despues_login_facial

                except FileNotFoundError:
                    print("No se encontró el archivo de rostros.")
                    return

            # Si no hay coincidencias, actualizar el estado
            status_label.config(text="Rostro detectado pero no coincide", bg="red")

            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)

        video_label.after(10, update_frame)

    # Iniciar la actualización del video
    update_frame()

    # Cerrar la cámara al cerrar la ventana
    def on_closing():
        cap.release()
        reconocer_window.destroy()
        if 'reconocer_window' in locals():
            reconocer_window.protocol("WM_DELETE_WINDOW", on_closing)
    
  
# Función que habilita los botones después de un login exitoso
 

class LoginRegisterApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Sistema de Login/Registro")
        self.root.attributes('-topmost', True)
        self.root.lift()
        

        # Diccionario simulado de base de datos (usado para almacenar usuarios registrados)
        self.users_db = {}

        self.create_login_frame()
        

    def create_login_frame(self):
        
        """Crear la ventana de login"""
        self.clear_window()
        global cerrar_despues_login_facial 
        if cerrar_despues_login_facial == True:
            self.root.destroy()
        else:
            pass
            

        # Widgets del formulario de login
        tk.Label(self.root, text="Iniciar Sesión", font=("Arial", 16)).pack(pady=10)

        self.username_entry = self.create_labeled_entry("Usuario")
        self.password_entry = self.create_labeled_entry("Contraseña", show="*")

        tk.Button(self.root, text="Iniciar Sesión", command=self.login).pack(pady=10)
        tk.Button(self.root, text="Ir a Registro", command=self.create_register_frame).pack(pady=5)
        tk.Button(self.root, text="Reconocimiento Facial", command=reconocer_rostro).pack(pady=5)
      


    def create_register_frame(self):
        """Crear la ventana de registro"""
        self.clear_window()

        # Widgets del formulario de registro
        tk.Label(self.root, text="Registrar", font=("Arial", 16)).pack(pady=10)

        self.new_username_entry = self.create_labeled_entry("Usuario")
        self.new_password_entry = self.create_labeled_entry("Contraseña", show="*")
        self.confirm_password_entry = self.create_labeled_entry("Confirmar Contraseña", show="*")
        self.cod_seg_admi_entry = self.create_labeled_entry("Código de Seguridad (admin)")
        self.clave_producto_entry = self.create_labeled_entry("Clave de Producto")
        self.pregunta_seg_admi_entry = self.create_labeled_entry("Respuesta a la Pregunta de Seguridad")

        tk.Button(self.root, text="Registrar", command=self.register).pack(pady=10)
        tk.Button(self.root, text="Ir a Iniciar Sesión", command=self.create_login_frame).pack(pady=5)

    def create_labeled_entry(self, label, show=None):
        """Método auxiliar para crear un campo de texto con etiqueta"""
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        tk.Label(frame, text=label).pack(side=tk.LEFT)
        entry = tk.Entry(frame, show=show)
        entry.pack(side=tk.LEFT)
        
        return entry

    def clear_window(self):
        """Limpiar la ventana actual
        sigue el comentario abajo por eso es varias lineas"""
        for widget in self.root.winfo_children():
            widget.destroy()
    def close_window(self):
        """Método para cerrar la ventana de login"""
        self.root.destroy()

    def hash_password(self, password): #comentario simple 
        """Método para hashear contraseñas"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        cod_seg_admi = self.cod_seg_admi_entry.get()
        clave_producto = self.clave_producto_entry.get()
        pregunta_seg_admi = self.pregunta_seg_admi_entry.get()

        if not username or not password or not cod_seg_admi or not clave_producto or not pregunta_seg_admi:
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=self.root)
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Las contraseñas no coinciden", parent=self.root)
            return

       #Validación de existencia de usuario
        if username in self.users_db:
            messagebox.showerror("Error", "El nombre de usuario ya existe", parent=self.root)
            return

    # Validaciones adicionales para los campos nuevos
        if cod_seg_admi != "admin123":  # Código fijo de administrador
            messagebox.showerror("Error", "Código de Seguridad inválido", parent=self.root)
            return

        if clave_producto != "prod123":  # Clave de producto
            messagebox.showerror("Error", "Clave de Producto inválida", parent=self.root)
            return

        if pregunta_seg_admi.lower() != "ladra":  # Respuesta a la pregunta de seguridad
            messagebox.showerror("Error", "Respuesta incorrecta a la pregunta de seguridad", parent=self.root)
            return

    # Guardar el usuario en la base de datos simulada (diccionario)
        self.users_db[username] = self.hash_password(password)

    # Verificar si el archivo existe antes de abrir
        try:
            with open('usuarios_registrados.csv', mode='r', newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == username:
                        messagebox.showerror("Error", "Ya existe un usuario con ese nombre", parent=self.root)
                        return  # Si ya existe, termina la función
        except FileNotFoundError:
            pass
    # Agregar el nuevo usuario al archivo CSV
        with open('usuarios_registrados.csv', mode='a', newline='') as file: #with expresion de contexto se usa para abrir archivos y los cierra automaticamente
            writer = csv.writer(file)
            writer.writerow([username, self.hash_password(password), cod_seg_admi, clave_producto, pregunta_seg_admi])
            messagebox.showinfo("Éxito", "¡Registro exitoso!", parent=self.root)
            self.create_login_frame()  # Cambia a la ventana de inicio de sesión

    def login(self):  
        username = self.username_entry.get()
        password = self.password_entry.get()
        hashed_password = self.hash_password(password)

    # Leer el archivo CSV para buscar el usuario
        try:
            with open('usuarios_registrados.csv', mode='r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row:  # Asegurarse de que no sea una línea vacía
                            csv_username, csv_hashed_password = row[0], row[1]
                    
                    # Verificar si el usuario y la contraseña coinciden
                        if csv_username == username and csv_hashed_password == hashed_password:
                            messagebox.showinfo("Éxito", "¡Inicio de sesión exitoso!", parent=self.root)
                            habilitar_funciones()
                            usuario_logueado.set(1)  # Actualiza el valor de la variable
                            user_label.config(image=userlog)  # Cambia la imagen de usernolog a userlog
                            user_btn.config(text="Salir")  # Cambia el texto del botón
                            user_label_txt.config(text=username)  # Muestra el nombre del usuario
                            self.root.destroy()
                            return  # Terminar el método tras un inicio de sesión exitoso

        # Si no se encontró el usuario o la contraseña no coincide
            messagebox.showerror("Error", "Usuario o contraseña incorrectos", parent=self.root)
          
    
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró el archivo de usuarios" , parent=self.root)
           
def cancelar_riego_re():
        global riego_programado, riego_id, riego_en_curso, label_derecho, gota_btn, irrigation_var
        if riego_id or riego_en_curso:
            if riego_id:
                root.after_cancel(riego_id)  # Cancela el riego programado
                riego_id = None  # Restablecer el ID del riego
                pass
            if riego_en_curso:
                print("Riego en marcha, apagando...")
                if ser is not None and ser.is_open:
                    ser.write(b"RIEGO_OFF\n")
                else:
                    print("Serial connection not open. Cannot send RIEGO_OFF command.")
                irrigation_var.set(0)
                gota_btn.config(image=gotaoff)
                label_iconoriego.config(image=iconriegomapoff)
                
                riego_en_curso = False  # Riego ya no está activo
            riego_programado = False  # Restablecer el riego programad
            label_derecho.configure(text="Sin riego programado") # Actualizar el estado en el label principal
            print("Riego cancelado.")
        else:
            messagebox.showinfo("Información", "No hay riegos activos para cancelar.")

def cancelar_programacion_luces():
    """Cancela la programación de luces y actualiza la interfaz."""
    global schedules
    schedules.clear()
    if estado_focos.get() == 1:
        estado_focos.set(0)
        dibujo_frame.config(bg="#2E2E2E")
        frame_icons.config(bg="#2E2E2E")
        lucesex_btn.config(image=icono_led_off)
        label_iconoluz.config(image=iconluzmapoff)   
        if ser is not None and ser.is_open:
            ser.write(b"LUZ_OFF\n")
        else:
            print("Sin conexión al puerto serial, no se pudo ejecutar el comando")

    else:
        pass  # Limpia todas las programaciones de luces
    label_izq.config(text="Sin programación luces", fg="red")  # Actualiza el label para mostrar que no hay programación
    print("Programación de luces cancelada.")






############vboooooooooooooo
def open_login_register():
    if usuario_logueado.get() == 0:  # Si no hay usuario logueado
        new_window = tk.Toplevel(root)
        app = LoginRegisterApp(new_window)
        
    else:  # Si el usuario está logueado, cerrar sesión
        usuario_logueado.set(0)
        user_label.config(image=usernolog)  # Cambia de nuevo la imagen a usernolog
        user_btn.config(text="Login")  # Cambia el texto del botón de nuevo a Login
        user_label_txt.config(text="Nombre Usuario")
        deshabilitar_funciones()  # Re

def ventana_botones_grafico():
    """Función para abrir una ventana secundaria con los botones"""
    secondary_window = Toplevel()
    secondary_window.title("Opciones de Monitoreo")


    btn_energy_water = tk.Button(secondary_window, text="Consumo de Agua y Energía", command=show_energy_consumption)
    btn_energy_water.pack(side="top", padx=20, pady=10)

    # Botón para Humedad del Suelo
    btn_soil_humidity = tk.Button(secondary_window, text="Humedad del Suelo")
    btn_soil_humidity.pack(side="top", padx=20, pady=10)

    # Botón para Temperatura y Humedad del Ambiente
    btn_temp_humidity = tk.Button(secondary_window, text="Temperatura y Humedad del Ambiente")
    btn_temp_humidity.pack(side="top",padx=20, pady=10)

def show_energy_consumption():
    """Función para mostrar una ventana secundaria con gráficos de consumo de energía y agua"""
    # Crear una ventana secundaria
    energy_window = Toplevel()
    energy_window.title("Consumo de Energía y Agua en los 12 Meses")

    # Datos de consumo de energía (en kW) y agua (en litros)
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    energy_consumption = [300, 250, 220, 310, 400, 420, 450, 300, 280, 270, 260, 310]  # Mayo, Junio, Julio con mayor consumo
    water_consumption = [500, 600, 650, 500, 450, 400, 350, 300, 400, 700, 750, 800]  # Nov, Dic, Ene, Feb con mayor consumo

    # Crear una figura con dos gráficos en una fila
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))  # 1 fila, 2 columnas, se define una figura fig y dos sub gaficos ax1 ax2

    # Ajustar espacio entre los gráficos con `wspace`
    plt.subplots_adjust(wspace=0.5)  # Espacio horizontal entre los gráficos

    # Gráfico de barras de consumo de energía
    ax1.bar(months, energy_consumption, color=['gray' if i not in [4, 5, 6] else 'red' for i in range(12)])
    ax1.set_ylabel('Consumo de energía (kW)')
    ax1.set_title('Consumo de Energía en los 12 Meses')
    ax1.set_xticklabels(months, rotation=45, ha="right")

    # Gráfico de barras de consumo de agua
    ax2.bar(months, water_consumption, color=['gray' if i not in [10, 11, 0, 1] else 'blue' for i in range(12)])
    ax2.set_ylabel('Consumo de agua (litros)')
    ax2.set_title('Consumo de Agua en los 12 Meses')
    ax2.set_xticklabels(months, rotation=45, ha="right")

    # Integrar el gráfico en la ventana de Tkinter
    canvas = FigureCanvasTkAgg(fig, master=energy_window)
    canvas.draw()
    canvas.get_tk_widget().pack()

    energy_window.mainloop()
       
FONT_PATH = "ds-digital/DS-DIGII.TTF"  # Cambia esto por la ruta de tu archivo

def show_tooltip(event, text):
    """Función para mostrar un tooltip siempre hacia arriba"""
    tooltip = tk.Toplevel()
    tooltip.wm_overrideredirect(True)  # Remueve los bordes de la ventana
    # Ajustar la posición para que siempre aparezca hacia arriba del cursor
    x = event.x_root - 120 # Posición horizontal (a la derecha del cursor)
    y = event.y_root - 40  # Posición vertical (arriba del cursor)
    tooltip.wm_geometry(f"+{x}+{y}")  # Posición cercana al cursor, siempre hacia arriba
    label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1, font=("Arial", 11))
    label.pack()
    event.widget.tooltip = tooltip  # Asigna el tooltip al botón
def show_tooltip_de(event, text):
    """Función para mostrar un tooltip siempre hacia arriba"""
    tooltip = tk.Toplevel()
    tooltip.wm_overrideredirect(True)  # Remueve los bordes de la ventana
    # Ajustar la posición para que siempre aparezca hacia arriba del cursor
    x = event.x_root + 40 # Posición horizontal (a la derecha del cursor)
    y = event.y_root - 40  # Posición vertical (arriba del cursor)
    tooltip.wm_geometry(f"+{x}+{y}")  # Posición cercana al cursor, siempre hacia arriba
    label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1, font=("Arial", 11))
    label.pack()
    event.widget.tooltip = tooltip  # Asigna el tooltip al botón

def hide_tooltip(event):
    """Función para ocultar el tooltip cuando el mouse sale del botón"""
    if hasattr(event.widget, 'tooltip'):
        event.widget.tooltip.destroy()

def bind_tooltip(button, tooltip_text):
    """Función general para asignar eventos de mostrar y ocultar tooltip"""
    button.bind("<Enter>", lambda e: show_tooltip(e, tooltip_text))
    button.bind("<Leave>", hide_tooltip)
        
def bind_tooltip_de(button, tooltip_text):
    """Función general para asignar eventos de mostrar y ocultar tooltip"""
    button.bind("<Enter>", lambda e: show_tooltip_de(e, tooltip_text))
    button.bind("<Leave>", hide_tooltip)

def avisar_riego_pro():
        global riego_programado
        global riego_en_curso
        if riego_programado == None or riego_programado == False or riego_en_curos == False:
            label_derecho.configure(text="Sin riego programado")





    
        

if __name__ == "__main__":   #name es un atributo de python el modulo este al ejecutarse directamente toma el nombre de main"
    root = tk.Tk()  # clasetk
    root.title("Invernadero")#si este modulo estuviera importado en otro modulo su nombre name seria distinto de main"
    root.geometry("1366x768")  # 1200x700 opcion normal
    root.configure(background="#A89B8C") #A89B8C 

   # Panel lateral izquierdo con botones de opciones
    label_azul = Label(root, width=15, height=700, bg="#654321")
    label_azul.pack(side="left", fill="y")

    frame_azul = Frame(label_azul)
    frame_azul.pack(fill="both", padx=0, pady=0)
    frame_azul.configure(background="#654321")   #654321

  
    #boton de opciones
    img_opc = Image.open("opcionesv4.png")
    img_opc = img_opc.resize((64,64), Image.Resampling.LANCZOS)
    img_opc = ImageTk.PhotoImage(img_opc)
    options_button = Button(
        frame_azul, image=img_opc, bg="#654321",fg="black", borderwidth=0, highlightthickness=0, relief="flat")
    options_button.config(state="disabled")
    
    # Asegura que el botón llene horizontalmente el frame
    options_button.pack(pady=20)
    options_button.bind("<Enter>", on_enter)
    options_button.bind("<Leave>", on_leave)
    options_button.bind("<Button-1>", show_menu)
    bind_tooltip_de(options_button, "Menu de opciones y configuraciones")

   
    
    

    menu = Menu(root, tearoff=0)

    programar_riego = menu.add_command(label="Programar riego", command=open_program_schedule, state="disabled")
    programar_luces = menu.add_command(label="Programar luces", command=open_light_schedule, state="disabled")
    historial = menu.add_command(label="Historial", command=ventana_botones_grafico, state="disabled") 
    menu.add_command(label="Cargar datos cultivo", command=lambda: cargar_datos(Frame))

   # Marco principal
    main_frame = Frame(root)
    main_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
    main_frame.configure(background="#A89B8C")
    root.update()  # Actualiza la geometría del root para reflejar el nuevo ancho
    
    # Ejemplo de cómo agregar texto al widget de terminal

    # Marco del gráfico
    graph_frame = Frame(main_frame, width=600, height=400,
                        bg="green", borderwidth=0, highlightthickness=0)
    graph_frame.pack(side="left", fill="both", expand=True, padx=1, pady=1)
    # Arrays para almacenar datos de temperatura, humedad y tiempo
    temp_array = [0] * 20
    humidity_array = [0] * 20
    time_array = [0] * 20
    soil_humidity = 0
    start_time = time.time()

# Crear gráfico inicial y canvas
    fig = Figure(figsize=(7.6, 4), dpi=100)
    ax1 = fig.add_subplot(111)

# Graficar temperatura
    line_temp, = ax1.plot(time_array, temp_array, marker='o', linestyle='-', color='b', label='Temp.')
    ax1.set_title('Temperatura y Humedad ambiente')
    ax1.set_xlabel('Tiempo (minutos)')
    ax1.set_ylabel('Temperatura °C', color='b')
    ax1.set_ylim(0, 100)
    ax1.set_yticks(np.arange(0, 101, 5))

# Graficar humedad ambiental
    ax2 = ax1.twinx()
    line_humidity, = ax2.plot(time_array, humidity_array, marker='s', linestyle='-', color='r', label='% Hum. Ambiente')
    ax2.set_ylabel('% Humedad del ambiente', color='r')
    ax2.set_ylim(0, 100)
    ax2.set_yticks(np.arange(0, 101, 5))

# Leyendas
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

# Colocar el canvas en el frame
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    def update_graph():
        global ser
        global temp_array, humidity_array, soil_humidity, time_array, start_time

        if ser is None or not ser.is_open:
            return

        if ser.in_waiting > 0:
            data = ser.readline().decode(errors='ignore').strip()
            try:
                if data.startswith("T:") and ",S:" in data:
                    temp_str = data.split(",")[0].replace("T:", "")
                    humedad_ambiental = data.split(",")[1].replace("S:", "")
                
                    temperatura = float(temp_str)
                    humedad_amb = float(humedad_ambiental)

                    temp_array.append(temperatura)
                    humidity_array.append(humedad_amb)

                # Actualizar el tiempo en minutos
                    elapsed_time = (time.time() - start_time) / 60
                    time_array.append(elapsed_time)

                # Limitar el tamaño de las listas a los últimos 20 valores
                    temp_array = temp_array[-20:]
                    humidity_array = humidity_array[-20:]
                    time_array = time_array[-20:]

                # Actualizar los datos del gráfico
                    ax1.clear()  # Limpia el gráfico
                    ax2.clear()

                # Configuración de ejes
                    ax1.set_title('Temperatura y Humedad ambiente')
                    ax1.set_xlabel('Tiempo (minutos)')
                    ax1.set_ylabel('Temperatura °C', color='b')
                    ax1.set_ylim(0, 100)
                    ax1.set_yticks(np.arange(0, 101, 5))

                # Graficar temperatura
                    ax1.plot(time_array, temp_array, marker='o', linestyle='-', color='b', label='Temp.')
                    ax1.legend(loc='upper left')

                # Configuración de ejes para humedad
                    ax2.set_ylabel('% Humedad del ambiente', color='r')
                    ax2.set_ylim(0, 100)
                    ax2.set_yticks(np.arange(0, 101, 5))

                # Graficar humedad
                    ax2.plot(time_array, humidity_array, marker='s', linestyle='-', color='r', label='% Hum. Ambiente')
                    ax2.legend(loc='upper right')

                # Refrescar el gráfico
                    canvas.draw()

                # Actualizar etiquetas y condiciones de alarma
                    temp_label.config(text=f"{temperatura:.1f}°C")
                    humidity_label.config(text=f"{humedad_amb} %")
                    act_label_hum_suelo(soil_humidity, 5.9)

                # Colorear y verificar alarmas
                    check_critical_levels(temp_label, temperatura, 29, "¡Urgente! Temperatura crítica")
                    temp_label.config(bg="red" if temperatura > 22.0 or temperatura < 12.0 else "#2E2E2E")
                    humidity_label.config(bg="red" if humedad_amb > 70 or humedad_amb < 15 else "#2E2E2E")

                else:
                    soil_humidity = int(data)
                    act_label_hum_suelo(soil_humidity, 5.9)

            except ValueError:
                print("Error: Could not parse data")

        root.after(1000, update_graph)
    update_graph()

# Frame para el contenido
    dibujo_frame = tk.Frame(graph_frame, bg="#2E2E2E", width=800, height=250)
    dibujo_frame.pack(side="bottom", fill="both", padx=1, pady=0, expand=False)
    dibujo_frame.pack_propagate(False)

    iconluzmapon = PhotoImage(file="luzonmap.png")
    iconluzmapoff = PhotoImage(file="luzoffmap.png")
    iconriegomapon = PhotoImage(file="water-dropon.png")
    iconriegomapoff = PhotoImage(file="water-dropoff.png")
    fanon = PhotoImage(file="fan_on.png")
    fanoff = PhotoImage(file="fan_off.png")


     
    # Crear un Frame más ancho para simular el tanque de agua
    # Crear un estilo para la barra de progreso y cambiar el color de fondo

    frame_icons = tk.Frame(dibujo_frame, bg="#2E2E2E", width=800, height=60) ##A0A0A0 150x60 orf
    frame_icons.pack(side="top", fill="y", padx=0, pady=0)
    frame_icons.pack_propagate(False)



    
    
    global label_derecho
    global label_izq
    
    label_derecho = tk.Label(frame_icons, text="Sin riego programado" , fg="green", font=("Arial", 11), bg="#2E2E2E")
    label_derecho.pack(side="right", fill="x", padx=0, pady=0)
    
    
    label_izq = tk.Label(frame_icons, text="Sin programación luces" , fg="green",bg="#2E2E2E", font=("Arial", 11))
    label_izq.pack(side="left", fill="x", padx=0, pady=0)


    new_contenedor = tk.Frame(frame_icons, bg="#2E2E2E", width=150, height=60) ##A0A0A0 150x60 orf
    new_contenedor.pack(side="top", fill="y", padx=0, pady=0)
    new_contenedor.pack_propagate(False)

    

   
   
    
    label_iconoluz = Button(new_contenedor, image=iconluzmapoff, bg="#424242")
    label_iconoluz.pack(side="left", fill="y" , expand=True)
    label_iconoluz.pack_propagate(False)
    label_iconoluz.image = iconluzmapon




    label_iconoriego = Button(new_contenedor, image=iconriegomapoff, bg="#424242")
    label_iconoriego.pack(side="right", fill="y" , expand=True)
    label_iconoriego.pack_propagate(False)
    label_iconoriego.image = iconluzmapon

    
# Crear un Frame más ancho para simular el tanque de agua
    progress_framea = tk.Frame(dibujo_frame, width=150, height=200, bg="blue")  # Aumentar el ancho del frame
    progress_framea.pack(side="right", fill="y", padx=0, pady=0) # Colocar a la derecha del frame
    progress_framea.pack_propagate(True)
    style = ttk.Style()
    style.configure("Vertical.TProgressbar", thickness=150, relief="Flat")  # Ajusta el grosor de la barra (50px de ancho)

# Barra de progreso (orientación vertical, dentro del frame que controla el ancho)
    progress_agua = ttk.Progressbar(
    progress_framea, orient="vertical", mode="determinate", style="Vertical.TProgressbar"
)

# Asegurar que la barra de progreso ocupe todo el espacio del Frame
    progress_agua.pack(fill="both", expand=True)
    progress_agua.pack_propagate(True)
    progress_agua["value"] = 80

    label_text = tk.StringVar()
    label_text.set("80%. pH 7.4")  # Establecer el texto

# Crear una etiqueta y asociarla con el StringVar
    labelp = tk.Label(progress_framea, textvariable=label_text, bg="white", font=("Arial", 14))
    labelp.place(relx=0.5, rely=0.5, anchor='center')  # Colocar el texto en el centro de la barra

    label_textp = tk.StringVar()
    label_textp.set("Tanque de agua")  # Establecer el texto

    

    labelh = tk.Label(progress_framea, textvariable=label_textp, bg="white", font=("Arial", 11))
    labelh.place(relx=0.5, rely=0.1, anchor='s')  # Colocar el texto en el centro de la barra




    # Crear StringVar para cada label
    textuno_var = tk.StringVar()
    textdos_var = tk.StringVar()
    texttres_var = tk.StringVar()
    textcuatro_var = tk.StringVar()

# Establecer el texto en cada StringVar
    textuno_var.set("Humedad de suelo: %.\n pH: 4.5")
    textdos_var.set("Humedad de suelo: %.\n pH: 4.5")
    texttres_var.set("Humedad de suelo: %.\n pH: 4.5")
    textcuatro_var.set("Humedad de suelo: %.\n pH: 4.5")

# Crear un Frame para cada etiqueta
    frame_suno = tk.Frame(dibujo_frame, bg="lightgreen", width=200, height=160)
    frame_suno.place(x=4, y=82, width=180, height=160)

    frame_sdos = tk.Frame(dibujo_frame, bg="lightgreen", width=200, height=100)
    frame_sdos.place(x=188, y=82, width=180, height=160)

    frame_stres = tk.Frame(dibujo_frame, bg="lightgreen", width=200, height=100)
    frame_stres.place(x=372, y=82, width=180, height=160)

    frame_scuatro = tk.Frame(dibujo_frame, bg="lightgreen", width=200, height=100)
    frame_scuatro.place(x=556, y=82, width=180, height=160) 

# Crear etiquetas dentro de cada Frame
    text_labeluno = tk.Label(frame_suno, textvariable=textuno_var, bg="lightgreen", font=("Arial", 12))
    text_labeluno.pack(expand=True, fill="both")

    text_labeldos = tk.Label(frame_sdos, textvariable=textdos_var, bg="lightgreen", font=("Arial", 12))
    text_labeldos.pack(expand=True, fill="both")

    text_labeltres = tk.Label(frame_stres, textvariable=texttres_var, bg="lightgreen", font=("Arial", 12))
    text_labeltres.pack(expand=True, fill="both")

    text_labelcuatro = tk.Label(frame_scuatro, textvariable=textcuatro_var, bg="lightgreen", font=("Arial", 12))
    text_labelcuatro.pack(expand=True, fill="both")
    text_labeluno.bind("<Button-1>", lambda event: open_frame_window(frame_suno, "-Sector1-\n Humedad de suelo: %.\n pH: 4.5", sector_num=1))
    text_labeldos.bind("<Button-1>", lambda event: open_frame_window(frame_sdos, "-Sector2- \n Humedad de suelo: %.\n pH: 4.5", sector_num=2))
    text_labeltres.bind("<Button-1>", lambda event: open_frame_window(frame_stres, "-Sector3- \n Humedad de suelo: %.\n pH: 4.5", sector_num=3))
    text_labelcuatro.bind("<Button-1>", lambda event: open_frame_window(frame_scuatro, "-Sector4- \n Humedad de suelo: %.\n pH: 4.5",sector_num=4))
    







  #  datos_tanque = tk.Frame(dibujo_frame, width=100, height=200, bg="blue")  # Aumentar el ancho del frame
   # datos_tanque.pack(side="right", fill="y", padx=0, pady=0)
   
    # Marco lateral con botones y barras de progreso

    side_frame = Frame(main_frame, width=150, height=200) #A89B8C
    side_frame.pack(side="right", fill="y", padx=0, pady=1)
    side_frame.pack_propagate(False) 


    frame_width = 300  # Ancho deseado del frame desplegable
    min_h = 23  # Altura mínima (cuando está contraído)
    max_h = 200  # Altura máxima (cuando está expandido)
    cur_height = min_h

# Coloca el frame en la parte inferior, centrado horizontalmente
    frame_desplegable = Frame(root, bg='yellow', width=frame_width, height=cur_height)
    frame_desplegable.place(relx=0.5, rely=1.0, anchor='s')  # Centrado en la parte inferior

# Evita que el frame cambie de tamaño según el contenido
    frame_desplegable.pack_propagate(False)

# Añadir un widget de texto dentro del frame
    terminal = Text(frame_desplegable, bg="black", fg="white")
    terminal.pack(fill="both", expand=True)
    frame_desplegable.bind('<Enter>', lambda e: expand())
    frame_desplegable.bind('<Leave>', lambda e: contract())
    

    # Imágenes de estado del riego y luces
    riego_off_image = PhotoImage(file="riego_off.png")
    riego_on_image = PhotoImage(file="riego_on.png")
    icono_led_on = PhotoImage(file="newfocoon.png")
    icono_led_off = PhotoImage(file="newfocooff.png")
    microoff = PhotoImage(file="newmicrooff.png")
    microon = PhotoImage(file="newmicroon.png")
    boton_central = PhotoImage(file="botoncentral.png")
    gotaon = PhotoImage(file="gotaver.png")
    gotaoff = PhotoImage(file="gotaoff.png")
    userlog = PhotoImage(file="userlog.png")
    usernolog = PhotoImage(file="usernolog.png")
  
    ## label usur
    usuario_logueado = IntVar(value=0)
    print(usuario_logueado.get())
    user_label = tk.Label(side_frame,image=usernolog, width=10)
    user_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
    user_label_txt = tk.Label(side_frame, text="Nombre Usuario", font=("Arial", 11), width=10)
    user_label_txt.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
    user_btn = tk.Button(side_frame, text="Login", command=open_login_register, width=10)
    user_btn.grid(row=2, column=0, padx=10, pady=3,  sticky='nsew')

    cancelar_riego_panel = tk.Button(side_frame, text="Cancelar \n Programación \nRiego", width=10, command=cancelar_riego_re)
    cancelar_riego_panel.grid(row=3, column=0, padx=10, pady=3,  sticky='nsew')
    bind_tooltip(cancelar_riego_panel, "Cancelar una programación \nde riego")
    cancelar_luces_panel = tk.Button(side_frame, text="Cancelar \n Programación \nLuces", command=cancelar_programacion_luces, width=10, state="disabled")
    bind_tooltip(cancelar_luces_panel, "Cancelar una programación \nde luces")
    cancelar_luces_panel.grid(row=4, column=0, padx=10, pady=3,  sticky='nsew')

    
    



    #luces y riego 


 

    ##
    clima_ext = tk.Label(side_frame, text="Clima exterior", font=("Arial", 11), width=12)
    clima_ext.grid(row=5, column=0, padx=10, pady=(170,10))
    clima_label = tk.Label(side_frame, text="Temperatura", font=("Arial", 11), width=13)
    clima_label.grid(row=6, column=0, padx=10, pady=(10))
    clima_label_uno = tk.Label(side_frame, text="Humedad", font=("Arial", 11), width=10)
    clima_label_uno.grid(row=7, column=0, padx=10, pady=10)
    #clima_label_dos = tk.Label(side_frame, text="ss", font=("Arial", 11), width=10)
    #clima_label_dos.grid(row=8, column=0, padx=10, pady=1)
    #obtener_clima()
    

    # Botón para actualizar el clima
    irrigation_var = tk.IntVar(value=0)
   
   
    actualizar_btn = tk.Button(side_frame, text="Registro Facial", command=registrar_rostro , width=10, state="disabled")
    actualizar_btn.grid(row=9, column=0, padx=10, pady=10)
    bind_tooltip(actualizar_btn, "Inicia el reconocimiento facial")
    camara_btn = tk.Button(side_frame, text="camara", command=reconocer_puno, width=10)
    camara_btn.grid(row=10, column=0, padx=1, pady=1)
    camara_btn.config(state="disabled")
    bind_tooltip(camara_btn, "Realizar acciones por gestos")
    


    ##

    custom_font = tkFont.Font(family="DS-Digital", size=14)
    root.option_add('*Font', custom_font)

    #hora
    clock_label = tk.Label(side_frame, text="", font=custom_font, fg="black", width=10)
    clock_label.grid(row=11, column=0, padx=1, pady=(1, 0))

# Iniciar el reloj
    update_clock()
    #jjs

    # Control de escucha
    escucha_var = IntVar(value=0)
    escucha_btn = Button(
        frame_azul, image=microoff, command=start_listening, bd=0, bg="#654321", highlightthickness=0, relief="flat")
    escucha_btn.pack(side="top", pady=20)
    escucha_btn.config(state="disabled")
    bind_tooltip_de(escucha_btn, "Comandos por voz")

#prueba
    irrigation_var = IntVar(value=0)
    global gota_btn
    gota_btn = Button(
        frame_azul, image=gotaoff, command=toggle_irrigation, bd=0, bg="#654321", highlightthickness=0, relief="flat")
    gota_btn.pack(side="top", pady=20)
    gota_btn.config(state="disabled")
    bind_tooltip_de(gota_btn, "Encender riego")



##############

    estado_focos = IntVar(value=0)
    lucesex_btn = Button(
        frame_azul, image=icono_led_off, command=control_luces, bd=0, bg="#654321", highlightthickness=0, relief="flat")
    lucesex_btn.pack(side="top", pady=20)
    lucesex_btn.config(state="disabled")
    bind_tooltip_de(lucesex_btn, "Encender luces")




###################
    estado_refri = IntVar(value=0)
    refri_btn = Button(
        frame_azul, image=fanoff, command=control_refri, bd=0, bg="#654321", highlightthickness=0, relief="flat")
    refri_btn.pack(side="top", pady=20)
    bind_tooltip_de(refri_btn, "Encender ventilacion")


    

    
    #boton inicio y apagado sistema

    # Botón central (debajo del botón de opciones)
   #boton de opciones
    btn_main = Image.open("botoncentral.png")
    btn_main = btn_main.resize((64,64), Image.Resampling.LANCZOS)
    btn_main = ImageTk.PhotoImage(btn_main)
    button_var = IntVar(value=0)
    toggle_btn = Button(
    frame_azul, image=btn_main, bg="#8B0000", borderwidth=1, highlightthickness=0, relief="flat", command=toggle_button)
# Empaquetar el botón debajo del botón de opciones
    toggle_btn.pack(side="top", pady=(134, 5))
    bind_tooltip_de(toggle_btn, "Prender o Apagar el sistema")
   

  
    data_frame = tk.Frame(main_frame, bg="#2E2E2E")  # Fondo oscuro para elegancia
    data_frame.pack(side="right", fill="y", padx=10, pady=1)
    data_frame.pack_propagate(False)

# Estilo para las etiquetas de datos grandes
    label_style_large = ("Arial", 32, "bold")
    label_style_small = ("Arial", 14, "italic")

# Estilo de colores modernos
    color_primary = "#EAECEE"  # Texto claro
    color_secondary = "#AAB7B8"  # Texto más pequeño
    color_bg = "#2E2E2E"  # Fondo oscuro

# Etiqueta de temperatura (dato grande)
    temp_label = tk.Label(data_frame, text=" °C", font=label_style_large, bg=color_bg, fg=color_primary)
    temp_label.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
    

# Etiqueta pequeña debajo para aclarar el dato
    temp_sub_label = tk.Label(data_frame, text="Temperatura ambiente", font=label_style_small, bg=color_bg, fg=color_secondary)
    temp_sub_label.grid(row=1, column=0, padx=20, pady=15, sticky="nsew")

# Etiqueta de humedad del ambiente
    humidity_label = tk.Label(data_frame, text=" %", font=label_style_large, bg=color_bg, fg=color_primary)
    humidity_label.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

# Etiqueta pequeña debajo para aclarar el dato
    humidity_sub_label = tk.Label(data_frame, text="Humedad ambiente", font=label_style_small, bg=color_bg, fg=color_secondary)
    humidity_sub_label.grid(row=4, column=0, padx=20, pady=15, sticky="nsew")

# Etiqueta de luz
    light_label = tk.Label(data_frame, text="75%", font=label_style_large, bg=color_bg, fg=color_primary)
    light_label.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

# Etiqueta pequeña debajo para aclarar el dato
    light_sub_label = tk.Label(data_frame, text="Luz", font=label_style_small, bg=color_bg, fg=color_secondary)
    light_sub_label.grid(row=6, column=0, padx=20, pady=15, sticky="nsew")


# Etiqueta de luz
    consumokw_label = tk.Label(data_frame, text="1.2 kW/h", font=label_style_large, bg=color_bg, fg=color_primary)
    consumokw_label.grid(row=7, column=0, padx=20, pady=10, sticky="nsew")

# Etiqueta pequeña debajo para aclarar el dato
    consumokw_sub_label = tk.Label(data_frame, text="kWattios/hora", font=label_style_small, bg=color_bg, fg=color_secondary)
    consumokw_sub_label.grid(row=8, column=0, padx=20, pady=5, sticky="nsew")

# Etiqueta de luz
    agua_label = tk.Label(data_frame, text="1000 L/M", font=label_style_large, bg=color_bg, fg=color_primary)
    agua_label.grid(row=9, column=0, padx=20, pady=10, sticky="nsew")

# Etiqueta pequeña debajo para aclarar el dato
    agua_sub_label = tk.Label(data_frame, text="Litros/Mes", font=label_style_small, bg=color_bg, fg=color_secondary)
    agua_sub_label.grid(row=10, column=0, padx=20, pady=5, sticky="nsew")


# Etiqueta de gases
    carbono_label = tk.Label(data_frame, text="1000 C02", font=label_style_large, bg=color_bg, fg=color_primary)
    carbono_label.grid(row=11, column=0, padx=20, pady=10, sticky="nsew")

# Etiqueta pequeña debajo para aclarar el dato
    carbono_sub_label = tk.Label(data_frame, text="partes por Millon", font=label_style_small, bg=color_bg, fg=color_secondary)
    carbono_sub_label.grid(row=12, column=0, padx=20, pady=5, sticky="nsew")

    ### prueba progres 4
   # Ajustar progress_bar4 y su label para que estén debajo de progress_bar (Temperatura)
   # progress_bar4 = ttk.Progressbar(
   # progress_frame, orient="vertical", length=150, mode="determinate")
   ### progress_label4.grid(row=3, column=2, padx=10, pady=(1, 5), sticky="n")  # Misma reducción de pady y ajuste con sticky


    ###

    #progress_bar['value'] = 25
   # progress_bar2['value'] = 0

    # llllllllllllllllllllllllllllllllllllllllllll

    # Inicializa el gráfico con datos vacíos
    #fig = plot_data(time_array, temp_array, humidity_array)
    #canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    #canvas.draw()
    #canvas.get_tk_widget().pack()
    

    
    root.bind("<Control-i>", toggle_button)
    root.bind("<Control-e>", start_listening)
    root.bind("<Control-r>", open_program_schedule)
    root.bind("<Control-l>", open_light_schedule)
    root.bind("<Alt-l>", control_luces)
    root.bind("<Alt-r>", toggle_irrigation)
    root.bind("<Control-c>", cerrar_ventana)
    root.protocol("WM_DELETE_WINDOW", stop_updates)
    root.protocol("WM_DELETE_WINDOW", confirmar_cierre)
    


    
   # root.mainloop()

app = Flask(__name__)

@app.route('/update_lights', methods=['POST'])
def update_lights():
    global estado_focos, luces_espera

    # Llamar a control_luces() para cambiar el estado
    control_luces()
    
    # Determinar el nuevo estado después del cambio
    if estado_focos.get() == 1:
        mostro = "ENCENDIDO" if not luces_espera else "Espera 40s desde la ultima acción para volver hacer click"
    elif estado_focos.get() == 0:
        mostro = "APAGADO" if not luces_espera else "Espera 40s desde la ultima acción para volver hacer click"
    
    return jsonify({"message": "Luces cambiadas", "estado": mostro})
    
@app.route('/get_irrigation_state', methods=['GET'])
def get_irrigation_state():
    global estado_riego, riego_espera

    # Consultar el estado actual del riego sin cambiarlo
    if irrigation_var.get() == 1:
        estado = "ENCENDIDO" if not riego_espera else "Espera 40s desde la última acción para volver hacer clic"
    else:
        estado = "APAGADO" if not riego_espera else "Espera 40s desde la última acción para volver hacer clic"
    
    return jsonify({"estado": estado})

@app.route('/update_irrigation', methods=['POST'])
def update_irrigation():
    global riego_espera, irrigation_var, toggle_irrigation

    # Llamar a control_riego() para cambiar el estado
    toggle_irrigation()
    
    # Determinar el nuevo estado después del cambio
    if irrigation_var.get() == 1:
        estado = "ENCENDIDO" if not riego_espera else "Espera 40s desde la última acción para volver hacer clic"
    elif irrigation_var.get() == 0:
        estado = "APAGADO" if not riego_espera else "Espera 40s desde la última acción para volver hacer clic"
    
    return jsonify({"message": "Riego cambiado", "estado": estado})

@app.route('/get_lights_state', methods=['GET'])
def get_lights_state():
    global estado_focos, luces_espera

    # Consultar el estado actual de las luces sin cambiarlo
    if estado_focos.get() == 1:
        estado = "ENCENDIDO" if not luces_espera else "Espera 40s desde la última acción para volver hacer clic"
    else:
        estado = "APAGADO" if not luces_espera else "Espera 40s desde la última acción para volver hacer clic"
    
    return jsonify({"estado": estado}) #combierte datos de py en json jsonify



# Iniciar la aplicación Flask en un puerto específico
def start_flask():
    app.run(host='0.0.0.0', port=5000)

# Tkinter main loop
def start_tkinter():
    root.mainloop()

if __name__ == "__main__":
    import threading

    # Ejecutar Flask en un hilo separado
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Ejecutar Tkinter en el hilo principal
    start_tkinter()

   