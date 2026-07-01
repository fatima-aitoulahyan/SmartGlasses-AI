import os
import numpy as np
from ultralytics import YOLO

MODEL_PATH        = os.getenv("OBSTACLE_MODEL_PATH", "/app/models/yolo_trained.pt")
INDOOR_MODEL_PATH = "/app/models/indoor_model.pt"
THRESHOLD         = float(os.getenv("CONFIDENCE_THRESHOLD", "0.3"))

CUSTOM_LABELS = {
    "Bicycle":          {"fr": "vélo", "en": "bicycle", "ar": "دراجة"},
    "Bus":              {"fr": "bus", "en": "bus", "ar": "حافلة"},
    "Car":              {"fr": "voiture", "en": "car", "ar": "سيارة"},
    "Dog":              {"fr": "chien", "en": "dog", "ar": "كلب"},
    "Electric pole":    {"fr": "poteau électrique", "en": "electric pole", "ar": "عمود كهربائي"},
    "Motorcycle":       {"fr": "moto", "en": "motorcycle", "ar": "دراجة nارية"},
    "Person":           {"fr": "personne", "en": "person", "ar": "شخص"},
    "Traffic signs":    {"fr": "panneau de signalisation", "en": "traffic sign", "ar": "علامة تشوير"},
    "Tree":             {"fr": "arbre", "en": "tree", "ar": "شجرة"},
    "Uncovered manhole":{"fr": "trou de regard", "en": "uncovered manhole", "ar": "بالوعة مفتوحة"},
}

INDOOR_LABELS = {
    "door":             {"fr": "porte", "en": "door", "ar": "باب"},
    "cabinetDoor":      {"fr": "porte de placard", "en": "cabinet door", "ar": "باب خزانة"},
    "refrigeratorDoor": {"fr": "porte de réfrigérateur", "en": "fridge door", "ar": "باب الثلاجة"},
    "window":           {"fr": "fenêtre", "en": "window", "ar": "نافذة"},
    "chair":            {"fr": "chaise", "en": "chair", "ar": "كرسي"},
    "table":            {"fr": "table", "en": "table", "ar": "طاولة"},
    "cabinet":          {"fr": "placard", "en": "cabinet", "ar": "خزانة"},
    "couch":            {"fr": "canapé", "en": "couch", "ar": "أريكة"},
    "openedDoor":       {"fr": "porte ouverte", "en": "open door", "ar": "باب مفتوح"},
    "pole":             {"fr": "poteau", "en": "pole", "ar": "عمود"},
}

COCO_LABELS = {
    0:  {"fr": "personne", "en": "person", "ar": "شخص"},
    1:  {"fr": "vélo", "en": "bicycle", "ar": "دراجة"},
    2:  {"fr": "voiture", "en": "car", "ar": "سيارة"},
    3:  {"fr": "moto", "en": "motorcycle", "ar": "دراجة نارية"},
    5:  {"fr": "bus", "en": "bus", "ar": "حافلة"},
    7:  {"fr": "camion", "en": "truck", "ar": "شاحنة"},
    9:  {"fr": "feu de circulation", "en": "traffic light", "ar": "إشارة مرور"},
    11: {"fr": "panneau stop", "en": "stop sign", "ar": "علامة قف"},
    13: {"fr": "banc", "en": "bench", "ar": "مقعد"},
    15: {"fr": "chat", "en": "cat", "ar": "قط"},
    16: {"fr": "chien", "en": "dog", "ar": "كلب"},
    24: {"fr": "sac à dos", "en": "backpack", "ar": "حقيبة ظهر"},
    25: {"fr": "parapluie", "en": "umbrella", "ar": "مظلة"},
    28: {"fr": "valise", "en": "suitcase", "ar": "حقيبة سفر"},
    56: {"fr": "chaise", "en": "chair", "ar": "كرسي"},
    57: {"fr": "canapé", "en": "couch", "ar": "أريكة"},
    58: {"fr": "plante", "en": "potted plant", "ar": "نبتة"},
    59: {"fr": "lit", "en": "bed", "ar": "سرير"},
    60: {"fr": "table", "en": "table", "ar": "طاولة"},
    67: {"fr": "téléphone", "en": "phone", "ar": "هاتف"},
}

