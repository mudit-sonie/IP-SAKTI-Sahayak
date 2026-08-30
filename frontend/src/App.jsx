import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Classify from "./pages/Classify";
import Ask from "./pages/Ask";
import Result from "./pages/Result";

export default function App() {
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
