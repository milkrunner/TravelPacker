"""
Main application class
"""

from src.services.trip_service import TripService
from src.services.ai_service import AIService
from src.services.packing_list_service import PackingListService


class NikNotesApp:
    """Main application orchestrator"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.trip_service = TripService()
        self.packing_service = PackingListService(self.ai_service)
    
    def run(self):
        """Run the application"""
        print("🎒 Welcome to NikNotes - Your AI-Powered Trip Packing Assistant!")
        print("\nStarting application...\n")
        
        # TODO: Implement CLI or web interface
        self._demo_workflow()
    
    def _demo_workflow(self):
        """Demonstrate the basic workflow"""
        print("Demo: Creating a sample trip...")
        
        # Create a trip
        trip = self.trip_service.create_trip(
            destination="Paris, France",
            start_date="2025-11-01",
            end_date="2025-11-07",
            travelers=["Adult", "Adult"],
            travel_style="leisure",
            transportation="flight"
        )
        
        print(f"✓ Trip created: {trip.destination}")
        print(f"  Duration: {trip.duration} days")
        print(f"  Travelers: {len(trip.travelers)}")
        
        # Generate AI suggestions
        print("\n🤖 Generating AI packing suggestions...")
        suggestions = self.packing_service.generate_suggestions(trip)
        
        print(f"\n✓ Generated {len(suggestions)} suggestions:")
        for item in suggestions[:5]:  # Show first 5
            print(f"  • {item}")
        
        if len(suggestions) > 5:
            print(f"  ... and {len(suggestions) - 5} more items")
        
        print("\n✨ Ready to start packing!")
