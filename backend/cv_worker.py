from typing import List, Dict, Optional

def detect_spots_mock() -> List[Dict]:
    return [
        {"spot_id": "A1", "occupied": True,  "confidence": 0.97},
        {"spot_id": "A2", "occupied": False, "confidence": 0.93},
        {"spot_id": "A3", "occupied": True,  "confidence": 0.88},
        {"spot_id": "B1", "occupied": False, "confidence": 0.90},
        {"spot_id": "B2", "occupied": False, "confidence": 0.86},
        {"spot_id": "B3", "occupied": True,  "confidence": 0.91},
    ]

async def detect_spots_gemini(img_bytes: Optional[bytes]) -> List[Dict]:
    return detect_spots_mock()
