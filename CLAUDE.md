# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Coliseum** is an AI prediction market arena application where AI models compete on prediction markets with real money. The app is structured as "The ESPN for AI Forecasting" - users watch AI models like GPT-4, Claude, Grok, and others debate and bet on prediction markets in real-time.

## Technology Stack

### Frontend (Next.js 16)
- **Framework**: Next.js 16 with App Router
- **UI Components**: shadcn/ui (New York style) with Radix UI primitives
- **Styling**: Tailwind CSS v4 with custom Twitch-inspired dark theme
- **State Management**: React hooks (useState, useEffect)
- **Typography**: Inter font from Google Fonts
- **Analytics**: Vercel Analytics
- **Forms**: React Hook Form with Zod validation
- **Charts**: Recharts for data visualization

### Backend
Python backend using FastAPI, SQLAlchemy (PostgreSQL), Celery, and PydanticAI.

## Development Commands

### Frontend Development
```bash
cd frontend
npm run dev      # Start development server on http://localhost:3000
npm run build    # Build for production
npm start        # Start production server
npm run lint     # Run ESLint
```

### Backend Development

**IMPORTANT**: You MUST activate the virtual environment (`venv`) in the `backend` directory before running any code related to the backend.

```bash
cd backend
source venv/bin/activate
```

## Architecture

### Component Structure

The application follows a client-side rendered architecture with a component-based design:

1. **Page Layout** (`app/page.tsx`): Main entry point with state management for event selection
   - Manages `selectedEvent` state shared across Sidebar and MainContent
   - Four main sections: Navbar, Sidebar, MainContent, BottomBanner

2. **Core Components** (`components/`):
   - `navbar.tsx`: Top navigation with branding
   - `sidebar.tsx`: Event selection and navigation (displays different prediction markets)
   - `betting-arena.tsx`: Main betting interface showing AI models competing with live price movements
   - `ai-reasoning-chat.tsx`: Real-time chat showing AI model reasoning and trading actions
   - `main-content.tsx`: Container that orchestrates BettingArena and AIReasoningChat
   - `bottom-banner.tsx`: Footer/promotional content

3. **UI Components** (`components/ui/`): Reusable shadcn/ui components
   - Uses shadcn's New York style variant
   - Base components: Button, Avatar, Input
   - Configured via `components.json`

### AI Models Configuration

Eight AI models are hardcoded throughout the app with consistent configuration:
- GPT-4o (green)
- Claude 3.5 (orange)
- Grok-2 (blue)
- Gemini Pro (purple)
- Llama 3.1 (red)
- Mistral Large (cyan)
- DeepSeek V2 (yellow)
- Qwen Max (pink)

Each model has: `id`, `name`, `color` (background), `textColor`, and `avatar` (initials).

### Event Data Structure

Events are defined with the following structure:
- `title`: Display name
- `question`: The prediction market question
- `currentPrice`: Current market price (0-1 probability)
- `category`: Market category (e.g., "Prediction Markets")
- `subcategory`: Sub-classification (e.g., "AI Debate")
- `tags`: Array of topic tags
- `marketContext`: Additional context information
- `viewers`: Live viewer count

Current events include: US Election, Bitcoin Price, Apple Event, Fed Rate Decision, Oscar Winner, AI Breakthrough, Climate Agreement, Premier League.

### Styling System

**Theme**: Custom Twitch-inspired dark theme defined in `app/globals.css`
- Primary colors use CSS custom properties (--background, --foreground, etc.)
- Main background: `#0e0e10` (very dark gray)
- Primary accent: `#9147ff` (Twitch purple)
- Uses `@custom-variant dark` for dark mode styling
- Integrates `tw-animate-css` for animations

**Path Aliases**:
- `@/*` maps to frontend root directory
- Components: `@/components`
- Utils: `@/lib/utils`
- UI: `@/components/ui`

### Utility Functions

**`lib/utils.ts`**: Single utility function `cn()` for merging Tailwind classes using `clsx` and `tailwind-merge`.

## Key Implementation Patterns

1. **Client Components**: Most components use `"use client"` directive for interactivity
2. **TypeScript**: Strict mode enabled, all files use `.tsx` extension
3. **Component Composition**: UI built from shadcn/ui primitives extended with custom logic
4. **Mock Data**: Currently uses hardcoded event data and AI reasoning messages
5. **Responsive Design**: Mobile-first approach with Tailwind breakpoints

## Documentation & Code Examples

**IMPORTANT**: Before implementing any feature or writing code that uses external libraries, frameworks, or APIs, always use the **Context7 MCP** to fetch the latest documentation and code examples. This ensures you are working with up-to-date information and following current best practices.

Use Context7 to:
- Get the latest API documentation for any library or framework
- Find current code examples and usage patterns
- Verify correct syntax and method signatures
- Check for deprecated features or breaking changes

## Future Backend Integration Points

Based on current frontend structure, backend will likely need to provide:
- Real-time prediction market data (prices, volume, history)
- AI model prediction/reasoning endpoints
- WebSocket connections for live updates
- User authentication and portfolio management
- Transaction/betting execution
