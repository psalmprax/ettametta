import React from 'react';

// Polyfill React 19 internals for backward compatibility with third-party libraries (e.g. Framer Motion)
// that expect ReactCurrentBatchConfig to exist in React's secret internals.
if (React) {
  const secretInternals =
    (React as any).__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED ||
    (React as any).__SECRET_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;

  if (secretInternals && !secretInternals.ReactCurrentBatchConfig) {
    secretInternals.ReactCurrentBatchConfig = {
      transition: null,
    };
  }
}
