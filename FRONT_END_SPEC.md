# Demo Dashboard Website - Product Requirements Document (PRD)

## Executive Summary

This PRD defines a visually stunning, demo-only dashboard that showcases sensor data flowing through a Databricks pipeline. The dashboard prioritizes visual impact and smooth animations over production reliability, featuring real-time data visualizations, animated pipeline flows, and interactive maps. Built for demonstration purposes, it will gracefully fallback to mock data when APIs are unavailable, ensuring a flawless demo experience every time.

## Project Overview

### Purpose
Create a read-only demonstration dashboard that visualizes IoT sensor data processing through various Databricks pipeline stages, optimized for sales demos and technical presentations.

### Key Principles
- **Visual Impact First**: Every element should contribute to a "wow" factor
- **Zero Visible Failures**: All errors hidden, automatic fallback to mock data
- **Smooth Animations**: Continuous movement and transitions to convey data flow
- **Demo-Ready**: Works perfectly out of the box with no configuration

### Success Criteria
- Loads instantly with smooth 60fps animations
- Visually engaging enough to make viewers say "whoa"
- Zero error messages ever shown to users
- Works perfectly with or without API connectivity
- Completes full demo flow in under 5 minutes

## Technical Architecture

### Frontend Stack
```
React 18+ with TypeScript
Vite (build tool)
Tailwind CSS (styling)
D3.js (custom visualizations)
Recharts (charts)
Leaflet (maps)
Framer Motion (animations)
React Query or SWR (data fetching)
Lucide React (icons)
```

### Data Flow Architecture
```
Unity Catalog API → 15s Polling → Local Cache → Interpolation Engine → 1s UI Updates → React Components
                ↓ (on failure)
           Mock Data Generator
```

### Color System
```css
:root {
  --primary: #1E40AF;        /* Databricks Blue */
  --primary-dark: #1E3A8A;   /* Darker Blue */
  --success: #10B981;        /* Emerald - Normal */
  --warning: #F59E0B;        /* Amber - Warning */
  --danger: #EF4444;         /* Red - Critical */
  --anomaly: #8B5CF6;        /* Purple - Anomaly */
  --background: #0F172A;     /* Dark Background */
  --surface: #1E293B;        /* Card Background */
  --surface-light: #334155;  /* Elevated Surface */
  --text: #F1F5F9;           /* Light Text */
  --text-muted: #94A3B8;     /* Muted Text */
  --accent: #06B6D4;         /* Cyan Accent */
}
```

## Detailed Page Specifications

### 1. Navigation Header
**Layout:**
```
[Logo] Pipeline Analytics | [Sensors] [Raw] [Schema] [Anomaly] [Aggregated] | ● LIVE [Records: 1.2M/s]
```

**Features:**
- Glassmorphism effect with backdrop blur
- Active tab with animated underline
- Live status indicator with pulsing animation
- Real-time throughput counter
- Smooth transitions between views (slide + fade)

### 2. Sensors Overview Page

**Hero Section:**
- Full-width interactive world map (dark theme)
- 50-100 animated sensor markers with:
  - Pulsing rings (2s cycle, staggered)
  - Color-coded status (green/yellow/red/purple)
  - Clustering at zoom levels
  - Smooth zoom animations on cluster click
  
**Sensor Details Popup (on hover):**
```
┌──────────────────────┐
│ Sensor TX-042        │
│ Location: Dallas, TX │
│ Temp: 72.3°F ↑      │
│ Status: ● Active     │
│ Last: 2 seconds ago  │
└──────────────────────┘
```

**Data Flow Visualization:**
- Particle system showing data flow from sensors to cloud
- Particles should vary in:
  - Speed (based on data rate)
  - Color (based on data quality)
  - Size (based on payload size)
  - Density (based on volume)
- Use WebGL or Canvas for performance

**Sensor Grid:**
- Responsive grid (auto-columns)
- Each card shows:
  - Live sparkline (20 data points, smooth interpolation)
  - Current reading with trend arrow
  - Mini status indicator
  - Subtle glow effect on data update

### 3. Raw Data View

**Pipeline Visualization:**
```
[Sensors] ══════> [Ingestion] ══════> [S3 Raw] ══════> [Unity Catalog]
   📡                 ⚙️                 💾                 🗄️
```
- Animated data packets moving along pipes
- Pipe width represents throughput
- Glow intensity shows activity level

**Live Data Stream Terminal:**
```css
.terminal {
  background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
  font-family: 'Fira Code', monospace;
  box-shadow: 0 0 40px rgba(6, 182, 212, 0.1);
}
```
- Matrix-style data rain effect in background
- Syntax highlighting for JSON
- Smooth auto-scroll with momentum
- Line numbers with subtle glow
- New entries slide in from top with fade

**Statistics Dashboard:**
- Circular gauge for records/second (animated needle)
- Rolling line chart for throughput (last 60 seconds)
- Data volume heat map (hourly breakdown)
- Latency histogram with percentiles

