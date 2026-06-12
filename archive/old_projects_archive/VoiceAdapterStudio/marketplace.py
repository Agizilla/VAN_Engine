"""
VoiceAdapter Studio - Marketplace Module
Mock marketplace for browsing, searching, and "purchasing" adapters.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class MarketplaceAdapter:
    """Represents an adapter in the marketplace."""
    
    def __init__(
        self,
        name: str,
        author: str,
        description: str,
        category: str,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        price: float = 9.99,
        rating: float = 4.5,
        downloads: int = 0,
        preview_url: Optional[str] = None,
        license_type: str = "personal"
    ):
        self.id = name.lower().replace(" ", "_")
        self.name = name
        self.author = author
        self.description = description
        self.category = category
        self.genre = genre
        self.mood = mood
        self.price = price
        self.rating = rating
        self.downloads = downloads
        self.preview_url = preview_url or f"preview_{self.id}.mp3"
        self.license_type = license_type
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "genre": self.genre,
            "mood": self.mood,
            "price": self.price,
            "rating": self.rating,
            "downloads": self.downloads,
            "preview_url": self.preview_url,
            "license_type": self.license_type,
            "created_at": self.created_at
        }


class Marketplace:
    """Manages the marketplace catalog and operations."""
    
    def __init__(self):
        self.marketplace_dir = Path("marketplace_data")
        self.marketplace_dir.mkdir(exist_ok=True)
        self.catalog_file = self.marketplace_dir / "catalog.json"
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> List[MarketplaceAdapter]:
        """Load catalog from disk or create default."""
        if self.catalog_file.exists():
            with open(self.catalog_file, 'r') as f:
                data = json.load(f)
                return [MarketplaceAdapter(**item) for item in data]
        else:
            # Create default catalog
            catalog = self._create_default_catalog()
            self._save_catalog(catalog)
            return catalog
    
    def _save_catalog(self, catalog: List[MarketplaceAdapter]):
        """Save catalog to disk."""
        with open(self.catalog_file, 'w') as f:
            json.dump([adapter.to_dict() for adapter in catalog], f, indent=2)
    
    def _create_default_catalog(self) -> List[MarketplaceAdapter]:
        """Create default marketplace catalog with example adapters."""
        adapters = [
            # Genre: Pop
            MarketplaceAdapter(
                name="Pop Star Shine",
                author="AI Studio",
                description="Bright, polished pop vocals with modern production quality. Perfect for upbeat tracks.",
                category="Genre",
                genre="Pop",
                price=12.99,
                rating=4.8,
                downloads=1532
            ),
            MarketplaceAdapter(
                name="Indie Pop Dreamer",
                author="VocalLabs",
                description="Soft, intimate indie-pop style with airy texture and emotional depth.",
                category="Genre",
                genre="Pop",
                price=9.99,
                rating=4.6,
                downloads=892
            ),
            
            # Genre: Rock
            MarketplaceAdapter(
                name="Rock Grit",
                author="MetalVoice AI",
                description="Powerful, gritty rock vocals with raw edge. Ideal for hard rock and metal.",
                category="Genre",
                genre="Rock",
                price=14.99,
                rating=4.9,
                downloads=2103
            ),
            MarketplaceAdapter(
                name="Classic Rock Legend",
                author="RetroSound",
                description="Vintage 70s-80s rock style with warm, analog character.",
                category="Genre",
                genre="Rock",
                price=11.99,
                rating=4.7,
                downloads=1456
            ),
            
            # Genre: Jazz
            MarketplaceAdapter(
                name="Smooth Jazz Lounge",
                author="JazzMasters",
                description="Silky smooth jazz vocals perfect for late-night lounges and ballads.",
                category="Genre",
                genre="Jazz",
                price=13.99,
                rating=4.8,
                downloads=734
            ),
            MarketplaceAdapter(
                name="Bebop Scat",
                author="ImprovAI",
                description="Dynamic bebop style with scat singing capabilities and swing feel.",
                category="Genre",
                genre="Jazz",
                price=15.99,
                rating=4.5,
                downloads=423
            ),
            
            # Genre: Hip-Hop
            MarketplaceAdapter(
                name="Trap Flow",
                author="HipHopAI",
                description="Modern trap-style vocals with autotune capabilities and melodic flow.",
                category="Genre",
                genre="Hip-Hop",
                price=16.99,
                rating=4.9,
                downloads=3421
            ),
            MarketplaceAdapter(
                name="Old School Rapper",
                author="90sVibe",
                description="Classic 90s hip-hop vocal style with clear diction and boom-bap energy.",
                category="Genre",
                genre="Hip-Hop",
                price=12.99,
                rating=4.7,
                downloads=1876
            ),
            
            # Genre: Electronic
            MarketplaceAdapter(
                name="EDM Vocalist",
                author="SynthWave Studios",
                description="Clean, powerful vocals optimized for EDM, house, and trance production.",
                category="Genre",
                genre="Electronic",
                price=11.99,
                rating=4.6,
                downloads=2234
            ),
            
            # Mood: Energetic
            MarketplaceAdapter(
                name="High Energy Performer",
                author="MotivateAI",
                description="Explosive, high-energy vocals perfect for workout playlists and hype tracks.",
                category="Mood",
                mood="Energetic",
                price=10.99,
                rating=4.7,
                downloads=1654
            ),
            
            # Mood: Melancholic
            MarketplaceAdapter(
                name="Melancholic Soul",
                author="EmotionWave",
                description="Deep, emotional vocals with melancholic undertones. Great for ballads.",
                category="Mood",
                mood="Melancholic",
                price=13.99,
                rating=4.9,
                downloads=1123
            ),
            MarketplaceAdapter(
                name="Sad Piano Vocal",
                author="TearDrop AI",
                description="Tender, vulnerable vocals perfect for sad piano pieces and emotional storytelling.",
                category="Mood",
                mood="Melancholic",
                price=12.99,
                rating=4.8,
                downloads=987
            ),
            
            # Mood: Romantic
            MarketplaceAdapter(
                name="Romantic Ballad",
                author="LoveNotes",
                description="Warm, intimate vocals designed for love songs and romantic ballads.",
                category="Mood",
                mood="Romantic",
                price=11.99,
                rating=4.8,
                downloads=2456
            ),
            
            # Mood: Chill
            MarketplaceAdapter(
                name="Lo-Fi Chill",
                author="RelaxBeats",
                description="Laid-back, lo-fi vocals with subtle imperfections for authentic chill vibes.",
                category="Mood",
                mood="Chill",
                price=9.99,
                rating=4.6,
                downloads=3102
            ),
            
            # Artist Style (Educational/Practice)
            MarketplaceAdapter(
                name="Classical Opera Style",
                author="OperaAI",
                description="Operatic vocal style for classical music education and practice. Not for commercial use.",
                category="Artist Style",
                price=19.99,
                rating=4.7,
                downloads=456,
                license_type="educational"
            )
        ]
        
        return adapters
    
    def get_all_adapters(self) -> List[Dict[str, Any]]:
        """Get all adapters in catalog."""
        return [adapter.to_dict() for adapter in self.catalog]
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get adapters by category."""
        filtered = [a for a in self.catalog if a.category.lower() == category.lower()]
        return [adapter.to_dict() for adapter in filtered]
    
    def get_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get adapters by genre."""
        filtered = [a for a in self.catalog if a.genre and a.genre.lower() == genre.lower()]
        return [adapter.to_dict() for adapter in filtered]
    
    def get_by_mood(self, mood: str) -> List[Dict[str, Any]]:
        """Get adapters by mood."""
        filtered = [a for a in self.catalog if a.mood and a.mood.lower() == mood.lower()]
        return [adapter.to_dict() for adapter in filtered]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search adapters by name, author, or description."""
        query_lower = query.lower()
        filtered = [
            a for a in self.catalog
            if query_lower in a.name.lower()
            or query_lower in a.author.lower()
            or query_lower in a.description.lower()
        ]
        return [adapter.to_dict() for adapter in filtered]
    
    def get_top_rated(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-rated adapters."""
        sorted_adapters = sorted(self.catalog, key=lambda x: x.rating, reverse=True)
        return [adapter.to_dict() for adapter in sorted_adapters[:limit]]
    
    def get_most_downloaded(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most downloaded adapters."""
        sorted_adapters = sorted(self.catalog, key=lambda x: x.downloads, reverse=True)
        return [adapter.to_dict() for adapter in sorted_adapters[:limit]]
    
    def mock_purchase(self, adapter_id: str) -> Dict[str, Any]:
        """
        Mock purchase of an adapter.
        In production, this would integrate with payment systems.
        """
        adapter = next((a for a in self.catalog if a.id == adapter_id), None)
        
        if not adapter:
            return {
                "success": False,
                "message": "Adapter not found"
            }
        
        # Simulate purchase
        adapter.downloads += 1
        self._save_catalog(self.catalog)
        
        return {
            "success": True,
            "message": f"Successfully purchased '{adapter.name}'!",
            "adapter": adapter.to_dict(),
            "transaction_id": f"MOCK_{adapter_id}_{datetime.now().timestamp()}",
            "note": "This is a mock purchase. No actual payment processed."
        }
    
    def add_adapter(self, adapter: MarketplaceAdapter) -> bool:
        """Add new adapter to marketplace."""
        # Check if adapter already exists
        if any(a.id == adapter.id for a in self.catalog):
            return False
        
        self.catalog.append(adapter)
        self._save_catalog(self.catalog)
        return True
    
    def get_categories(self) -> List[str]:
        """Get unique categories."""
        return list(set(a.category for a in self.catalog))
    
    def get_genres(self) -> List[str]:
        """Get unique genres."""
        genres = [a.genre for a in self.catalog if a.genre]
        return list(set(genres))
    
    def get_moods(self) -> List[str]:
        """Get unique moods."""
        moods = [a.mood for a in self.catalog if a.mood]
        return list(set(moods))


def format_adapter_card(adapter: Dict[str, Any]) -> str:
    """Format adapter info as text card."""
    card = f"""
╔══════════════════════════════════════╗
  {adapter['name']}
╚══════════════════════════════════════╝

Author: {adapter['author']}
Category: {adapter['category']}
{f"Genre: {adapter['genre']}" if adapter.get('genre') else ""}
{f"Mood: {adapter['mood']}" if adapter.get('mood') else ""}

{adapter['description']}

Price: ${adapter['price']}
Rating: {'⭐' * int(adapter['rating'])} ({adapter['rating']}/5.0)
Downloads: {adapter['downloads']:,}
License: {adapter['license_type']}
"""
    return card


if __name__ == "__main__":
    # Example usage
    marketplace = Marketplace()
    
    print("=== Marketplace Demo ===\n")
    
    # Get all adapters
    all_adapters = marketplace.get_all_adapters()
    print(f"Total adapters: {len(all_adapters)}\n")
    
    # Search
    results = marketplace.search("rock")
    print(f"Search 'rock': {len(results)} results")
    for adapter in results:
        print(f"  - {adapter['name']} by {adapter['author']}")
    
    print("\n" + "="*50 + "\n")
    
    # Top rated
    top = marketplace.get_top_rated(3)
    print("Top 3 Rated:")
    for adapter in top:
        print(format_adapter_card(adapter))
