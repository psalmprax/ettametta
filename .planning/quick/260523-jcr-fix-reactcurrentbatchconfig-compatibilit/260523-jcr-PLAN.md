# Quick Task Plan: Fix ReactCurrentBatchConfig compatibility issue in dashboard

## Goal
Resolve the "Cannot read properties of undefined (reading 'ReactCurrentBatchConfig')" error in the dashboard application under React 19 by polyfilling/mocking the missing property on React's secret internals.

## Proposed Changes

### Dashboard
#### [MODIFY] [RootClientContext.tsx](file:///home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/components/providers/RootClientContext.tsx)
- Import `React` first.
- Inject the polyfill for React 19 compatibility before other providers or components are initialized.

## Verification Plan
- Build the dashboard using `npm run build --workspace=apps/dashboard` to verify no compilation/TypeScript errors.
