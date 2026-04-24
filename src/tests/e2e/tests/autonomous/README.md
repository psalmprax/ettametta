# Autonomous Operations Test Suite

## Overview

This test suite validates Step 4 of the Ettametta platform: **Autonomous Operations**. It covers the Agent Zero (Autonomous Director) and Nexus Flow systems that enable fully automated content creation pipelines.

## Test Files

### 1. `agent_zero_autonomous.spec.ts`
Core tests for Agent Zero autonomous operations:
- Launch and stop autonomous director
- Verify autonomous execution states (SCOUTING, SCREENING, BRAINSTORMING, RENDERING, PUBLISHING)
- Monitor insights oracle and strategy generation
- Validate console logging and system monitoring

### 2. `autonomous_operations.spec.ts`
Comprehensive end-to-end tests:
- Complete autonomous cycle with all phases
- Nexus Flow composition pipeline
- Node visualization and interaction
- Strategy generation and recommendations
- Workflow integration (Autonomous → Nexus)
- Error handling and force kill scenarios
- Performance under concurrent operations

### 3. `test_helpers.ts`
Reusable test utilities:
- `AutonomousTestHelper` class for common operations
- Assertion helpers
- Test data fixtures

## Test Scenarios

### Agent Zero Scenarios

1. **Launch Director**
   - Navigate to /autonomous
   - Click "Launch Director"
   - Verify state transition to "Autonomous Active"
   - Confirm all pipeline phases visible

2. **Autonomous Loop**
   - Verify SCOUTING phase (trend discovery)
   - Verify SCREENING phase (content filtering)
   - Verify BRAINSTORMING phase (strategy generation)
   - Verify RENDERING phase (video synthesis)
   - Verify PUBLISHING phase (distribution)

3. **Insights Generation**
   - Verify strategy oracle populated
   - Check recommended products
   - Validate viral hooks
   - Confirm optimization suggestions

4. **Console Monitoring**
   - Verify real-time log streaming
   - Check timestamp format
   - Validate log levels (INFO, WARN, ERROR)
   - Test export functionality

### Nexus Flow Scenarios

1. **Pipeline Launch**
   - Navigate to /nexus
   - Select niche and blueprint
   - Click "Launch Pipeline"
   - Verify dispatch confirmation

2. **Node Visualization**
   - Verify pipeline mesh rendering
   - Check node status indicators
   - Validate execution priority
   - Confirm cluster routing

3. **Job Tracking**
   - Monitor activity stream
   - Verify job completion status
   - Check output generation
   - Validate error handling

4. **Integration Workflow**
   - Launch Agent Zero for discovery
   - Capture autonomous insights
   - Navigate to Nexus
   - Use insights for composition
   - Verify end-to-end pipeline

## Running Tests

### Run All Autonomous Tests
```bash
cd src/tests/e2e
npm test -- tests/autonomous/
```

### Run Specific Test File
```bash
npm test -- tests/autonomous/agent_zero_autonomous.spec.ts
```

### Run with UI Mode
```bash
npm run test:ui -- tests/autonomous/
```

### Run Headed Mode
```bash
npm run test:headed -- tests/autonomous/
```

## Configuration

### Base URL
Tests use the base URL configured in `playwright.config.ts`:
- Default: `http://localhost:3000`
- Override: `BASE_URL` environment variable

### Timeouts
- Action timeout: 30 seconds
- Navigation timeout: 60 seconds
- Test timeout: 180 seconds

### Retry Policy
- CI environment: 2 retries
- Local: 0 retries

## Test Data

### Niches
- AI Automation
- Tech Reviews
- Productivity
- Business Growth
- Digital Marketing

### Blueprints
- Cinema Mode
- Story Factory
- Blueprint Templates
- Video Assembler

### Personas
- Tech Expert
- Business Coach
- Marketing Guru

## Assertions

### Element Visibility
```typescript
await expect(page.locator('text=Launch Director')).toBeVisible();
```

### Text Content
```typescript
await expect(page.locator('h1')).toContainText('Agent Zero');
```

### Count
```typescript
await expect(page.locator('.glass-card')).toHaveCount(4);
```

### URL
```typescript
await expect(page).toHaveURL('/autonomous');
```

## Best Practices

1. **Use Test Helpers**: Leverage `AutonomousTestHelper` for common operations
2. **Explicit Waits**: Use `toBeVisible()` with appropriate timeouts
3. **State Verification**: Always verify state transitions
4. **Error Handling**: Test both success and failure scenarios
5. **Cleanup**: Ensure tests leave system in clean state

## Troubleshooting

### Tests Timing Out
- Increase timeout values in `playwright.config.ts`
- Check if backend services are running
- Verify network connectivity

### Element Not Found
- Verify page has fully loaded
- Check for dynamic content loading
- Use `waitForSelector()` if needed

### Authentication Issues
- Verify test credentials in `beforeEach`
- Check authentication service is running
- Clear browser storage between tests

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:
- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI

Set environment variables:
```bash
export BASE_URL=https://your-test-environment.com
export CI=true
```

## Reporting

HTML reports are generated in `playwright-report/`:
```bash
npm run test:report
```

## Maintenance

### Adding New Tests
1. Create new test file in `tests/autonomous/`
2. Import test helpers
3. Follow existing patterns
4. Add to test suite

### Updating Test Data
1. Modify `testData` in `test_helpers.ts`
2. Update test scenarios as needed
3. Verify all tests pass

### Debugging
1. Run tests in headed mode
2. Use `page.pause()` for inspection
3. Check console logs
4. Review screenshots/videos in report
