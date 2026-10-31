import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { DisclaimerBanner } from './components/DisclaimerBanner';

// Pages
import { Dashboard } from './pages/Dashboard';
import { HistoricalTimeline } from './pages/HistoricalTimeline';
import { PolicyPrediction } from './pages/PolicyPrediction';
import { ArrestPrediction } from './pages/ArrestPrediction';
import { Backtesting } from './pages/Backtesting';
import { NewsCenter } from './pages/NewsCenter';
import { NewsVerification } from './pages/NewsVerification';
import { LiveMarket } from './pages/LiveMarket';
import { EventExplorer } from './pages/EventExplorer';
import { ModelInformation } from './pages/ModelInformation';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* Top Universal Disclaimer (10% Accent) */}
      <DisclaimerBanner />

      {/* Main Sticky Navbar (30% Blue Brand & Status) */}
      <Navbar />

      {/* Workspace Body (60% Crisp White & Light Slate) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation */}
        <Sidebar />

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-slate-50/70">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/timeline" element={<HistoricalTimeline />} />
              <Route path="/predict-policy" element={<PolicyPrediction />} />
              <Route path="/predict-arrest" element={<ArrestPrediction />} />
              <Route path="/backtesting" element={<Backtesting />} />
              <Route path="/news" element={<NewsCenter />} />
              <Route path="/verify" element={<NewsVerification />} />
              <Route path="/live" element={<LiveMarket />} />
              <Route path="/events" element={<EventExplorer />} />
              <Route path="/model-info" element={<ModelInformation />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
