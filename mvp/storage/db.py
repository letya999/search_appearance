import json
import os
from typing import List, Optional, Dict
from ..schema.models import PhotoProfile

class PhotoDatabase:
    def __init__(self, db_path: str = "data/db.json"):
        self.db_path = db_path
        self._ensure_db()
        self.profiles: Dict[str, PhotoProfile] = {}
        self.load()

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({}, f)

    def load(self):
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self.profiles = {}
                
                if isinstance(data, list):
                    for item in data:
                        # Ensure ID
                        if 'id' not in item:
                            # If no ID, skip or gen? Ideally skip if critical.
                            continue
                        self.profiles[item['id']] = PhotoProfile(**item)
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if 'id' not in value:
                            value['id'] = key
                        self.profiles[key] = PhotoProfile(**value)
        except json.JSONDecodeError:
            self.profiles = {}
        except Exception as e:
            print(f"Error loading DB: {e}")
            self.profiles = {}

    def save(self):
        data = {k: v.model_dump(mode='json') for k, v in self.profiles.items()}
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_profile(self, profile: PhotoProfile):
        self.profiles[profile.id] = profile
        self.save()

    def get_profile(self, profile_id: str) -> Optional[PhotoProfile]:
        return self.profiles.get(profile_id)

    def get_all_profiles(self) -> List[PhotoProfile]:
        return list(self.profiles.values())