### 4. Schematized Data View

**Enhanced Pipeline:**
```
[Raw] ──validate──> [Schema Engine] ──enrich──> [Structured] ──persist──> [Unity]
                         🔧                          📋
```

**Before/After Comparison:**
- Split-screen with synchronized scrolling
- Diff highlighting:
  - Green: Added fields
  - Blue: Modified fields
  - Yellow: Type conversions
- Animated transitions when switching samples

**Schema Rules Panel:**
- Visual rule cards with icons
- Success rate donut chart with animation
- Rule execution timeline (Gantt-style)
- Live validation counter

### 5. Anomaly Detection View

**Branching Pipeline:**
```
                    ┌──> [Normal] ──> [Standard Processing]
[Ingest] ──analyze──┤
                    └──> [Anomaly] ──> [Alert System]
```
- Animated flow splitting at decision point
- Particle color changes at branch
- Visual "scanner" effect at analysis stage

**Rule Engine Visualization:**
- Node-based rule graph
- Live highlighting of triggered rules
- Threshold sliders with current values
- Rule hit frequency sparklines

**Anomaly Dashboard:**
- 3D heat map (time vs sensor vs severity)
- Animated alert cards sliding in
- Pattern detection visualization (clustering)
- Time-series anomaly score with confidence bands

### 6. Aggregated Data View

**Compression Visualization:**
- Before/after data size comparison (animated bars)
- Compression ratio speedometer
- Cost savings calculator (animated counter)
- Window size selector with preview

**Aggregation Display:**
- Hierarchical treemap of data categories
- Animated transitions on drill-down
- Statistical summary cards with micro-animations
- Trend visualization with prediction bands

## Animation Specifications

### Core Animations
1. **Pulse Effects**: 2s cycle, ease-in-out, 0.8-1.2 scale
2. **Data Particles**: 60fps, variable speed 1-3s transit
3. **Number Counters**: Spring physics, 500ms duration
4. **Page Transitions**: 300ms slide + fade
5. **Hover Effects**: 150ms scale + glow
6. **Loading States**: Shimmer effect, 1.5s cycle
7. **Alert Animations**: Bounce in + glow, 400ms
8. **Graph Updates**: Morph transitions, 200ms
9. **Map Markers**: Staggered fade-in, 50ms delay
10. **Pipeline Flow**: Continuous loop, 3s per segment

### Performance Targets
- 60fps for all animations
- < 100ms interaction response
- < 2s initial page load
- < 16ms frame time

## Mock Data Specifications

### Sensor Data Generator
```typescript
interface SensorData {
  id: string;
  location: { lat: number; lng: number; city: string };
  temperature: number;
  humidity: number;
  pressure: number;
  status: 'active' | 'warning' | 'critical' | 'offline';
  lastReading: Date;
  trend: 'up' | 'down' | 'stable';
  history: Array<{ time: Date; value: number }>;
}
```

### Data Generation Rules
- Temperature: Normal distribution, mean=70°F, std=10
- Anomalies: 5% of readings outside 3 standard deviations
- Update frequency: Gaussian noise around 1s intervals
- Sensor failures: 2% chance per minute, 30s recovery
- Geographic clustering: 70% US, 20% EU, 10% Asia

## API Integration

### Endpoints
```typescript
const API_ENDPOINTS = {
  sensors: {
    status: '/api/sensors/status',
    realtime: '/api/sensors/realtime',
    history: '/api/sensors/:id/history'
  },
  pipeline: {
    raw: '/api/pipeline/raw?limit=50',
    schematized: '/api/pipeline/schematized?limit=50',
    anomalies: '/api/pipeline/anomalies?limit=50',
    aggregated: '/api/pipeline/aggregated?window=1m'
  },
  statistics: {
    throughput: '/api/stats/throughput',
    latency: '/api/stats/latency',
    errors: '/api/stats/errors' // Never displayed
  }
};
```

### Fallback Strategy
```typescript
const fetchWithFallback = async (url: string, mockData: any) => {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) throw new Error();
    return await response.json();
  } catch {
    return generateMockData(mockData);
  }
};
```

## Visual Design Details

### Glass Morphism Cards
```css
.glass-card {
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.1);
  box-shadow: 
    0 0 40px rgba(6, 182, 212, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
```

### Glow Effects
```css
.glow-effect {
  box-shadow: 
    0 0 20px currentColor,
    0 0 40px currentColor,
    0 0 60px currentColor;
  animation: pulse-glow 2s ease-in-out infinite;
}
```

### Data Flow Pipes
```css
.data-pipe {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(6, 182, 212, 0.5),
    transparent
  );
  background-size: 200% 100%;
  animation: flow 2s linear infinite;
}
```

## Demo Mode Features

### URL Parameters
- `?demo=auto` - Auto-advance through views (30s each)
- `?speed=0.5x|1x|2x|4x` - Animation speed multiplier
- `?sensors=10-500` - Number of sensors to display
- `?theme=dark|light|contrast` - Color theme
- `?data=live|mock|hybrid` - Data source mode
- `?view=sensors|raw|schema|anomaly|aggregated` - Initial view

