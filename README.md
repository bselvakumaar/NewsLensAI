# NewsLensAI MVP - React Frontend

This is the React-based MVP frontend for NewsLensAI, a RAG-powered India & Global News Intelligence Platform.

## 🎯 MVP Features

- **💬 Conversational AI Chat**: Multi-turn dialogue with RAG-backed, citation-verified responses
- **📰 News Display**: Browse latest India & Global news with topics and regions
- **📊 Sentiment Dashboard**: Real-time sentiment analysis (Phase 2 - coming soon)
- **🔄 Session Management**: Persistent conversation sessions
- **🌐 Google Cloud Integration**: Built for GCP Free Tier

## 🚀 Quick Start

### Prerequisites

- Node.js 14+ and npm
- Google Cloud Account (free tier eligible)
- Python 3.8+ (for backend development)

### 1. Clone & Setup

```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your Google Cloud project details
```

### 2. Local Development

```bash
# Start the React development server
npm start
# App opens at http://localhost:3000
```

### 3. Build for Production

```bash
npm run build
# Build output in ./build directory
```

## 📁 Project Structure

```
client/
├── src/
│   ├── components/           # React UI components
│   │   ├── ChatInterface.js
│   │   ├── NewsDisplay.js
│   │   └── SentimentDashboard.js
│   ├── services/
│   │   └── api.js            # Backend API client
│   ├── config/
│   │   └── gcp.js            # Google Cloud configuration
│   ├── styles/
│   │   ├── ChatInterface.css
│   │   ├── NewsDisplay.css
│   │   └── SentimentDashboard.css
│   ├── App.js
│   └── App.css
├── .env.example
└── package.json
```

## 🌍 Environment Variables

```env
REACT_APP_GCP_PROJECT_ID=newslensai-dev
REACT_APP_GCP_REGION=asia-south1
REACT_APP_ENV=development
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Available Scripts

```bash
npm start      # Start development server
npm test       # Run tests
npm run build  # Create production build
```

## ☁️ Google Cloud Deployment

See `src/config/gcp.js` for detailed GCP deployment guide.

Key GCP free tier services:
- **Cloud Run**: 180,000 vCPU-seconds/month
- **Cloud SQL**: 1 shared-core instance, 10GB storage
- **Vertex AI**: $300 free credits
- **Cloud Storage**: 5GB/month egress
- **Total Cost**: $0/month during development

## 🔌 API Integration

The frontend connects to FastAPI backend:

```bash
POST /api/chat          # Send chat message
GET  /api/news?...      # Fetch news
GET  /api/sentiment?... # Get sentiment data
GET  /health            # Health check
```

## 📚 Learning Resources

- [React Docs](https://react.dev)
- [Google Cloud Platform](https://cloud.google.com)
- [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
- [Cloud SQL Docs](https://cloud.google.com/sql/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## 🗺️ Phase Roadmap

- **MVP Phase 1** (Current): Chat, News, Sessions
- **Phase 2** (Q2-Q3 2026): Sentiment Analytics
- **Phase 3** (Q3-Q4 2026): WhatsApp Bot, Election Tracker
- **Phase 4** (2027): Advanced Analytics, Predictions

## 📄 License

Proprietary - NewsLensAI MVP

**Version**: 1.0 | **Status**: MVP Development
