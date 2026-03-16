import json
import logging
from pathlib import Path
from sqlmodel import Session, select

from app.db.database import engine
from app.models.tarot import TarotCard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "app" / "data"
DECK_PATH = DATA_DIR / "tarot_deck.json"

def seed_tarot_deck():
    """
    Load the tarot deck from JSON and insert/update in the database.
    """
    if not DECK_PATH.exists():
        logger.error(f"Deck file not found at {DECK_PATH}")
        return

    with DECK_PATH.open(encoding="utf-8") as f:
        deck_data = json.load(f)

    with Session(engine) as session:
        for item in deck_data:
            # Check if card exists
            existing = session.get(TarotCard, item["id"])
            
            # Construct image path (assuming a convention like assets/images/cards/0.webp)
            image_path = f"assets/images/cards/{item['id']}.webp"
            
            card_data = {
                "id": item["id"],
                "name": item["name"],
                "name_es": item["name_es"],
                "arcana": item["arcana"],
                "suit": item["suit"],
                "meaning_upright_en": item["meaning_upright_en"],
                "meaning_upright_es": item["meaning_upright_es"],
                "meaning_reversed_en": item["meaning_reversed_en"],
                "meaning_reversed_es": item["meaning_reversed_es"],
                "keywords_en": item["keywords_en"],
                "keywords_es": item["keywords_es"],
                "image_path": image_path,
            }
            
            if existing:
                # Update existing
                for key, value in card_data.items():
                    setattr(existing, key, value)
                logger.info(f"Updated card: {item['name']}")
            else:
                # Create new
                new_card = TarotCard(**card_data)
                session.add(new_card)
                logger.info(f"Created card: {item['name']}")
        
        session.commit()
        logger.info("Tarot deck seeding complete.")

if __name__ == "__main__":
    seed_tarot_deck()
