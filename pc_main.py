import cv2
import requests
import time
import threading
import queue
import numpy as np
import os
from ultralytics import YOLO
from gtts import gTTS
from playsound import playsound

# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════

PI_IP      = "192.168.137.172"
PI_PORT    = 5000
STREAM_URL = f"http://{PI_IP}:{PI_PORT}/stream"
ACTION_URL = f"http://{PI_IP}:{PI_PORT}/action"
AUDIO_DIR  = "C:\\robot_project\\audio"

os.makedirs(AUDIO_DIR, exist_ok=True)

# ═══════════════════════════════════════
# INITIALISATION
# ═══════════════════════════════════════

print("Chargement YOLO...")
model       = YOLO("yolov8n.pt")
qr_detector = cv2.QRCodeDetector()
print("YOLO prêt !")

file_lecture   = queue.Queue()
compteur_audio = 0
fichiers_audio = []
lock_audio     = threading.Lock()

# ═══════════════════════════════════════
# ÉTATS GLOBAUX
# ═══════════════════════════════════════

ETAT_CHERCHE_PERSONNE = 1
ETAT_CHERCHE_QR       = 2
ETAT_LECTURE          = 3
ETAT_ATTENTE          = 4

etat_actuel  = ETAT_CHERCHE_PERSONNE
message_etat = "En attente d'une personne..."
compteur     = 0
last_qr      = ""
etat_lock    = threading.Lock()

# ═══════════════════════════════════════
# FONCTIONS AUDIO
# ═══════════════════════════════════════

def parler_partie(texte, index):
    try:
        fichier = os.path.join(AUDIO_DIR, f"part_{index}.mp3")

        with lock_audio:
            fichiers_audio.append(fichier)

        # Générer MP3
        tts = gTTS(text=texte, lang='fr')
        tts.save(fichier)

        # Jouer — bloque jusqu'à la fin
        playsound(fichier)

    except Exception as e:
        print(f"Erreur audio : {e}")

def supprimer_fichiers_audio():
    def _supprimer():
        time.sleep(2)
        with lock_audio:
            for f in fichiers_audio[:]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                        print(f"Supprimé : {f}")
                except Exception as e:
                    print(f"Erreur suppression : {e}")
            fichiers_audio.clear()
    threading.Thread(target=_supprimer, daemon=True).start()

# ═══════════════════════════════════════
# THREAD LECTEUR
# ═══════════════════════════════════════

def lecteur_vocal():
    global compteur_audio, etat_actuel, message_etat

    while True:
        try:
            partie = file_lecture.get(timeout=1)

            if partie == "FIN":
                print("Lecture terminée → Attente 5 secondes")
                envoyer_action('oled', "")
                supprimer_fichiers_audio()

                with etat_lock:
                    etat_actuel  = ETAT_ATTENTE
                    message_etat = "Attente 5 secondes..."

                time.sleep(5)

                with etat_lock:
                    etat_actuel  = ETAT_CHERCHE_PERSONNE
                    message_etat = "En attente d'une personne..."

                print("→ Retour recherche personne")
                file_lecture.task_done()
                continue

            print(f"Parle : [{partie}]")

            with etat_lock:
                etat_actuel  = ETAT_LECTURE
                message_etat = f"{partie}"

            # Afficher sur OLED
            envoyer_action('oled', partie)
            time.sleep(0.2)

            # Lire à voix haute
            parler_partie(partie, compteur_audio)
            compteur_audio += 1

            time.sleep(0.2)
            file_lecture.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Erreur lecteur : {e}")

thread_lecteur = threading.Thread(target=lecteur_vocal, daemon=True)
thread_lecteur.start()

# ═══════════════════════════════════════
# FONCTIONS
# ═══════════════════════════════════════

def envoyer_action(type_action, contenu=""):
    try:
        requests.post(
            ACTION_URL,
            json={'type': type_action, 'contenu': contenu},
            timeout=2
        )
    except Exception as e:
        print(f"Erreur envoi : {e}")

def decouper_par_mots(texte, max_chars=20):
    mots    = texte.split()
    parties = []
    partie  = ""

    for mot in mots:
        if partie == "":
            partie = mot
        elif len(partie) + 1 + len(mot) <= max_chars:
            partie += " " + mot
        else:
            parties.append(partie)
            partie = mot

    if partie:
        parties.append(partie)

    return parties

def lire_et_afficher(texte):
    parties = decouper_par_mots(texte, max_chars=20)
    print(f"Texte divisé en {len(parties)} parties :")
    for i, partie in enumerate(parties):
        print(f"  {i+1}/{len(parties)} : [{partie}]")
        file_lecture.put(partie)
    file_lecture.put("FIN")

def gerer_qr(contenu):
    print(f"QR détecté : {contenu}")

    with etat_lock:
        global etat_actuel, message_etat
        etat_actuel  = ETAT_LECTURE
        message_etat = "Lecture en cours..."

    threading.Thread(
        target=lire_et_afficher,
        args=(contenu,),
        daemon=True
    ).start()

    contenu_upper = contenu.upper()
    if "FES" in contenu_upper or "FÈS" in contenu_upper:
        print("→ FES détecté")
        envoyer_action('ville', 'FES')
    elif "RABAT" in contenu_upper:
        print("→ RABAT détecté")
        envoyer_action('ville', 'RABAT')

def dessiner_detection(frame, box, nom, confiance, couleur):
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    cv2.rectangle(frame, (x1, y1), (x2, y2), couleur, 2)
    cv2.putText(
        frame,
        f"{nom} {confiance:.0%}",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6, couleur, 2
    )

