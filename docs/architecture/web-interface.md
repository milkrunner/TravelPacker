# NikNotes Web Interface

A beautiful, modern web interface for your AI-powered trip packing assistant!

## 🚀 Getting Started

### Run the Web Application

```powershell
python web_app.py
```

The app will be available at: **<http://localhost:5000>**

## ✨ Features

### 🏠 Home Page

- View all your trips at a glance
- Beautiful card-based layout
- Quick access to trip details
- Create new trips with one click

### ➕ Create Trip

- **Destination & Dates**: Specify where and when you're traveling
- **Travelers**: Define who's coming along (Adults, Children, Infants)
- **Travel Style**: Choose from Business, Leisure, Adventure, Backpacking, Luxury
- **Transportation**: Flight, Road Trip, Train, Cruise, or Other
- **Activities**: List planned activities for better AI suggestions
- **Special Notes**: Add weather info, medical needs, or other requirements
- **AI Suggestions (Optional)**: Choose whether to generate AI-powered packing suggestions
  - Checkbox enabled by default
  - Uncheck to create an empty trip and add items manually
  - Can generate AI suggestions later from the trip view page

### 📋 Trip Details & Packing List

- **Progress Tracking**: Visual progress bar showing packing completion
- **Categorized Items**: Items organized by category (Clothing, Toiletries, Electronics, etc.)
- **Interactive Checkboxes**: Mark items as packed/unpacked in real-time
- **AI Suggestions**: Items suggested by AI are clearly marked
- **Essential Items**: Flag important items you can't forget
- **Add Custom Items**: Manually add items with categories, quantities, and notes
- **Regenerate Suggestions**: Get fresh AI recommendations anytime

### 🎨 User Interface

- **Modern Design**: Clean, professional interface with smooth animations
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Real-time Updates**: Changes reflect immediately without page reload
- **Intuitive Navigation**: Easy to use with clear visual hierarchy
- **Progress Visualization**: See your packing progress at a glance

## 🛠️ Technical Details

### Technologies Used

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Google Gemini API
- **Data Models**: Pydantic for validation

### Project Structure

```file
NikNotes/
├── web_app.py              # Flask application
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── new_trip.html      # Create trip form
│   └── view_trip.html     # Trip details & packing list
└── static/                # Static assets
    ├── css/
    │   └── style.css      # Styles
    └── js/
        └── main.js        # JavaScript
```

## 🎯 API Endpoints

### Web Routes

- `GET /` - Home page (list trips)
- `GET /trip/new` - New trip form
- `POST /trip/new` - Create new trip
- `GET /trip/<trip_id>` - View trip details
- `POST /trip/<trip_id>/delete` - Delete trip

### API Routes (AJAX)

- `POST /api/item/<item_id>/toggle` - Toggle item packed status
- `POST /api/trip/<trip_id>/item` - Add new item
- `DELETE /api/item/<item_id>` - Delete item
- `POST /api/trip/<trip_id>/regenerate` - Get new AI suggestions

## 🎨 Features in Detail

### Smart Item Categorization

The app automatically categorizes items based on keywords:

- **Clothing**: shirts, pants, shoes, jacket, etc.
- **Toiletries**: toothbrush, shampoo, soap, etc.
- **Electronics**: phone, charger, laptop, camera, etc.
- **Documents**: passport, visa, tickets, ID, etc.
- **Medical**: medicine, first aid, bandages, etc.
- **Entertainment**: books, games, kindle, etc.
- **Gear**: backpack, tent, sleeping bag, etc.

### Progress Tracking

- Visual progress bar
- Real-time completion percentage
- Count of packed vs. unpacked items
- Color-coded statistics

### AI-Powered Suggestions

- Context-aware recommendations based on:
  - Destination
  - Trip duration
  - Number of travelers
  - Travel style (business, leisure, etc.)
  - Transportation method
  - Planned activities
- Clearly marked AI suggestions with 🤖 badge
- Ability to regenerate suggestions anytime

## 🔧 Configuration

### Secret Key

For production, change the secret key in `web_app.py`:

```python
app.config['SECRET_KEY'] = 'your-secure-random-key-here'
```

### Port

To change the port, modify the last line in `web_app.py`:

```python
app.run(debug=True, port=5000)  # Change 5000 to your preferred port
```

### Production Deployment

For production, use a WSGI server like Gunicorn:

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## 📱 Mobile Responsive

The interface is fully responsive and works great on:

- Desktop computers
- Tablets
- Mobile phones

## 🎯 Usage Tips

1. **Start Simple**: Create your first trip with basic information
2. **Review AI Suggestions**: Check the AI-generated list and adjust as needed
3. **Add Custom Items**: Manually add items specific to your needs
4. **Mark Essentials**: Flag items you absolutely can't forget
5. **Track Progress**: Check off items as you pack them
6. **Regenerate**: Get fresh suggestions if you need more ideas

## 🐛 Troubleshooting

### Port Already in Use

```powershell
# Kill the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### CSS Not Loading

- Clear browser cache
- Check that `static/` folder exists
- Verify file paths in templates

### AI Not Working

- Ensure `GEMINI_API_KEY` is set in `.env`
- Check [GEMINI_SETUP.md](GEMINI_SETUP.md) for configuration

## 🎉 Enjoy

Your NikNotes web app is ready to help you plan stress-free trips with AI-powered packing suggestions!

Visit: **<http://localhost:5000>**
