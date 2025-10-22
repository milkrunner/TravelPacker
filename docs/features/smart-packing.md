# Smart Quantity Suggestions - Version 0.8.0

## Overview

NikNotes now includes **intelligent quantity suggestions** that calculate the optimal number of items based on:

- **Trip duration** (number of days)
- **Number of travelers**
- **Item shareability** (can it be shared among travelers?)

## How It Works

### AI Prompt Enhancement

The AI service now generates suggestions in the format: `QUANTITY x ITEM_NAME`

**Examples:**

```text
5 x Pairs of socks          (5-day trip = 5 pairs)
3 x Toothbrush              (3 travelers = 3 toothbrushes)
1 x Toothpaste              (shared among all travelers)
7 x Underwear               (5 days + 2 extra)
2 x Phone charger           (2 travelers)
```

### Smart Calculation Logic

The AI considers multiple factors:

1. **Duration-Based Items**

   - Daily wear items: `duration` quantity
   - Example: 5-day trip → 5 t-shirts, 5 pairs of socks

2. **Per-Person Items**

   - Personal items that cannot be shared
   - Example: 3 travelers → 3 toothbrushes, 3 deodorants

3. **Shared Items**

   - Items that can be shared among all travelers
   - Example: 1 toothpaste, 1 sunscreen, 1 first aid kit

4. **Combination Items**
   - Items that depend on both duration and travelers
   - Example: 3 travelers × 5 days = 15 pairs of socks total

### Parsing Logic

The system uses regex pattern matching to extract quantities:

```python
Pattern: r'^(\d+)\s*x\s*(.+)$'

"5 x Pairs of socks" → quantity=5, name="Pairs of socks"
"1 x Toothpaste"     → quantity=1, name="Toothpaste"
"No quantity"        → quantity=1, name="No quantity" (fallback)
```

## Example Scenarios

### Scenario 1: Solo Business Trip (3 days)

```text
Trip: 1 traveler, 3 days, business style
Suggestions:
- 3 x Business shirts
- 3 x Pairs of socks
- 5 x Underwear (3 days + 2 extra)
- 1 x Toothbrush
- 1 x Toothpaste
- 1 x Laptop charger
```

### Scenario 2: Family Vacation (7 days, 4 people)

```text
Trip: 4 travelers, 7 days, leisure style
Suggestions:
- 28 x Pairs of socks (7 days × 4 people)
- 4 x Toothbrush (one per person)
- 1 x Toothpaste (shared)
- 4 x Swimsuit (one per person)
- 1 x Sunscreen (shared)
- 1 x First aid kit (shared)
```

### Scenario 3: Weekend Adventure (2 days, 2 people)

```text
Trip: 2 travelers, 2 days, adventure style
Suggestions:
- 2 x Hiking boots (one per person)
- 4 x T-shirts (2 days × 2 people)
- 2 x Backpack (one per person)
- 1 x First aid kit (shared)
- 2 x Water bottle (one per person)
```

## Implementation Details

### Files Modified

1. **src/services/ai_service.py**

   - Enhanced `_build_prompt()` with quantity instructions
   - Updated `_get_mock_suggestions()` with smart quantities

2. **web_app.py**
   - Added `_parse_quantity_and_name()` function
   - Updated `regenerate_suggestions()` to use parsed quantities
   - Updated `new_trip()` route to parse quantities

### AI Prompt Template

```python
IMPORTANT: For each item, suggest smart quantities based on:
- Trip duration ({duration} days)
- Number of travelers ({num_travelers} person(s))
- Item shareability (e.g., toothpaste can be shared, but toothbrushes cannot)

Format each line EXACTLY as: "QUANTITY x ITEM_NAME"
Examples:
- "{duration} x Pairs of socks" (one per day)
- "{num_travelers} x Toothbrush" (one per person)
- "1 x Toothpaste" (shared among all travelers)
- "{num_travelers * 2} x Underwear" (multiple per person)
```

## Benefits

✅ **Accurate packing** - No more guessing quantities  
✅ **Avoid overpacking** - Smart shareability logic  
✅ **Save money** - Don't buy duplicates of shared items  
✅ **Customized** - Adapts to your specific trip parameters  
✅ **Transparent** - Clear quantity display in UI

## Testing

The quantity parsing has been tested with various formats:

```python
Test cases:
✓ "5 x Pairs of socks"     → (5, "Pairs of socks")
✓ "1 x Toothpaste"         → (1, "Toothpaste")
✓ "3 x Toothbrush"         → (3, "Toothbrush")
✓ "No quantity item"       → (1, "No quantity item")
✓ "10 X Underwear"         → (10, "Underwear")  # Case insensitive
```

## Future Enhancements

Potential improvements for future versions:

- 📊 **Quantity analytics** - Track common quantity patterns
- 🔄 **User adjustments** - Learn from user's manual quantity changes
- 💡 **Smart recommendations** - "Users with similar trips typically pack X items"
- 🧮 **Advanced calculations** - Weather-adjusted quantities (e.g., more layers in cold weather)
- 🎯 **Activity-based** - Hiking = more socks, Beach = more swimwear

## Version History

- **v0.8.0** (2025-10-20): Initial smart quantity suggestions
  - Duration-based calculations
  - Per-person vs shared items logic
  - Regex-based quantity parsing
  - Mock and AI integration

---

**Next Steps:** Test with real trips and gather user feedback!
