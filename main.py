"""
NikNotes - AI-Powered Trip Packing Assistant
Main application entry point
"""

from src.app import NikNotesApp


def main():
    """Run the NikNotes application"""
    app = NikNotesApp()
    app.run()


if __name__ == "__main__":
    main()
