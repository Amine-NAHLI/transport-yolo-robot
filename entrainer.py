from ultralytics import YOLO

print("Démarrage entraînement...")

model = YOLO("yolov8n.pt")

model.train(
    data    = r"C:\robot_project\dataset_final\data.yaml",
    epochs  = 50,
    imgsz   = 640,
    batch   = 8,
    name    = "robot_panneaux",
    patience= 10,
)

print("Entraînement terminé !")
print("Modèle sauvegardé dans : runs/detect/robot_panneaux/weights/best.pt")