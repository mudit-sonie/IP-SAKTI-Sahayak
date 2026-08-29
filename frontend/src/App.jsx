import { useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";
import "./App.css";
import Classify from "./pages/Classify";
import Ask from "./pages/Ask";
import Result from "./pages/Result";

function Home() {
  const [jurisdiction, setJurisdiction] = useState("india");
  const navigate = useNavigate();

  function startClassification() {
    navigate("/classify", {
      state: { jurisdiction },
    });
  }

  return (
    <div className="app">
      <header className="navbar">
        <div className="logo">
          IP-SAKTI <span>Sahayak</span>
        </div>

        <div className="nav-tag">
          Ayurveda • IPR • Regulatory Guidance
        </div>
      </header>

      <main className="hero">
        <div className="badge">AI-POWERED IP & REGULATORY ASSISTANT</div>

        <h1>
          Protecting Ayurveda&apos;s
          <br />
          <span>Innovation & Knowledge</span>
        </h1>

        <p className="description">
          IP-SAKTI Sahayak helps Ayurveda practitioners, researchers,
          startups and MSMEs navigate intellectual property and regulatory
          requirements with source-cited guidance.
        </p>

        <div className="jurisdiction-card">
          <h2>Choose your jurisdiction</h2>

          <p>
            Select the legal framework you want your answer to be based on.
          </p>

          <div className="toggle-container">
            <button
              className={jurisdiction === "india" ? "toggle active" : "toggle"}
              onClick={() => setJurisdiction("india")}
            >
              🇮🇳 India
            </button>

            <button
              className={
                jurisdiction === "international" ? "toggle active" : "toggle"
              }
              onClick={() => setJurisdiction("international")}
            >
              🌍 International
            </button>
          </div>

          <div className="selected-jurisdiction">
            Selected:{" "}
            <strong>
              {jurisdiction === "india" ? "India" : "International"}
            </strong>
          </div>
        </div>

        <div className="disclaimer">
          <strong>⚠ Important:</strong> IP-SAKTI Sahayak provides information
          and guidance for educational and informational purposes only. It does
          not constitute legal advice.
        </div>

        <button className="start-button" onClick={startClassification}>
          Start with Formulation Classification →
        </button>

        <p className="privacy-note">
          Your information should not include confidential or sensitive
          personal data.
        </p>
      </main>

      <footer>
        <p>IP-SAKTI Sahayak • Smart India Hackathon 2026</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/classify" element={<Classify />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

