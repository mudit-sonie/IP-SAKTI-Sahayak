import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Classify from "./pages/Classify";
import Ask from "./pages/Ask";
import Result from "./pages/Result";
import Matters from "./pages/Matters";
import Matter from "./pages/Matter";
import Coverage from "./pages/Coverage";
import Compare from "./pages/Compare";
import Fees from "./pages/Fees";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/classify" element={<Classify />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/result" element={<Result />} />
        <Route path="/matters" element={<Matters />} />
        <Route path="/matters/:id" element={<Matter />} />
        <Route path="/coverage" element={<Coverage />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/fees" element={<Fees />} />
      </Routes>
    </BrowserRouter>
  );
}
