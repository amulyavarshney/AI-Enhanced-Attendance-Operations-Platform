# AI-Enhanced Attendance Platform Frontend

The frontend application for the AI-Enhanced Attendance Operations Platform built with React, TypeScript, and Tailwind CSS.

## Overview

This frontend provides a modern, responsive user interface for managing employee attendance, team organization, and accessing AI-powered insights. It communicates with the FastAPI backend to provide a complete attendance management solution.

## Tech Stack

- **Framework**: React with TypeScript
- **UI Library**: shadcn/ui components
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Date/Time Handling**: date-fns
- **Charts**: Recharts for data visualization

## Key Features

- **Dashboard**: Overview of attendance metrics and recent activity
- **Teams Management**: Create, edit, and manage teams
- **Employee Directory**: Manage employee information and view attendance history
- **Attendance Tracking**: Record and manage daily attendance
- **Analytics**: Visual reports and statistics
- **AI Insights**: Natural language queries and AI-generated insights
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── layout/         # Layout components (header, sidebar, etc.)
│   │   └── ui/             # UI primitives from shadcn/ui
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utility functions and configs
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Dashboard page
│   │   ├── Teams.tsx       # Teams management
│   │   ├── Employees.tsx   # Employee management
│   │   ├── Attendance.tsx  # Attendance tracking
│   │   ├── Analytics.tsx   # Analytics and reports
│   │   └── AIInsights.tsx  # AI Insights interface
│   ├── services/           # API service functions
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── App.tsx             # Main application component
│   └── main.tsx            # Application entry point
├── public/                 # Static assets
├── index.html              # HTML template
├── vite.config.ts          # Vite configuration
├── tailwind.config.ts      # Tailwind CSS configuration
└── package.json            # Project dependencies
```

## Pages

### Dashboard
- Overview of key metrics
- Recent activity feed
- Quick access to common actions

### Teams
- Team creation and management
- Team analytics view
- Employee assignments

### Employees
- Employee directory with search and filtering
- Employee profile management
- Attendance history for individual employees

### Attendance
- Daily attendance recording
- Status updates (present, absent, WFH, etc.)
- Check-in/check-out tracking

### Analytics
- Attendance trends visualization
- Team comparison charts
- Exportable reports

### AI Insights
- Natural language query interface
- AI-generated attendance insights
- Custom SQL-based analytics

## Development

### Prerequisites
- Node.js (v20+)
- npm or bun

### Setup

1. Clone the repository and navigate to the frontend directory:
```sh
cd frontend
```

2. Install dependencies:
```sh
npm install
# or
bun install
```

3. Create a `.env` file:
```
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```sh
npm run dev
# or
bun run dev
```

The application will be available at http://localhost:3000.

### Build for Production

```sh
npm run build
# or
bun run build
```

## API Integration

The frontend communicates with the FastAPI backend through services defined in the `services` directory. All API calls are centralized and consistent error handling is implemented.

## UI Component Library

This project uses shadcn/ui, a collection of reusable components built on Radix UI primitives. Components are imported and customized for the application's needs.

## License

This project is licensed under the MIT License - see the main [LICENSE](../LICENSE) file for details.