ALERT_TEMPLATES = {
    "fr": {"alert": "Attention ! {} devant vous.", "clear": "Voie libre."},
    "en": {"alert": "Warning ! {} in front of you.", "clear": "Clear path."},
    "ar": {"alert": "انتبه ! {} أمامك.", "clear": "الطريق سالكة."}
}

def get_distance_multilang(bbox_height: float, image_height: float) -> dict:
    ratio = bbox_height / image_height
    if ratio > 0.6:
        return {"fr": "très proche, moins de 0.5 mètre", "en": "very close, less than 0.5 meters", "ar": "قريب جدا، أقل من نصف متر"}
    elif ratio > 0.35:
        return {"fr": "proche, environ 1 mètre", "en": "close, around 1 meter", "ar": "قريب، حوالي متر واحد"}
    elif ratio > 0.15:
        return {"fr": "à environ 2 mètres", "en": "about 2 meters away", "ar": "على بعد حوالي مترين"}
    else:
        return {"fr": "loin, plus de 3 mètres", "en": "far, more than 3 meters", "ar": "بعيد، أكثر من 3 أمتار"}

def get_position_multilang(x_center: float) -> dict:
    if x_center < 0.33:
        return {"fr": "à gauche", "en": "on the left", "ar": "على اليسار"}
    elif x_center > 0.66:
        return {"fr": "à droite", "en": "on the right", "ar": "على اليمين"}
    return {"fr": "devant vous", "en": "in front of you", "ar": "أمامك"}


class ObstacleDetector:
    def __init__(self):
        path = MODEL_PATH if os.path.exists(MODEL_PATH) else "yolov8n.pt"
        self.model_custom = YOLO(path)
        self.model_indoor = YOLO(INDOOR_MODEL_PATH) if os.path.exists(INDOOR_MODEL_PATH) else None
        self.model_coco = YOLO("yolov8n.pt")
        self.threshold = THRESHOLD

    def _process_boxes(self, boxes, names, labels_dict, h):
        detections = []
        for box in boxes:
            label_en = names[int(box.cls)] if isinstance(labels_dict, dict) and not isinstance(list(labels_dict.keys())[0], int) else int(box.cls[0])
            if label_en not in labels_dict:
                continue

            x_center = float(box.xywhn[0][0])
            bbox_h   = float(box.xywh[0][3])

            detections.append({
                "label":      labels_dict[label_en],
                "confidence": round(float(box.conf[0]), 2),
                "position":   get_position_multilang(x_center),
                "distance":   get_distance_multilang(bbox_h, h)
            })
        return detections

    def detect(self, image: np.ndarray) -> dict:
        h, w = image.shape[:2]
        res_custom = self.model_custom(image, conf=self.threshold)[0]
        det_custom = self._process_boxes(res_custom.boxes, res_custom.names, CUSTOM_LABELS, h)

        det_indoor = []
        if self.model_indoor:
            res_indoor = self.model_indoor(image, conf=self.threshold)[0]
            det_indoor = self._process_boxes(res_indoor.boxes, res_indoor.names, INDOOR_LABELS, h)

        res_coco = self.model_coco(image, conf=self.threshold)[0]
        det_coco = self._process_boxes(res_coco.boxes, res_coco.names, COCO_LABELS, h)
        seen = set()
        all_detections = []
        for d in det_custom + det_indoor + det_coco:
            key = (d["label"]["fr"], d["position"]["fr"])
            if key not in seen:
                seen.add(key)
                all_detections.append(d)
        vocal_messages = {}
        for lang in ["fr", "en", "ar"]:
            lang_items = []
            for d in all_detections:
                if lang == "ar":
                    lang_items.append(f"{d['label'][lang]} {d['position'][lang]} {d['distance'][lang]}")
                else:
                    lang_items.append(f"{d['label'][lang]} {d['distance'][lang]} {d['position'][lang]}")

            templates = ALERT_TEMPLATES[lang]
            if lang_items:
                sep = " و " if lang == "ar" else ", "
                vocal_messages[lang] = templates["alert"].format(sep.join(lang_items))
            else:
                vocal_messages[lang] = templates["clear"]

        return {
            "success": True,
            "mode": "obstacle",
            "result": {
                "detections": all_detections,
                "vocal_message": vocal_messages,
                "alert_message": vocal_messages
            }
        }

detector = ObstacleDetector()