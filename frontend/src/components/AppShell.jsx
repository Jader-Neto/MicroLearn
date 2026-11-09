import Navbar from './Navbar';
export default function AppShell({ children }) {
  return <><Navbar/><main className="main-area">{children}</main><footer>MicroLearn • Engenharia de Software 2026.2 • Sprint 4</footer></>;
}
