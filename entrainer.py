from ultralytics import YOLO

if __name__ == '__main__':
    print("Démarrage entraînement GPU...")

    model = YOLO("yolov8n.pt")

    model.train(
        data    = r"C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_final\data.yaml",
        epochs  = 50,
        imgsz   = 640,
        batch   = 16,
        name    = "robot_panneaux",
        device  = 0,
        workers = 4,
    )

    print("Entraînement terminé !")
    print("Modèle : runs/detect/robot_panneaux/weights/best.pt")