def afficher_panneau(frame, lignes, couleur_fond):
    overlay = frame.copy()
    h, w    = frame.shape[:2]
    cv2.rectangle(overlay, (0, h-120), (w, h), couleur_fond, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    y = h - 100
    for ligne in lignes:
        cv2.putText(
            frame, ligne,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (255, 255, 255), 2
        )
        y += 30

# ═══════════════════════════════════════
# BOUCLE PRINCIPALE
# ═══════════════════════════════════════

print(f"Connexion au stream Pi...")
stream = cv2.VideoCapture(STREAM_URL)

if not stream.isOpened():
    print("ERREUR : impossible de se connecter au Pi")
    exit()

print("Stream connecté !")
print("Appuie sur Q pour quitter")

try:
    while True:
        ret, frame = stream.read()

        if not ret:
            print("Reconnexion...")
            time.sleep(1)
            stream = cv2.VideoCapture(STREAM_URL)
            continue

        compteur += 1
        h, w = frame.shape[:2]

        with etat_lock:
            etat_courant = etat_actuel
            msg_courant  = message_etat

        # ═══════════════════════════════
        # ÉTAT 1 — CHERCHE PERSONNE
        # ═══════════════════════════════
        if etat_courant == ETAT_CHERCHE_PERSONNE:

            if compteur % 2 == 0:
                resultats = model(
                    frame,
                    imgsz=320,
                    conf=0.5,
                    verbose=False
                )

                for r in resultats:
                    for box in r.boxes:
                        classe_id = int(box.cls[0])
                        confiance = float(box.conf[0])
                        nom       = r.names[classe_id]

                        if classe_id == 0:
                            dessiner_detection(
                                frame, box,
                                "Personne", confiance,
                                (0, 255, 0)
                            )
                            with etat_lock:
                                etat_actuel  = ETAT_CHERCHE_QR
                                message_etat = "Personne detectee!"
                            print("✓ Personne → Attente QR")

                        elif classe_id == 11:
                            dessiner_detection(
                                frame, box,
                                "STOP", confiance,
                                (0, 0, 255)
                            )
                            envoyer_action('stop')
                            print("⛔ STOP")

                        elif classe_id == 13:
                            vitesse = f"{int(confiance*100)} km/h"
                            dessiner_detection(
                                frame, box,
                                f"Vitesse:{vitesse}", confiance,
                                (255, 165, 0)
                            )
                            envoyer_action('vitesse', vitesse)
                            print(f"Vitesse : {vitesse}")

            afficher_panneau(
                frame,
                [
                    "● Recherche personne",
                    msg_courant,
                    "Montre une personne"
                ],
                (50, 50, 50)
            )

        # ═══════════════════════════════
        # ÉTAT 2 — CHERCHE QR CODE
        # ═══════════════════════════════
        elif etat_courant == ETAT_CHERCHE_QR:

            try:
                contenu, points, _ = qr_detector.detectAndDecode(frame)
            except:
                contenu = ""
                points  = None

            if contenu:
                if points is not None:
                    try:
                        pts = points[0].astype(int)
                        for i in range(4):
                            cv2.line(
                                frame,
                                tuple(pts[i]),
                                tuple(pts[(i+1) % 4]),
                                (255, 0, 255), 3
                            )
                    except:
                        pass

                last_qr = contenu
                gerer_qr(contenu)
                print(f"✓ QR : {contenu}")

            afficher_panneau(
                frame,
                [
                    "● Attente QR code",
                    "Montre un QR code",
                    f"Dernier: {last_qr[:25]}" if last_qr else "Aucun QR encore"
                ],
                (0, 80, 0)
            )

        # ═══════════════════════════════
        # ÉTAT 3 — LECTURE EN COURS
        # ═══════════════════════════════
        elif etat_courant == ETAT_LECTURE:

            afficher_panneau(
                frame,
                [
                    "● Lecture en cours...",
                    msg_courant[:30],
                    "Attendre la fin"
                ],
                (0, 0, 100)
            )

        # ═══════════════════════════════
        # ÉTAT 4 — ATTENTE 5 SECONDES
        # ═══════════════════════════════
        elif etat_courant == ETAT_ATTENTE:

            afficher_panneau(
                frame,
                [
                    "● Attente 5 secondes",
                    "Reprise dans un instant...",
                    ""
                ],
                (100, 50, 0)
            )

        # ═══════════════════════════════
        # BARRE EN HAUT
        # ═══════════════════════════════

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 45), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        couleurs = {
            ETAT_CHERCHE_PERSONNE: (0, 255, 0),
            ETAT_CHERCHE_QR:       (255, 0, 255),
            ETAT_LECTURE:          (0, 100, 255),
            ETAT_ATTENTE:          (0, 165, 255),
        }

        textes = {
            ETAT_CHERCHE_PERSONNE: "CHERCHE PERSONNE",
            ETAT_CHERCHE_QR:       "CHERCHE QR CODE",
            ETAT_LECTURE:          "LECTURE EN COURS",
            ETAT_ATTENTE:          "ATTENTE 5 SEC",
        }

        couleur_etat = couleurs.get(etat_courant, (255, 255, 255))
        texte_etat   = textes.get(etat_courant, "")

        cv2.putText(
            frame,
            f"● {texte_etat}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, couleur_etat, 2
        )

        cv2.putText(
            frame,
            f"Pi:{PI_IP}",
            (w - 170, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, (200, 200, 200), 1
        )

        cv2.imshow("Robot Vision — Stream Live", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Arrêt")
finally:
    stream.release()
    cv2.destroyAllWindows()
    supprimer_fichiers_audio()
    print("Programme arrêté")