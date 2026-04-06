const express = require('express');
const axios = require('axios');

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

    // Placeholder for browser-use integration
    // This would call the actual browser-use skill
    const result = {
      action,
      url,
      selector,
      text,
      status: 'simulated',
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// N8n workflow endpoint
app.post('/workflow', async (req, res) => {
  try {
    const { workflow_data } = req.body;

    // Placeholder for n8n workflow integration
    const result = {
      workflow_id: 'wf_' + Date.now(),
      status: 'executed',
      output: workflow_data,
      timestamp: new Date().toISOString()
    };

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Document processing endpoints
app.post('/process-pdf', async (req, res) => {
  try {
    const { file_url, action } = req.body;

    // Placeholder for PDF processing
    const result = {
      file_type: 'pdf',
      action,
      content: 'Extracted text content...',
      pages: 5,
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

    // Placeholder for DOCX processing
    const result = {
      file_type: 'docx',
      action,
      content: 'Document content...',
      paragraphs: 10,
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

    // Placeholder for PPTX processing
    const result = {
      file_type: 'pptx',
      action,
      slides: 8,
      content: 'Presentation content...',
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