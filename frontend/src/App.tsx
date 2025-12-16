import React, { useEffect, useState } from "react";
import AnomalyVisualizationDashboard from "./components/AnomalyVisualizationDashboard";
import { componentRegistry } from "./adkComponentRegistry";
import { Chat } from "./components/chat";


function App() {
  return (
    <div className="app">
      <Chat />
    </div>
  );
}

export default App;