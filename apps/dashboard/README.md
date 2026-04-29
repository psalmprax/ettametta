# Playwright Auth Flow Test Script
# Run the following commands to execute the tests:

# 1. Install Playwright (if not already installed)
npm init -y
npm install -D @playwright/test
npx playwright install

# 2. Run tests against local dashboard
BASE_URL=http://localhost:7202 npx playwright test

# 3. Run tests against remote server
BASE_URL=http://149.104.110.122:7202 npx playwright test

# 4. Generate HTML test report
npx playwright show-report

# 5. Run with headed mode (watch tests execute)
BASE_URL=http://localhost:7202 npx playwright test --headed

# 6. Run with tracing enabled
BASE_URL=http://localhost:7202 npx playwright test --trace on
