# Transport YOLO Robot 🤖🚦

Ce projet est un système de vision par ordinateur conçu pour un robot transporteur. Il utilise **YOLOv8** pour la détection d'objets (personnes, panneaux de signalisation, feux tricolores) et la bibliothèque OpenCV pour la détection de **QR codes**. Le traitement lourd (IA et synthèse vocale) est effectué sur un PC qui communique en réseau avec un Raspberry Pi embarqué sur le robot.

---

## 📋 Table des matières
1. [Architecture du Système](#architecture-du-système)
2. [Structure du Projet](#structure-du-projet)
3. [Fonctionnement Principal (`pc_main.py`)](#fonctionnement-principal-pc_mainpy)
4. [Gestion des Datasets et Entraînement](#gestion-des-datasets-et-entraînement)
5. [Prérequis et Dépendances](#prérequis-et-dépendances)
6. [Guide d'Utilisation](#guide-dutilisation)

---

## 🏗 Architecture du Système

Le système est divisé en deux parties communiquant via requêtes HTTP :

- **Le Raspberry Pi (Serveur - `192.168.137.172:5000`)** : 
  - Gère la caméra et diffuse le flux vidéo (`/stream`).
  - Reçoit les commandes du PC (`/action`) pour contrôler les moteurs, afficher du texte sur un écran OLED, ou réagir aux panneaux.
- **Le PC (Client - Exécute `pc_main.py`)** :
  - Récupère le flux vidéo du Pi.
  - Exécute les modèles d'Intelligence Artificielle (YOLOv8) et traite l'image (QR Code).
  - Génère de la synthèse vocale (Text-To-Speech) pour lire les informations.
  - Envoie les instructions au robot.

---

## 📂 Structure du Projet

Voici le détail complet du contenu de ce dossier :

### 📁 Datasets d'origine (Format YOLOv8, issus de Roboflow)
- `Stop Sign.yolov8/` : Dataset pour les panneaux Stop.
- `vitesse_80_yolov8/` : Dataset pour les panneaux de limitation à 80 km/h.
- `traffic signal detection.yolov8 (1)/` : Dataset pour les feux rouges.
- `traffic signal detection.yolov8 (1) copy/` : Copie de sauvegarde du dataset des feux rouges.
- `Traffic light green.yolov8/` : Dataset pour les feux verts.
- `Yellow traffic light.yolov8/` : Dataset pour les feux oranges.
- `Simpson2.yolov8/` : Dataset pour la détection de Bart Simpson.
- `red traffic light.yolov8/` : Dataset spécifique aux feux rouges.
- `train/` : Dossier contenant les images et les labels d'entraînement bruts référencés dans `data.yaml`.
- `README.roboflow.txt` / `data.yaml` : Fichiers de configuration et métadonnées d'export Roboflow originaux.

### 🛠 Scripts de préparation des données
- `fusionner_datasets.py` : Script de première génération combinant les panneaux (Stop, Vitesse 80, Feux rouges) en un seul dataset unifié (`dataset_final/`).
- `fusionner_v2.py` : Version améliorée combinant 6 classes (Stop, Vitesse_80, Feux_Rouge, Feux_Vert, Feux_Orange, Bart_Simpson) vers le dossier `dataset_v2/`.

### 🗃 Datasets Fusionnés (Résultats)
- `dataset_final/` : Résultat de `fusionner_datasets.py` (3 classes).
- `dataset_v2/` : Résultat de `fusionner_v2.py` (6 classes).

### 🧠 Scripts d'Entraînement YOLO
- `entrainer.py` : Entraîne le modèle YOLOv8 sur `dataset_final/` pendant 50 epochs (nommé `robot_panneaux`).
- `entrainer_v2.py` : Entraîne le modèle sur `dataset_v2/` pendant 80 epochs (nommé `best_2`).
- `runs/` : Dossier généré automatiquement par Ultralytics contenant les résultats d'entraînement, les graphiques de performances et les poids (`best.pt`, `last.pt`) des modèles entraînés.
- `yolov8n.pt` / `yolo26n.pt` : Poids pré-entraînés de base (modèles Nano) utilisés pour le transfert d'apprentissage.

### 🚀 Application Principale
- **`pc_main.py`** : C'est le cœur du système. Ce script tourne sur le PC, lit le flux vidéo, analyse les images et contrôle le robot.

### 🔧 Fichiers Système et Git
- `README.md` : Ce fichier de documentation.
- `.git/` : Dossier contenant l'historique du contrôle de version Git.
- `.gitignore` : Fichier indiquant à Git quels fichiers ou dossiers ignorer (ex: les environnements virtuels ou les gros datasets).

---

## ⚙ Fonctionnement Principal (`pc_main.py`)

Le script principal repose sur une **Machine à 4 États** avec un système de threads pour gérer l'audio de manière asynchrone sans bloquer la vidéo :

1. **État 1 : CHERCHE PERSONNE (Couleur Verte)**
   - L'IA analyse l'image via YOLO.
   - Si un **Panneau Stop** (Classe 11) est détecté : Envoie l'action `stop` au Pi.
   - Si un **Panneau Vitesse** (Classe 13) est détecté : Envoie la vitesse lue au Pi.
   - Si une **Personne** (Classe 0) est détectée : Le robot s'arrête (ou se prépare) et passe à l'état 2 pour attendre une instruction via QR Code.

2. **État 2 : CHERCHE QR CODE (Couleur Violette)**
   - Utilise `cv2.QRCodeDetector()` pour scanner l'image.
   - Si un QR Code est détecté, son contenu est analysé.
   - Détecte des mots-clés spécifiques de destination (ex: **FES** ou **RABAT**) et informe le robot de la ville cible (`envoyer_action('ville', '...')`).
   - Le texte du QR code est découpé par groupes de mots et envoyé dans une file d'attente pour lecture. Le système passe à l'état 3.

3. **État 3 : LECTURE EN COURS (Couleur Orange/Rouge)**
   - Un Thread séparé lit le texte du QR code à haute voix en utilisant **gTTS** (Google Text-to-Speech) et `playsound`.
   - Le texte lu est envoyé simultanément à l'écran OLED du Raspberry Pi (`envoyer_action('oled', texte)`).
   - Une fois la lecture terminée, le système passe à l'état 4.

4. **État 4 : ATTENTE 5 SEC (Couleur Jaune)**
   - Pause de 5 secondes après avoir fini de parler.
   - Les fichiers audio MP3 temporaires (dans `C:\robot_project\audio`) sont supprimés pour libérer l'espace.
   - Le système repasse à l'État 1 (Recherche Personne).

---

## 🛠 Prérequis et Dépendances

L'environnement Python sur le PC nécessite l'installation des paquets suivants :

```bash
pip install opencv-python
pip install ultralytics
pip install requests
pip install gTTS
pip install playsound
pip install pyyaml
```
*(Optionnel mais recommandé : un environnement avec support CUDA pour exécuter YOLOv8 sur la carte graphique afin d'obtenir un flux vidéo fluide).*

---

## 🚀 Guide d'Utilisation

### 1. Préparation (Si besoin de ré-entraîner le modèle)
1. Exécutez `python fusionner_v2.py` pour compiler tous les sous-datasets.
2. Exécutez `python entrainer_v2.py` pour lancer l'entraînement.
3. Remplacez le nom du modèle (`yolov8n.pt`) à la ligne 29 de `pc_main.py` par le chemin de votre nouveau modèle entraîné (ex: `runs/detect/best_2/weights/best.pt`).

### 2. Lancement du Système
1. **Sur le Raspberry Pi** : Lancez le serveur Flask/Python qui gère le robot et expose les endpoints `/stream` et `/action` (sur IP `192.168.137.172`).
2. **Sur le PC** : 
   - Vérifiez que vous êtes connecté au même réseau (ex: Hotspot du Pi).
   - Exécutez la commande : `python pc_main.py`
3. L'interface caméra OpenCV s'ouvrira avec l'affichage de l'état actuel et des détections (Bounding boxes).
4. **Pour quitter** : Appuyez sur la touche `Q` dans la fenêtre vidéo.
