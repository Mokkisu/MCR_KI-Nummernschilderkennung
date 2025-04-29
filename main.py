import cv2
import pandas as pd
import numpy as np
import time
import threading
from datetime import datetime
import customtkinter as ctk
from PIL import Image, ImageTk
from ultralytics import YOLO
import pytesseract
import paho.mqtt.client as mqtt

# MQTT Setup
mqtt_broker = "192.168.99.138"  # z.B. "localhost" oder IP-Adresse
mqtt_port = 1883  # Standard-Port für MQTT
mqtt_topic_granted = "parkhaus/status"

mqtt_client = mqtt.Client()
#mqtt_client.username_pw_set(username='client', password='123456')
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.loop_start()

# Pfad zu Tesseract definieren
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# YOLO-Model für Nummernschilder laden (angepasstes Modell erforderlich)
yolo_model = YOLO("best.pt")  

erlaubte_nummern = set()
illegale_nummern = set()

def lade_nummern(csv_datei):
    try:
        with open(csv_datei, "r") as file:
            content = file.read().strip()
            return set(content.split(";")) if content else set()
    except FileNotFoundError:
        return set()

def speichere_nummern(csv_datei, nummern):
    with open(csv_datei, "w") as file:
        file.write(";".join(nummern))

erlaubte_nummern = lade_nummern("erlaubt.csv")
illegale_nummern = lade_nummern("illegal.csv")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)

frame_lock = threading.Lock()
latest_frame = None

def capture_frames():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if ret:
            with frame_lock:
                latest_frame = frame

