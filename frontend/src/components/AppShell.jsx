import Navbar from './Navbar';
export default function AppShell({ children }) {
  return <><Navbar/><main className="main-area">{children}</main><footer>MicroLearn • Ambiente Virtual de Aprendizagem</footer></>;
}