### Guided Tour Mode
- Spotlight effect highlighting key features
- Tooltip explanations for each section
- Auto-progression with pause/play controls
- Skip to specific sections

## Comprehensive To-Do List

### Setup & Infrastructure (4 items)
1. **Initialize Vite + React + TypeScript project** with proper folder structure (/components, /pages, /hooks, /utils, /mock)
2. **Configure Tailwind CSS** with custom color palette, glass morphism utilities, and animation classes
3. **Install and configure all dependencies** (D3.js, Recharts, Leaflet, Framer Motion, React Query, Lucide React)
4. **Set up mock data generator service** with realistic sensor data, anomaly injection, and temporal patterns

### Core Layout & Navigation (3 items)
5. **Build responsive navigation header** with glassmorphism effect, active tab indicators, and live status badge
6. **Implement view routing system** with Framer Motion page transitions and URL parameter parsing
7. **Create base layout components** including Container, Card, GlassCard, and AnimatedNumber

### Sensors Overview Page (5 items)
8. **Integrate Leaflet map** with dark theme, custom markers, clustering, and smooth zoom animations
9. **Build particle flow system** using Canvas/WebGL for sensor-to-cloud data visualization
10. **Create sensor grid component** with sparklines, live updates, and hover effects
11. **Implement sensor popup tooltips** with real-time data and status indicators
12. **Add sensor status legend** and filtering controls with animated transitions

### Raw Data View (3 items)
13. **Design pipeline visualization** with animated SVG pipes and data packet animations
14. **Build terminal-style log viewer** with syntax highlighting, auto-scroll, and matrix rain background
15. **Create statistics dashboard** with circular gauges, rolling charts, and heat maps

### Schematized Data View (3 items)
16. **Implement before/after comparison viewer** with synchronized scrolling and diff highlighting
17. **Build schema rules panel** with visual rule cards and success rate animations
18. **Create validation timeline** component with Gantt-style visualization

### Anomaly Detection View (4 items)
19. **Design branching pipeline visualization** with animated flow splitting and scanner effects
20. **Build rule engine graph** with node-based visualization and live rule triggering
21. **Create anomaly heat map** using D3.js with 3D effect and drill-down capability
22. **Implement alert card system** with slide-in animations and severity indicators

### Aggregated Data View (3 items)
23. **Build compression visualization** with animated size comparisons and savings calculator
24. **Create hierarchical treemap** with drill-down animations and category breakdowns
25. **Implement trend prediction chart** with confidence bands and extrapolation

### Data & Performance (4 items)
26. **Set up data fetching layer** with 15-second polling, automatic fallback, and caching
27. **Implement data interpolation engine** for smooth 1-second UI updates between fetches
28. **Add performance monitoring** to ensure 60fps animations and optimize render cycles
29. **Create loading states** with skeleton screens and shimmer effects

### Polish & Demo Features (4 items)
30. **Add URL parameter handling** for demo mode, speed control, and view selection
31. **Implement guided tour mode** with spotlight effects and auto-progression
32. **Add keyboard shortcuts** for view navigation and animation control
33. **Final visual polish pass** including micro-interactions, sound effects (optional), and Easter eggs

## Development Guidelines

### Code Organization
```
src/
├── components/
│   ├── common/
│   ├── visualizations/
│   └── animations/
├── pages/
├── hooks/
├── utils/
├── mock/
└── styles/
```

### Component Patterns
- Use compound components for complex UI
- Implement render props for flexible visualizations
- Use custom hooks for data fetching and animation
- Memoize expensive computations

### Performance Optimizations
- Virtualize long lists
- Use CSS transforms for animations
- Implement progressive rendering
- Lazy load heavy visualizations
- Use Web Workers for data processing

## Deployment Configuration

### Environment Variables
```env
VITE_API_BASE_URL=https://api.demo.databricks.com
VITE_POLLING_INTERVAL=15000
VITE_UPDATE_INTERVAL=1000
VITE_MOCK_DATA_ENABLED=true
VITE_ANIMATION_SPEED=1
```

### Build Configuration
```javascript
// vite.config.ts
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'charts': ['d3', 'recharts'],
          'maps': ['leaflet'],
          'animations': ['framer-motion']
        }
      }
    }
  }
}
```

### Hosting Requirements
- Static site hosting (Vercel/Netlify recommended)
- CDN for assets
- No backend required
- No authentication needed

## Notes for Implementation

This dashboard prioritizes visual impact and smooth user experience over production reliability. Every design decision should enhance the "wow factor" while maintaining smooth performance. The implementation should feel premium and cutting-edge, using modern web technologies to create an immersive data visualization experience.

Remember: This is a demo showcasing what's possible, not what's practical. Push the boundaries of web visualization while ensuring the demo never fails visibly.

---

**End of PRD**
