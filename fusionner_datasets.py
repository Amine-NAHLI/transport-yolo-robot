import os
import shutil
import yaml

# ═══════════════════════════════════════
# CHEMINS DES DATASETS
# ═══════════════════════════════════════

DATASETS = [
    {
        "nom":    "Stop Sign",
        "images": r"C:\robot_project\Stop Sign.yolov8\train\images",
        "labels": r"C:\robot_project\Stop Sign.yolov8\train\labels",
        "classe": 0,  # stop = classe 0
        "yaml":   r"C:\robot_project\Stop Sign.yolov8\data.yaml"
    },
    {
        "nom":    "Vitesse 80",
        "images": r"C:\robot_project\vitesse_80_yolov8\train\images",
        "labels": r"C:\robot_project\vitesse_80_yolov8\train\labels",
        "classe": 1,  # vitesse = classe 1
        "yaml":   r"C:\robot_project\vitesse_80_yolov8\data.yaml"
    },
    {
        "nom":    "Feux rouge",
        "images": r"C:\robot_project\traffic signal detection.yolov8 (1)\train\images",
        "labels": r"C:\robot_project\traffic signal detection.yolov8 (1)\train\labels",
        "classe": 2,  # feux = classe 2
        "yaml":   r"C:\robot_project\traffic signal detection.yolov8 (1)\data.yaml"
    },
]

DEST_IMAGES = r"C:\robot_project\dataset_final\images\train"
DEST_LABELS = r"C:\robot_project\dataset_final\labels\train"

# ═══════════════════════════════════════
# FUSION
# ═══════════════════════════════════════

total = 0

for ds in DATASETS:
    print(f"\nTraitement : {ds['nom']}")

    # Vérifier que le dossier existe
    if not os.path.exists(ds['images']):
        print(f"  ERREUR : {ds['images']} non trouvé")
        continue

    # Lire les classes originales du dataset
    classes_originales = {}
    if os.path.exists(ds['yaml']):
        with open(ds['yaml'], 'r') as f:
            yaml_data = yaml.safe_load(f)
            noms = yaml_data.get('names', [])
            if isinstance(noms, dict):
                classes_originales = noms
            else:
                classes_originales = {i: n for i, n in enumerate(noms)}
        print(f"  Classes originales : {classes_originales}")

    # Copier images
    images = [f for f in os.listdir(ds['images'])
              if f.endswith(('.jpg', '.jpeg', '.png'))]

    print(f"  Images trouvées : {len(images)}")

    for img in images:
        # Nom unique
        nouveau_nom = f"{ds['nom'].replace(' ', '_')}_{img}"

        # Copier image
        src_img  = os.path.join(ds['images'], img)
        dest_img = os.path.join(DEST_IMAGES, nouveau_nom)
        shutil.copy2(src_img, dest_img)

        # Copier et corriger le label
        nom_label = os.path.splitext(img)[0] + ".txt"
        src_label = os.path.join(ds['labels'], nom_label)

        if os.path.exists(src_label):
            nouveau_label = os.path.splitext(nouveau_nom)[0] + ".txt"
            dest_label    = os.path.join(DEST_LABELS, nouveau_label)

            with open(src_label, 'r') as f:
                lignes = f.readlines()

            with open(dest_label, 'w') as f:
                for ligne in lignes:
                    parts = ligne.strip().split()
                    if parts:
                        # Remplacer la classe par notre numéro
                        parts[0] = str(ds['classe'])
                        f.write(' '.join(parts) + '\n')

            total += 1

    print(f"  ✓ {len(images)} images copiées")

print(f"\nTotal : {total} images fusionnées")

# ═══════════════════════════════════════
# CRÉER data.yaml FINAL
# ═══════════════════════════════════════

yaml_final = {
    'path':  r'C:\robot_project\dataset_final',
    'train': 'images/train',
    'val':   'images/train',
    'nc':    3,
    'names': ['stop', 'vitesse_80', 'feux_rouge']
}

with open(r'C:\robot_project\dataset_final\data.yaml', 'w') as f:
    yaml.dump(yaml_final, f, default_flow_style=False)

print("\n✓ data.yaml créé")
print("✓ Dataset fusionné prêt pour l'entraînement !")