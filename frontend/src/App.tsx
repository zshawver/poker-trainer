import { Routes, Route } from "react-router-dom";

function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <h1 className="text-headline uppercase">Project Name</h1>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      {/* TODO: Add routes here */}
    </Routes>
  );
}
