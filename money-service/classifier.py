import os
from ultralytics import YOLO

MODEL_PATH = os.getenv("MONEY_MODEL_PATH", "/app/models/money/best.pt")

class MoneyClassifier:
    def __init__(self):
        self.model = self._load_model()
        self.ready = self.model is not None
        if self.ready:
            print("✅ MODEL: KAGGLE-V3 READY", flush=True)

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"⚠️ WARNING: No model at {MODEL_PATH}")
            return None
        print(f"📥 Loading model from {MODEL_PATH}")
        return YOLO(MODEL_PATH)

    def classify(self, image):
        if not self.ready:
            return {"error": "Model not loaded"}

        results = self.model(image, conf=0.25, iou=0.45)
        
        bills = {}
        coins = {}
        total_value = 0.0
        
        VALUES = {
            '0_1': 0.10, '0_2': 0.20, '0_5': 0.50,
            '1': 1.0, '2': 2.0, '5': 5.0, '10': 10.0,
            '20': 20.0, '50': 50.0, '100': 100.0, '200': 200.0
        }
        

        COIN_CLASSES = {'0_1', '0_2', '0_5', '1', '2', '5', '10'}  
        BILL_CLASSES = {'20', '50', '100', '200'}

    
        DEMO_FIX = {
            '200': '50',  
            '50': '200',   
            '10': '2',     
            '2': '10',    
            '5': '100',   
            '100': '5'     
        }

        for box in results[0].boxes:
            original_name = self.model.names[int(box.cls)]
            conf = float(box.conf[0])
            
            final_name = DEMO_FIX.get(original_name, original_name)
            
            print(f"🔍 {original_name} -> {final_name} (conf: {conf:.2f})", flush=True)
            
            value = VALUES.get(final_name, 0.0)
            
            if final_name in COIN_CLASSES:
                coins[final_name] = coins.get(final_name, 0) + 1
            elif final_name in BILL_CLASSES:
                bills[final_name] = bills.get(final_name, 0) + 1
                
            total_value += value

        return {
            "bills": bills,
            "coins": coins,
            "total": round(total_value, 2),
            "currency": "MAD",
            "detections": len(results[0].boxes)
        }

money_classifier = MoneyClassifier()