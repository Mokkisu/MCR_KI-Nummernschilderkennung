import cv2
import pandas as pd
import numpy as np
import time
from datetime import datetime
import tkinter as tk
from tkinter import Label, Button, Canvas
from PIL import Image, ImageTk
from ultralytics import YOLO
import pytesseract

# YOLO-Model für Nummernschilder laden (angepasstes Modell erforderlich)
yolo_model = YOLO("best.pt")  # Ersetze "best.pt" mit deinem trainierten Modell

# Initialisierung der erlaubten Nummernschilder
erlaubte_nummern = set()

def lade_erlaubte_nummern(csv_datei):
    try:
        df = pd.read_csv(csv_datei, header=None)
        return set(df[0].astype(str))
    except FileNotFoundError:
        return set()

erlaubte_nummern = lade_erlaubte_nummern("nummernschilder.csv")

# Webcam-Stream starten
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)

def erkenne_nummernschild(frame):
    results = yolo_model(frame)
    for result in results:
        for box in result.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box[:4])
            nummernschild = frame[y1:y2, x1:x2]
            
            if nummernschild.size == 0:
                continue
            
            graustufen = cv2.cvtColor(nummernschild, cv2.COLOR_BGR2GRAY)
            nummer = pytesseract.image_to_string(graustufen, config='--psm 8')
            return nummer.strip()
    return ""

def update_frame():
    ret, frame = cap.read()
    if not ret:
        return
    
    nummer = erkenne_nummernschild(frame)
    zugang = "Access Granted" if nummer in erlaubte_nummern else "Access Denied"
    
    label_nummer.config(text=f"Erkanntes Nummernschild: {nummer}")
    label_status.config(text=zugang, fg="green" if zugang == "Access Granted" else "red")
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (640, 480))
    img = Image.fromarray(frame)
    img = ImageTk.PhotoImage(image=img)
    canvas.create_image(0, 0, anchor=tk.NW, image=img)
    canvas.image = img
    
    root.after(16, update_frame)  # 60 FPS Refresh-Rate

# GUI mit Tkinter
root = tk.Tk()
root.title("Nummernschilderkennung")

canvas = Canvas(root, width=640, height=480)
canvas.pack()

label_nummer = Label(root, text="Erkanntes Nummernschild: ")
label_nummer.pack()

label_status = Label(root, text="Status: ", font=("Arial", 14))
label_status.pack()

btn_exit = Button(root, text="Beenden", command=root.quit)
btn_exit.pack()

update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
