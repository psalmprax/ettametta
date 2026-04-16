const express = require('express');
const axios = require('axios');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const pdfParse = require('pdf-parse');
const mammoth = require('mammoth');

const app = express();
const PORT = 3002;

app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'node-skills' });
});

// Browser automation endpoint
app.post('/browser-use', async (req, res) => {
  try {
    const { action, url, selector, text } = req.body;

    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    let result = { action, url, selector, text, status: 'completed' };

    if (action === 'navigate') {
      await page.goto(url, { waitUntil: 'networkidle2' });
      result.title = await page.title();
      result.url = page.url();
    } else if (action === 'click' && selector) {
      await page.goto(url, { waitUntil: 'networkidle2' });
      await page.click(selector);
      await page.waitForTimeout(2000);
      result.clicked = true;
    } else if (action === 'extract' && selector) {
      await page.goto(url, { waitUntil: 'networkidle2' });
      const extracted = await page.$eval(selector, el => el.textContent || el.innerHTML);
      result.extracted = extracted;
    } else if (action === 'type' && selector && text) {
      await page.goto(url, { waitUntil: 'networkidle2' });
      await page.type(selector, text);
      result.typed = text.length;
    }

    await browser.close();

    result.timestamp = new Date().toISOString();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Workflow execution endpoint
app.post('/workflow', async (req, res) => {
  try {
    const { steps, name } = req.body;

    // Simple workflow execution
    const results = [];
    let currentData = {};

    for (const step of steps) {
      const stepResult = await executeWorkflowStep(step, currentData);
      results.push(stepResult);
      currentData = { ...currentData, ...stepResult.output };
    }

    const result = {
      workflow_id: name || 'wf_' + Date.now(),
      status: 'executed',
      steps_executed: results.length,
      results: results,
      final_output: currentData,
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

async function executeWorkflowStep(step, inputData) {
  const { action, params } = step;

  try {
    let output = {};

    if (action === 'http_request') {
      const response = await axios(params);
      output = { status: response.status, data: response.data };
    } else if (action === 'transform') {
      output = { transformed: params.transform_function ? eval(params.transform_function)(inputData) : inputData };
    } else if (action === 'condition') {
      const condition = params.condition;
      output = { condition_met: eval(condition.replace('input', 'inputData')) };
    } else if (action === 'delay') {
      await new Promise(resolve => setTimeout(resolve, params.ms || 1000));
      output = { delayed: true };
    } else {
      output = { action, params, executed: true };
    }

    return {
      step: action,
      success: true,
      output: output,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      step: action,
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

// Document processing endpoints
app.post('/process-pdf', async (req, res) => {
  try {
    const { file_url, action } = req.body;

    // Download file
    const response = await axios.get(file_url, { responseType: 'arraybuffer' });
    const buffer = Buffer.from(response.data);

    // Parse PDF
    const data = await pdfParse(buffer);

    const result = {
      file_type: 'pdf',
      action,
      content: data.text.substring(0, 5000), // Limit content size
      pages: data.numpages,
      info: data.info,
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/process-docx', async (req, res) => {
  try {
    const { file_url, action } = req.body;

    // Download file
    const response = await axios.get(file_url, { responseType: 'arraybuffer' });
    const buffer = Buffer.from(response.data);

    // Parse DOCX
    const result_docx = await mammoth.extractRawText({ buffer: buffer });

    const result = {
      file_type: 'docx',
      action,
      content: result_docx.value.substring(0, 5000), // Limit content size
      messages: result_docx.messages,
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/process-pptx', async (req, res) => {
  try {
    const { file_url, action } = req.body;

    // For PPTX, we'll download and provide basic info since full parsing is complex
    const response = await axios.get(file_url, { responseType: 'arraybuffer' });
    const buffer = Buffer.from(response.data);

    // Basic PPTX processing (placeholder for full implementation)
    const result = {
      file_type: 'pptx',
      action,
      file_size: buffer.length,
      content: 'PPTX processing requires additional libraries for full slide extraction',
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Proxy endpoint to call our main API
app.post('/api-proxy/*', async (req, res) => {
  try {
    const path = req.params[0];
    const apiUrl = `http://api:8000/${path}`;

    const response = await axios.post(apiUrl, req.body, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.authorization || ''
      }
    });

    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

app.listen(PORT, () => {
  console.log(`Node.js skills service running on port ${PORT}`);
});