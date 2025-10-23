# Google Gemini Integration Setup

NikNotes now uses Google's Gemini AI model for generating intelligent packing suggestions!

## Getting Your API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy your API key

## Configuration

1. Open the `.env` file in your project root
2. Replace `your_api_key_here` with your actual API key:

```bash
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-pro
```

## Supported Models

You can use any of these Gemini models:

- `gemini-pro` - Best for text generation (recommended)
- `gemini-2.5-flash` - Faster, cost-effective
- `gemini-2.5-pro` - Most capable model with longer context

## How It Works

When you create a trip, the AI service:

1. Builds a detailed prompt with your trip information:

   - Destination
   - Duration
   - Number of travelers
   - Travel style (business, leisure, adventure, etc.)
   - Transportation method
   - Activities and special notes

2. Sends the prompt to Gemini
3. Parses the response into a clean list of suggestions
4. Returns personalized packing recommendations

## Fallback Behavior

If no API key is configured or there's an error, the app automatically falls back to mock suggestions based on:

- Travel style
- Transportation method
- Number of travelers

This ensures the app works even without an API key for testing purposes.

## Testing

Run the web application:

```powershell
python web_app.py
```

Or using Docker:

```powershell
docker compose up
```

With a valid API key, you'll see AI-generated suggestions. Without one, you'll see mock suggestions.

## Cost & Limits

- Gemini API has a generous free tier
- Check current pricing at [Google AI Pricing](https://ai.google.dev/pricing)
- Rate limits apply based on your tier

## Troubleshooting

### Error: "API key not valid"

- Verify your API key is correctly copied
- Ensure no extra spaces in the `.env` file

### Error: "Model not found"

- Check the model name is spelled correctly
- Ensure the model is available in your region

### Using mock suggestions

- This means no valid API key was detected
- The app will still work with pre-defined suggestions
