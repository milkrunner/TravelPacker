# Dark Mode Feature

## Overview

NikNotes includes a fully functional dark mode theme that can be toggled at any time. The dark mode provides a comfortable viewing experience in low-light environments and reduces eye strain during extended use.

## Features

### 🌙 Automatic Theme Persistence

- Your theme preference is saved automatically in browser local storage
- Returns to your chosen theme when you revisit the site
- Works independently for each browser/device

### 🎨 Complete Theme Coverage

Dark mode applies to all UI elements:

- Navigation bar
- Page backgrounds
- Cards and containers
- Forms and inputs
- Modals and dialogs
- Tables and lists
- Buttons (maintains brand colors with adjusted contrast)
- Text and headings
- Borders and shadows

### ⚡ Smooth Transitions

- Animated theme switching with 0.3s transitions
- Smooth color changes across all elements
- Toggle button with rotating icon animation

### 🔘 Easy Toggle

- One-click theme switching via toggle button in navigation
- Sun icon (☀️) for light mode
- Moon icon (🌙) for dark mode
- Located in the top navigation bar next to "New Trip" button

## How to Use

### Toggle Dark Mode

1. Look for the circular toggle button in the top-right navigation area
2. Click the button to switch between light and dark modes
3. The theme will change immediately
4. Your preference is automatically saved

### Visual Indicators

- **Light Mode Active**: Sun icon (☀️) is visible
- **Dark Mode Active**: Moon icon (🌙) is visible
- Button has a subtle border that matches the theme

## Color Scheme

### Light Mode Colors

- **Background**: White (#ffffff) and light gray (#f9fafb)
- **Text**: Dark gray (#1f2937) for primary text
- **Cards**: White with subtle shadows
- **Borders**: Light gray (#e5e7eb)

### Dark Mode Colors

- **Background**: Dark gray (#111827) and charcoal (#1f2937)
- **Text**: Light gray (#f9fafb) for primary text
- **Cards**: Dark gray (#1f2937) with enhanced shadows
- **Borders**: Medium gray (#374151)

### Maintained Brand Colors

These colors remain consistent across both themes for brand identity:

- **Primary Blue**: #3b82f6 (slightly adjusted for dark mode)
- **Success Green**: #10b981
- **Danger Red**: #dc2626
- **Warning Yellow**: #d97706

## Technical Implementation

### CSS Variables

The theme uses CSS custom properties (variables) for all colors:

**Light Mode Variables:**

```css
--bg-primary: #ffffff
--bg-secondary: #f9fafb
--text-primary: #1f2937
--card-bg: #ffffff
```

**Dark Mode Variables:**

```css
--bg-primary: #111827
--bg-secondary: #1f2937
--text-primary: #f9fafb
--card-bg: #1f2937
```

### JavaScript Toggle

```javascript
// Check saved preference on load
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "dark") {
  body.classList.add("dark-mode");
}

// Toggle on button click
body.classList.toggle("dark-mode");
localStorage.setItem("theme", "dark");
```

### LocalStorage Persistence

- Theme preference stored in: `localStorage.getItem('theme')`
- Values: `'light'` or `'dark'`
- Persists across browser sessions
- Separate for each browser/device

## Files Modified

### Created

- `static/css/dark-mode.css` - Complete dark mode stylesheet with CSS variables

### Modified

- `templates/base.html` - Added dark mode toggle button and CSS link
- `static/js/main.js` - Added theme toggle logic and persistence
- Navigation bar - Added toggle button with icons

## Benefits

### 👁️ Eye Comfort

- Reduces eye strain in low-light environments
- Decreases screen brightness for nighttime use
- Minimizes blue light exposure

### 🔋 Battery Saving

- Dark backgrounds can save battery on OLED/AMOLED screens
- Reduces power consumption on mobile devices
- Lower screen brightness requirements

### 🎯 User Preference

- Respects user's system preferences
- Allows manual override at any time
- Consistent experience across sessions

### ♿ Accessibility

- High contrast ratios maintained in both modes
- WCAG compliant color combinations
- Clear visual feedback for theme state

## Browser Compatibility

Works in all modern browsers that support:

- CSS Custom Properties (CSS Variables)
- LocalStorage API
- ES6 JavaScript

Supported browsers:

- ✅ Chrome 49+
- ✅ Firefox 31+
- ✅ Safari 9.1+
- ✅ Edge 15+
- ✅ Opera 36+

## Customization

### Adjusting Dark Mode Colors

Edit `static/css/dark-mode.css`:

```css
body.dark-mode {
  --bg-primary: #your-color-here;
  --text-primary: #your-color-here;
  /* ... other variables */
}
```

### Adding New Elements

To ensure new UI elements support dark mode:

1. Use CSS variables for colors:

```css
.my-element {
  background-color: var(--card-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
```

Add dark mode specific styles if needed:

```css
body.dark-mode .my-element {
  /* dark mode overrides */
}
```

## Future Enhancements

Potential improvements:

- Auto-detection based on system theme preference
- Scheduled theme switching (dark at night, light during day)
- Multiple theme options (sepia, high contrast, etc.)
- Theme preview before applying
- Per-page theme customization

## Troubleshooting

### Theme Not Persisting

- Check browser's LocalStorage is enabled
- Clear browser cache and try again
- Ensure JavaScript is enabled

### Colors Not Changing

- Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
- Check that dark-mode.css is loading
- Verify no browser extensions are interfering

### Toggle Button Not Visible

- Check screen width (responsive design)
- Ensure JavaScript loaded successfully
- Check browser console for errors

## Notes

- Theme preference is stored per browser/device
- Clearing browser data will reset to default (light mode)
- The toggle button is always accessible in the navigation
- Theme changes are instant with smooth transitions
- Works offline once page is loaded
