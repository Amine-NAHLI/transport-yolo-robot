from ultralytics import YOLO

if __name__ == '__main__':
    print("Entrainement v2...")

    model = YOLO("yolov8n.pt")

    model.train(
        data    = r"C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_v2\data.yaml",
        epochs  = 80,
        imgsz   = 640,
        batch   = 16,
        name    = "best_2",
        device  = 0,
        workers = 4,
    )

    print("Termine !")
    print("Modele : runs/detect/best_2/weights/best.pt")