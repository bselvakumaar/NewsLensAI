# NewsLensAI MVP - Quick Reference Guide

## 🚀 Start Development in 5 Minutes

```bash
# 1. Navigate to client
cd client

# 2. Install dependencies (first time only)
npm install

# 3. Start dev server
npm start

# 4. Open browser → http://localhost:3000
```

## 📂 Key Files to Know

| File | Purpose |
|------|---------|
| `src/App.js` | Main app component with routing |
| `src/components/ChatInterface.js` | Chat UI component |
| `src/services/api.js` | Backend API client |
| `src/config/gcp.js` | GCP configuration |
| `.env` | Environment variables |
| `src/styles/` | Component styles |

## 🔌 API Endpoints

```bash
# Health Check
GET /health

# Chat (RAG)
POST /api/chat
Body: {"session_id": "...", "query": "..."}

# News
GET /api/news?region=India&topic=Politics&limit=12

# Sentiment
GET /api/sentiment?entity=Name&days=7

# Admin Stats
GET /api/admin/stats
```

## 🎨 Component Features

### ChatInterface
- ✅ Multi-turn conversation
- ✅ Source attribution
- ✅ Loading states
- ✅ Auto-scroll to latest
- ✅ Suggestion pills

### NewsDisplay
- ✅ Responsive grid layout
- ✅ Article cards with metadata
- ✅ Image support
- ✅ Read more links
- ✅ Empty states

### SentimentDashboard
- ✅ Sentiment meter visualization
- ✅ Positive/Neutral/Negative counts
- ✅ Recent mentions
- ✅ Entity tracking
- ✅ Color-coded sentiment

## 🌐 Google Cloud Services Used

```
New Project
├── Cloud Run (API backend)
│   ├── 512MB RAM
│   └── 1 vCPU
├── Cloud SQL (PostgreSQL + pgvector)
│   ├── f1-micro tier
│   └── 10GB storage
├── Vertex AI (LLM)
│   ├── Gemini 1.5 Flash
│   └── Text Embeddings
├── Cloud Scheduler (Jobs)
├── Cloud Storage (Uploads)
├── Redis (Cache)
├── Cloud Logging
└── Cloud Build (CI/CD)
```

## 🛠️ Development Commands

```bash
# Frontend only
npm start              # Dev server on :3000
npm run build          # Production build
npm test              # Run tests

# Backend (when ready)
python -m uvicorn main:app --reload  # Dev server on :8000
```

## 📦 Package.json Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-scripts": "5.0.1"
}
```

## 🔐 Environment Variables

```env
REACT_APP_GCP_PROJECT_ID=newslensai-dev
REACT_APP_GCP_REGION=asia-south1
REACT_APP_ENV=development
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ADMIN_TOKEN=dev-token
```

## 🎯 MVP Components Status

- ✅ **Chat Interface** - Ready
- ✅ **News Display** - Ready  
- ⏳ **Sentiment Dashboard** - UI Ready (API pending)
- 🚫 **WhatsApp Bot** - Phase 3
- 🚫 **Election Tracker** - Phase 3
- 🚫 **Financial Intelligence** - Phase 2

## 📱 Responsive Breakpoints

- Desktop: 1200px+ (full sidebar)
- Tablet: 768px (smaller cards)
- Mobile: 480px (stack layout)

## 🎨 Color Scheme

```css
Primary Gradient: #667eea → #764ba2
Success Green: #4CAF50
Alert Yellow: #FFC107
Error Red: #F44336
Neutral Gray: #f0f0f0
```

## 🧪 Testing the UI

1. **Chat Component**
   - Type message → Send → See response
   - Check sources appear with articles
   - Try suggestion pills

2. **News Component**
   - Click "News" tab
   - Load articles
   - Check responsive grid

3. **Layout**
   - Resize window
   - Check mobile layout
   - Verify sidebar functionality

## 🔧 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Port 3000 in use | `PORT=3001 npm start` |
| CORS errors | Check API_URL in .env |
| Styling not loading | Hard refresh (Ctrl+Shift+R) |
| Node modules error | Delete `node_modules`, run `npm install` |
| Build fails | Check Node version (14+) |

## 📊 Build Size

```
React App: ~3.5 MB (gzipped: ~1.2 MB)
Expectations:
- Initial load: 2-3 seconds
- Chat response: <4 seconds
- News load: <2 seconds
```

## 🚀 Next: Build Backend

When ready to add backend:

1. Create `backend/` folder
2. Initialize FastAPI project
3. Implement `/api/chat` endpoint
4. Add Vertex AI integration
5. Connect to Cloud SQL
6. Test with frontend

## 📚 Resources

- React Docs: https://react.dev
- GCP Console: https://console.cloud.google.com
- Cloud Run: https://cloud.google.com/run/docs
- Vertex AI: https://cloud.google.com/vertex-ai/docs

## 💡 Pro Tips

1. **Local Testing**: Use mock data in `.env` for testing without backend
2. **Performance**: React DevTools browser extension helps debugging
3. **Styling**: VS Code CSS Intellisense extension recommended
4. **GCP**: Enable billing alerts at $10 to prevent charges
5. **Version Control**: Never commit `.env` files (add to `.gitignore`)

## 📞 Getting Help

- Check console (F12 → Console tab)
- Review error messages carefully
- Check browser DevTools Network tab
- Verify API endpoint URLs
- Check GCP Cloud Logging

---

**Quick Links:**
- [Full Setup Guide](./SETUP_GUIDE.md)
- [Product Requirements](./docs/NewsLensAI_PRD.md)
- [GCP Configuration](./client/src/config/gcp.js)

**Status**: MVP Ready for Backend Connection