def erkenne_nummernschild(frame):
    results = yolo_model.predict(frame, conf=0.5, verbose=False)
    nummer = ""
    for result in results:
        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
            if int(cls) != 0:  # Ersetze 0 mit der tatsächlichen Klasse für Nummernschilder
                continue
            x1, y1, x2, y2 = map(int, box[:4])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            nummernschild = frame[y1:y2, x1:x2]

            if nummernschild.size == 0:
                continue
            
            nummernschild = cv2.resize(nummernschild, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LINEAR)

            # Graustufen
            graustufen = cv2.cvtColor(nummernschild, cv2.COLOR_BGR2GRAY)

            # Farben invertieren
            invertiert = cv2.bitwise_not(graustufen)

            # Kontrast verbessern mit CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            kontrastbild = clahe.apply(invertiert)

            # Glätten
            geglättet = cv2.GaussianBlur(kontrastbild, (5, 5), 0)

            # Schwellenwert setzen
            # Manuelles Thresholding statt Otsu
            _, schwellenwert = cv2.threshold(geglättet, 185, 255, cv2.THRESH_BINARY)

            
            # Debug: Eingabebild anzeigen
            cv2.imshow("OCR Input", schwellenwert)
            cv2.waitKey(1)

            # OCR ausführen
            nummer = pytesseract.image_to_string(
                schwellenwert,
                config='--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ).strip()

            print(f"OCR Debug-Ausgabe: {nummer}")

            if nummer:
                return nummer, frame

    return None, frame

    results = yolo_model.predict(frame, conf=0.5, verbose=False)
    nummer = ""
    for result in results:
        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
            if int(cls) != 0:  # Ersetze 0 mit der tatsächlichen Klasse für Nummernschilder
                continue
            x1, y1, x2, y2 = map(int, box[:4])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            nummernschild = frame[y1:y2, x1:x2]

            if nummernschild.size == 0:
                continue

            # Graustufen
            graustufen = cv2.cvtColor(nummernschild, cv2.COLOR_BGR2GRAY)

            # Kontrast verbessern mit CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            graustufen = clahe.apply(graustufen)

            # Glätten (optional, reduziert Rauschen)
            graustufen = cv2.GaussianBlur(graustufen, (5, 5), 0)

            # Binarisieren
            _, schwellenwert = cv2.threshold(graustufen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Debug: Bild zeigen
            cv2.imshow("OCR Input", schwellenwert)
            cv2.waitKey(1)

            # OCR
            nummer = pytesseract.image_to_string(
                schwellenwert,
                config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ).strip()

            if nummer:
                return nummer, frame

    return None, frame

    results = yolo_model.predict(frame, conf=0.5, verbose=False)
    nummer = ""
    for result in results:
        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
            if int(cls) != 0:  # Ersetze 0 mit der tatsächlichen Klasse für Nummernschilder
                continue
            x1, y1, x2, y2 = map(int, box[:4])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            nummernschild = frame[y1:y2, x1:x2]
            
            if nummernschild.size == 0:
                continue
            
            graustufen = cv2.cvtColor(nummernschild, cv2.COLOR_BGR2GRAY)
            graustufen = cv2.GaussianBlur(graustufen, (5, 5), 0)
            _, schwellenwert = cv2.threshold(graustufen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            cv2.imshow("OCR Input", schwellenwert)  # Debug-Bildanzeige
            cv2.waitKey(1)  # Bild aktualisieren
            
            nummer = pytesseract.image_to_string(schwellenwert, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()
            
            if nummer:
                return nummer, frame
    
    return None, frame

ocr_sperre_aktiv = False

def entsperre_ocr():
    global ocr_sperre_aktiv
    ocr_sperre_aktiv = False


def update_frame():
    global latest_frame, ocr_sperre_aktiv
    with frame_lock:
        if latest_frame is None:
            root.after(16, update_frame)
            return
        frame = latest_frame.copy()

    nummer = None
    if not ocr_sperre_aktiv:
        nummer, frame = erkenne_nummernschild(frame)

    if nummer:
        if nummer not in erlaubte_nummern and nummer not in illegale_nummern:
            illegale_nummern.add(nummer)
            speichere_nummern("illegal.csv", illegale_nummern)
        zugang = "Access Granted" if nummer in erlaubte_nummern else "Access Denied"

        if zugang == "Access Granted":
            mqtt_client.publish(mqtt_topic_granted, payload="yuppy")
        #OCR für 5 Sekunden deaktivieren
            ocr_sperre_aktiv = True
            threading.Timer(5.0, entsperre_ocr).start()

    else:
        zugang = "Access Denied"

    label_nummer.configure(text=f"Erkanntes Nummernschild: {nummer if nummer else 'Keins erkannt'}")
    label_status.configure(text=zugang, text_color="green" if zugang == "Access Granted" else "red")

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (640, 480))
    img = Image.fromarray(frame)
    img = ImageTk.PhotoImage(image=img)
    canvas.create_image(0, 0, anchor=ctk.NW, image=img)
    canvas.image = img

    root.after(16, update_frame)

def add_number():
    nummer = entry_nummer.get()
    if nummer and nummer not in erlaubte_nummern:
        erlaubte_nummern.add(nummer)
        speichere_nummern("erlaubt.csv", erlaubte_nummern)
        load_numbers()

def remove_number():
    nummer = entry_nummer.get()
    if nummer in erlaubte_nummern:
        erlaubte_nummern.remove(nummer)
        speichere_nummern("erlaubt.csv", erlaubte_nummern)
    elif nummer in illegale_nummern:
        illegale_nummern.remove(nummer)
        speichere_nummern("illegal.csv", illegale_nummern)
    load_numbers()

def load_numbers():
    listbox_erlaubt.configure(state="normal")
    listbox_erlaubt.delete("1.0", ctk.END)
    for num in erlaubte_nummern:
        listbox_erlaubt.insert(ctk.END, num + "\n")
    listbox_erlaubt.configure(state="disabled")
    
    listbox_illegal.configure(state="normal")
    listbox_illegal.delete("1.0", ctk.END)
    for num in illegale_nummern:
        listbox_illegal.insert(ctk.END, num + "\n")
    listbox_illegal.configure(state="disabled")

capture_thread = threading.Thread(target=capture_frames, daemon=True)
capture_thread.start()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Nummernschilderkennung Dashboard")
root.geometry("900x600")

frame_left = ctk.CTkFrame(root, width=300, height=600)
frame_left.pack(side=ctk.LEFT, fill=ctk.Y)

canvas = ctk.CTkCanvas(root, width=640, height=480)
canvas.pack()

label_nummer = ctk.CTkLabel(frame_left, text="Erkanntes Nummernschild:")
label_nummer.pack()

label_status = ctk.CTkLabel(frame_left, text="Status:", font=("Arial", 14))
label_status.pack()

entry_nummer = ctk.CTkEntry(frame_left, placeholder_text="Nummernschild eingeben")
entry_nummer.pack()

btn_add = ctk.CTkButton(frame_left, text="Hinzufügen", command=add_number)
btn_add.pack()

btn_remove = ctk.CTkButton(frame_left, text="Löschen", command=remove_number)
btn_remove.pack()

listbox_erlaubt = ctk.CTkTextbox(frame_left, height=100, width=250, state="disabled")
listbox_erlaubt.pack(pady=5)
listbox_illegal = ctk.CTkTextbox(frame_left, height=100, width=250, state="disabled")
listbox_illegal.pack(pady=5)

btn_exit = ctk.CTkButton(frame_left, text="Beenden", command=root.quit)
btn_exit.pack()

load_numbers()
update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
