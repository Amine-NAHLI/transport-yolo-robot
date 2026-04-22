import os
import shutil
import yaml

DATASETS = [
    {
        "nom":    "Stop",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Stop Sign.yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Stop Sign.yolov8\train\labels",
        "classe": 0,
    },
    {
        "nom":    "Vitesse_80",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\vitesse_80_yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\vitesse_80_yolov8\train\labels",
        "classe": 1,
    },
    {
        "nom":    "Feux_Rouge",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\red traffic light.yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\red traffic light.yolov8\train\labels",
        "classe": 2,
    },
    {
        "nom":    "Feux_Vert",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Traffic light green.yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Traffic light green.yolov8\train\labels",
        "classe": 3,
    },
    {
        "nom":    "Feux_Orange",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Yellow traffic light.yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Yellow traffic light.yolov8\train\labels",
        "classe": 4,
    },
    {
        "nom":    "Bart_Simpson",
        "images": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Simpson2.yolov8\train\images",
        "labels": r"C:\1er CI\ROBOTIC\transport-yolo-robot\Simpson2.yolov8\train\labels",
        "classe": 5,
    },
]

DEST_IMAGES = r"C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_v2\images\train"
DEST_LABELS = r"C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_v2\labels\train"

os.makedirs(DEST_IMAGES, exist_ok=True)
os.makedirs(DEST_LABELS, exist_ok=True)

total = 0

for ds in DATASETS:
    print(f"\nTraitement : {ds['nom']}")

    if not os.path.exists(ds['images']):
        print(f"  ERREUR : {ds['images']} non trouve")
        continue

    images = [f for f in os.listdir(ds['images'])
              if f.endswith(('.jpg', '.jpeg', '.png'))]

    print(f"  Images trouvees : {len(images)}")

    for img in images:
        nouveau_nom = f"{ds['nom']}_{img}"

        shutil.copy2(
            os.path.join(ds['images'], img),
            os.path.join(DEST_IMAGES, nouveau_nom)
        )

        nom_label = os.path.splitext(img)[0] + ".txt"
        src_label = os.path.join(ds['labels'], nom_label)

        if os.path.exists(src_label):
            dest_label = os.path.join(
                DEST_LABELS,
                os.path.splitext(nouveau_nom)[0] + ".txt"
            )

            with open(src_label, 'r') as f:
                lignes = f.readlines()

            with open(dest_label, 'w') as f:
                for ligne in lignes:
                    parts = ligne.strip().split()
                    if parts:
                        parts[0] = str(ds['classe'])
                        f.write(' '.join(parts) + '\n')

            total += 1

    print(f"  OK : {len(images)} images copiees")

yaml_final = {
    'path':  r'C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_v2',
    'train': 'images/train',
    'val':   'images/train',
    'nc':    6,
    'names': [
        'stop',
        'vitesse_80',
        'feux_rouge',
        'feux_vert',
        'feux_orange',
        'bart_simpson'
    ]
}

with open(r'C:\1er CI\ROBOTIC\transport-yolo-robot\dataset_v2\data.yaml', 'w') as f:
    yaml.dump(yaml_final, f, default_flow_style=False)

print(f"\nTotal : {total} images fusionnees")
print("dataset_v2 pret !")