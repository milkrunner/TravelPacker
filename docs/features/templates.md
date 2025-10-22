# Trip Templates Feature

## Overview

The template system allows you to save frequently-used trip configurations as reusable templates. This is perfect for trips you take regularly, such as:

- Weekend getaways
- Business trips
- Family vacations
- Recurring conferences

## Features

### 1. Save Trip as Template

Convert any existing trip into a reusable template:

- Go to the trip details page
- Click the "💾 Save as Template" button
- Enter a descriptive template name (e.g., "Weekend Getaway", "Business Trip")
- The trip is converted to a template and moved to the templates section

### 2. View Templates

Templates are displayed separately on the home page with:

- Purple accent border for easy identification
- Template name with 💾 icon
- Destination, travelers, and transportation info
- "Use Template" and "View" buttons

### 3. Create Trip from Template

Use a template to quickly create a new trip:

1. Click "Use Template" on any template card
2. The form is pre-filled with:
   - Destination (editable)
   - Travel style (from template)
   - Transportation method (from template)
   - Activities (from template)
   - Travelers (editable)
3. Enter new dates and any additional notes
4. Click "Create Trip from Template"
5. All packing items from the template are automatically copied to the new trip

## Technical Implementation

### Database Schema

```sql
-- Template fields in trips table
is_template BOOLEAN DEFAULT 0,  -- Flag indicating if trip is a template
template_name TEXT              -- Name of the template
```

### Routes

- `POST /trip/<trip_id>/save-as-template` - Convert trip to template
- `GET /trip/from-template/<template_id>` - Show template form
- `POST /trip/from-template/<template_id>` - Create trip from template

### Domain Model

```python
class Trip:
    is_template: bool = False
    template_name: Optional[str] = None
```

### UI Components

- **Home Page**: Separate sections for templates and regular trips
- **Trip Details**: "Save as Template" button (hidden for existing templates)
- **Template Form**: Pre-filled form with template data
- **Modals**: Custom save template modal

## Benefits

- **Time Saving**: Skip repetitive data entry for recurring trips
- **Consistency**: Maintain consistent packing lists across similar trips
- **Flexibility**: Templates can be edited like regular trips
- **Easy Management**: Templates are clearly separated from active trips

## Example Workflow

1. Plan a business trip with all necessary items
2. Save it as "Business Trip Template"
3. Next month, use the template to create a new business trip
4. Update dates and destination
5. All standard business travel items are already in the packing list
6. Add any trip-specific items

## Notes

- Templates retain all trip properties (travel style, transportation, activities)
- Packing items are copied, not shared (changes to the new trip won't affect the template)
- Templates can be deleted like regular trips
- Templates do not show in the "Upcoming Trips" section
