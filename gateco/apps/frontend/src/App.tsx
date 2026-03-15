import { Router } from './routes/Router';
import { EntitlementProvider } from './contexts/EntitlementContext';

function App() {
  return (
    <EntitlementProvider>
      <Router />
    </EntitlementProvider>
  );
}

export default App;
