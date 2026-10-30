const assert = require('node:assert/strict');
const fs = require('node:fs');

const workflow = JSON.parse(fs.readFileSync('adk_hiring_agent_n8n_workflow.json', 'utf8'));
for (const item of workflow.nodes.filter((entry) => entry.type === 'n8n-nodes-base.code')) {
  assert.doesNotThrow(() => new Function('$input', '$json', '$node', '$workflow', item.parameters.jsCode));
}
const node = workflow.nodes.find((item) => item.name === 'Format Final Response');
const formatResponse = new Function('$input', '$node', node.parameters.jsCode);
const prepareNode = workflow.nodes.find((item) => item.name === 'Prepare Input & API Keys');
const prepareInput = new Function('$input', prepareNode.parameters.jsCode);

process.env.GEMINI_API_KEY = 'test-secret';
const prepared = prepareInput({ first: () => ({ json: { body: {
  job_description: 'Backend engineer role', resume: 'Python experience', gemini_api_key: 'attacker-key',
} } }) }).json;
assert.equal(Object.hasOwn(prepared, 'gemini_api_key'), false);
assert.equal(prepared.job_description, 'Backend engineer role');
assert.throws(() => prepareInput({ first: () => ({ json: { body: {} } }) }), /job_description and resume are required/);
delete process.env.GEMINI_API_KEY;
for (const item of workflow.nodes.filter((entry) => entry.type === 'n8n-nodes-base.httpRequest' && entry.parameters.url.includes('generativelanguage.googleapis.com'))) {
  assert.equal(item.parameters.url.includes('?key='), false);
  assert.equal(item.parameters.headerParameters.parameters.find((header) => header.name === 'x-goog-api-key').value, '={{ $env.GEMINI_API_KEY }}');
}

for (const verdict of [
  '### HIRE',
  '### NO HIRE',
  'Insufficient evidence; no recommendation is appropriate.',
]) {
  const result = formatResponse(
    { first: () => ({ json: { candidates: [{ content: { parts: [{ text: verdict }] } }] } }) },
    { 'Step 5: VerdictSynthesizer (LLM)': { input: { item: { json: { resume_evaluation: '**CANDIDATE:** Example' } } } } },
  ).json;
  assert.equal(result.decision, 'HUMAN_REVIEW_REQUIRED');
  assert.equal(result.composite_score, 'Not calculated');
  assert.equal(result.candidate_name, 'Example');
}

console.log('n8n decision formatter: all cases passed');
