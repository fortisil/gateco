import { useState } from 'react';
import { ConnectionForm } from './ConnectionForm';
import { MigrationProgress } from './MigrationProgress';

type WizardStep = 'choose' | 'credentials' | 'apply' | 'ready';

interface DbSetupStepperProps {
  onClose: () => void;
}

const STEP_LABELS: Record<WizardStep, string> = {
  choose: 'Setup Mode',
  credentials: 'Connection',
  apply: 'Applying',
  ready: 'Complete',
};

const STEP_ORDER: WizardStep[] = ['choose', 'credentials', 'apply', 'ready'];

/**
 * Multi-step database setup wizard rendered as a modal overlay.
 * State machine: choose -> credentials -> apply -> ready
 */
export function DbSetupStepper({ onClose }: DbSetupStepperProps) {
  const [step, setStep] = useState<WizardStep>('choose');
  const [dbUrl, setDbUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const currentIndex = STEP_ORDER.indexOf(step);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Panel */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-xl leading-none"
          aria-label="Close"
        >
          \u00d7
        </button>

        <h2 className="text-lg font-bold text-gray-900 mb-4">Database Setup</h2>

        {/* Step indicator */}
        <div className="flex gap-1 mb-6">
          {STEP_ORDER.map((s, i) => (
            <div key={s} className="flex-1">
              <div className={`h-1.5 rounded-full ${
                i <= currentIndex ? 'bg-blue-500' : 'bg-gray-200'
              }`} />
              <span className={`block text-xs mt-1 ${
                i === currentIndex ? 'text-blue-600 font-medium' : 'text-gray-400'
              }`}>
                {STEP_LABELS[s]}
              </span>
            </div>
          ))}
        </div>

        {/* Step content */}
        {step === 'choose' && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Configure your PostgreSQL database to enable data persistence.
            </p>
            <button
              onClick={() => setStep('credentials')}
              className="w-full px-4 py-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Enter connection details
            </button>
          </div>
        )}

        {step === 'credentials' && (
          <ConnectionForm
            onTestSuccess={(url) => {
              setDbUrl(url);
              setStep('apply');
            }}
            onBack={() => setStep('choose')}
          />
        )}

        {step === 'apply' && (
          <MigrationProgress
            databaseUrl={dbUrl}
            onComplete={() => setStep('ready')}
            onError={(msg) => setErrorMsg(msg)}
          />
        )}

        {step === 'ready' && (
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100">
              <span className="text-green-600 text-2xl">\u2713</span>
            </div>
            <p className="text-gray-700 font-medium">Database is ready!</p>
            <button
              onClick={onClose}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        )}

        {errorMsg && step === 'apply' && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded">
            {errorMsg}
          </div>
        )}
      </div>
    </div>
  );
}
