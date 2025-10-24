"""
PDF Export Service
Generates PDF documents for trip packing lists
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from typing import List, Dict
from src.models.trip import Trip
from src.models.packing_item import PackingItem


class PDFService:
    """Service for generating PDF exports of packing lists"""
    
    @staticmethod
    def generate_packing_list_pdf(trip: Trip, items: List[PackingItem], progress: Dict) -> BytesIO:
        """
        Generate a PDF document for a trip's packing list
        
        Args:
            trip: Trip object with trip details
            items: List of packing items
            progress: Dictionary with packing progress statistics
            
        Returns:
            BytesIO object containing the PDF data
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563')
        )
        
        # Title
        title = Paragraph(f"Packing List: {trip.destination}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Trip Details Section
        trip_details_data = [
            ['Dates:', f"{trip.start_date} to {trip.end_date}"],
            ['Duration:', f"{trip.duration} days"],
            ['Travelers:', f"{len(trip.travelers)} ({', '.join(trip.travelers)})"],
            ['Travel Style:', trip.travel_style_display],
            ['Transportation:', trip.transport_display],
        ]
        
        if trip.activities:
            trip_details_data.append(['Activities:', ', '.join(trip.activities)])
        
        trip_table = Table(trip_details_data, colWidths=[1.5*inch, 4.5*inch])
        trip_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(trip_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Progress Section
        progress_heading = Paragraph("Packing Progress", heading_style)
        elements.append(progress_heading)
        
        completion = progress['completion_percentage']
        packed = progress['packed_items']
        unpacked = progress['unpacked_items']
        total = packed + unpacked
        
        progress_text = Paragraph(
            f"<b>{completion:.0f}% Complete</b> - {packed} of {total} items packed",
            normal_style
        )
        elements.append(progress_text)
        elements.append(Spacer(1, 0.3*inch))
        
        # Weather Information
        if trip.weather_conditions:
            weather_heading = Paragraph("Weather Information", heading_style)
            elements.append(weather_heading)
            weather_text = Paragraph(trip.weather_conditions, normal_style)
            elements.append(weather_text)
            elements.append(Spacer(1, 0.3*inch))
        
        # Packing List by Category
        packing_heading = Paragraph("Packing List", heading_style)
        elements.append(packing_heading)
        elements.append(Spacer(1, 0.1*inch))
        
        # Group items by category
        items_by_category = {}
        for item in sorted(items, key=lambda x: x.display_order):
            category = item.category.value
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)
        
        # Create table for each category
        for category, category_items in sorted(items_by_category.items()):
            # Category header
            category_title = Paragraph(
                f"<b>{category.title()}</b>",
                ParagraphStyle(
                    'CategoryTitle',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=colors.HexColor('#374151'),
                    spaceAfter=6
                )
            )
            elements.append(category_title)
            
            # Items table
            table_data = [['[ ]', 'Item', 'Qty', 'Notes']]
            
            for item in category_items:
                checkbox = '[X]' if item.is_packed else '[ ]'
                name = item.name
                if item.is_essential:
                    name = f"* {name}"
                quantity = str(item.quantity) if item.quantity > 1 else ''
                notes = item.notes or ''
                table_data.append([checkbox, name, quantity, notes])
            
            items_table = Table(
                table_data,
                colWidths=[0.4*inch, 3*inch, 0.6*inch, 2*inch]
            )
            
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                
                # Padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Special Notes
        if trip.special_notes:
            notes_heading = Paragraph("Special Notes", heading_style)
            elements.append(notes_heading)
            notes_text = Paragraph(trip.special_notes, normal_style)
            elements.append(notes_text)
            elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            alignment=TA_CENTER
        )
        footer_text = Paragraph(
            f"Generated by NikNotes on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            footer_style
        )
        elements.append(footer_text)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
