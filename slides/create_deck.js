const path = require('path');
const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Final Project - Agent-Based Programming';
pptx.subject = 'Multi-agent system for resume and job analysis';
pptx.title = 'Multi-Agent Resume Analysis System';
pptx.company = 'UFPB';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};
pptx.defineLayout({ name: 'CUSTOM_WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'CUSTOM_WIDE';
pptx.margin = 0;
pptx.slideWidth = 13.333;
pptx.slideHeight = 7.5;
pptx.defineSlideMaster({
  title: 'BASE',
  background: { color: 'F7FAFC' },
  objects: [
    { line: { x: 0.55, y: 7.08, w: 12.2, h: 0, line: { color: 'CBD5E1', width: 0.7 } } },
    { text: { text: 'Final Project • Agent-Based Programming', options: { x: 0.7, y: 7.12, w: 4.5, h: 0.2, fontSize: 7, color: '64748B' } } },
  ],
  slideNumber: { x: 12.35, y: 7.08, color: '64748B', fontSize: 8 },
});

const C = {
  bg: 'F7FAFC',
  ink: '0F172A',
  muted: '475569',
  subtle: 'E2E8F0',
  white: 'FFFFFF',
  blue: '2563EB',
  teal: '0F766E',
  green: '16A34A',
  orange: 'EA580C',
  purple: '7C3AED',
  red: 'DC2626',
  slate: '334155',
};

function addTitle(slide, title, subtitle) {
  slide.addText(title, { x: 0.65, y: 0.42, w: 11.9, h: 0.45, fontFace: 'Aptos Display', fontSize: 27, bold: true, color: C.ink, margin: 0 });
  if (subtitle) slide.addText(subtitle, { x: 0.68, y: 0.95, w: 10.9, h: 0.28, fontSize: 11, color: C.muted, margin: 0 });
}

function pill(slide, text, x, y, w, color) {
  slide.addText(text, { x, y, w, h: 0.35, fontSize: 10, bold: true, align: 'center', valign: 'mid', color: color, fill: { color: 'FFFFFF' }, line: { color, width: 1 }, radius: 0.16, margin: 0.03 });
}

function box(slide, text, x, y, w, h, color, opts = {}) {
  slide.addText(text, { x, y, w, h, fontSize: opts.fontSize || 14, bold: opts.bold || false, color: opts.color || C.ink, valign: 'mid', align: opts.align || 'center', fill: { color: opts.fill || 'FFFFFF' }, line: { color: color || C.subtle, width: opts.lineWidth || 1.2 }, radius: 0.16, margin: opts.margin || 0.08, breakLine: false, fit: 'shrink' });
}

function arrow(slide, x1, y1, x2, y2, color = C.slate) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width: 1.6, beginArrowType: 'none', endArrowType: 'triangle' } });
}

function validate() {
  // Layout validation is performed during project development.
}

// Slide 1
{
  const s = pptx.addSlide('BASE');
  s.background = { color: 'F7FAFC' };
  pill(s, 'FINAL PROJECT', 0.75, 1.1, 1.55, C.teal);
  s.addText('Multi-agent system\nfor resume and job analysis', { x: 0.75, y: 1.65, w: 6.85, h: 1.4, fontFace: 'Aptos Display', fontSize: 33, bold: true, color: C.ink, margin: 0, breakLine: false, fit: 'shrink' });
  s.addText('A Python implementation that divides the analysis among specialized agents: resume, job, matching, recommendation, and review.', { x: 0.78, y: 3.35, w: 6.45, h: 0.72, fontSize: 15, color: C.muted, margin: 0, breakLine: false, fit: 'shrink' });
  box(s, 'Resume', 8.25, 1.35, 1.75, 0.78, C.blue, { fill: 'EFF6FF', bold: true });
  box(s, 'Job', 10.55, 1.35, 1.5, 0.78, C.purple, { fill: 'F5F3FF', bold: true });
  arrow(s, 10.02, 1.74, 10.48, 1.74, C.slate);
  box(s, '🤖\nCooperating agents', 8.95, 3.0, 2.3, 1.05, C.teal, { fill: 'ECFDF5', bold: true, fontSize: 15 });
  arrow(s, 9.35, 2.18, 9.7, 2.95, C.slate);
  arrow(s, 11.1, 2.18, 10.55, 2.95, C.slate);
  box(s, 'Compatibility + recommendations', 8.45, 5.0, 3.35, 0.92, C.green, { fill: 'F0FDF4', bold: true });
  arrow(s, 10.1, 4.08, 10.1, 4.9, C.slate);
  validate(s);
}

// Slide 2
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Problem', 'Resumes and job descriptions contain scattered information; manual analysis is slow and subjective.');
  s.addText('Before', { x: 0.8, y: 1.55, w: 1.2, h: 0.3, fontSize: 14, bold: true, color: C.red, margin: 0 });
  box(s, 'Job description\nwith mixed requirements', 0.85, 2.05, 2.7, 1.0, C.red, { fill: 'FEF2F2', bold: true });
  box(s, 'Resume\nwith scattered experience', 0.85, 3.45, 2.7, 1.0, C.orange, { fill: 'FFF7ED', bold: true });
  s.addText('→ difficult to identify missing skills\n→ risk of poorly targeted applications\n→ limited explanation of the result', { x: 4.1, y: 2.25, w: 3.2, h: 1.9, fontSize: 18, color: C.ink, breakLine: false, fit: 'shrink' });
  s.addText('After', { x: 8.25, y: 1.55, w: 1.35, h: 0.3, fontSize: 14, bold: true, color: C.green, margin: 0 });
  box(s, 'Analysis divided\namong agents', 8.05, 2.05, 2.4, 0.95, C.teal, { fill: 'ECFDF5', bold: true });
  box(s, 'Explained result\nwith next steps', 9.45, 3.62, 2.65, 0.95, C.green, { fill: 'F0FDF4', bold: true });
  arrow(s, 9.2, 3.03, 10.45, 3.55, C.slate);
  s.addShape(pptx.ShapeType.line, { x: 7.55, y: 1.55, w: 0, h: 4.6, line: { color: 'CBD5E1', width: 1 } });
  validate(s);
}

// Slide 3
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Solution idea', 'Each agent solves a small part and passes its result to the next agent.');
  const nodes = [
    ['Resume', 'extracts skills\nand experience', 0.8, 2.0, C.blue, 'EFF6FF'],
    ['Job', 'classifies requirements\nand preferences', 3.25, 2.0, C.purple, 'F5F3FF'],
    ['Matcher', 'calculates score\nand skill gaps', 5.7, 2.0, C.teal, 'ECFDF5'],
    ['Advisor', 'suggests practical\nactions', 8.15, 2.0, C.orange, 'FFF7ED'],
    ['Reviewer', 'consolidates the\nfinal response', 10.6, 2.0, C.green, 'F0FDF4'],
  ];
  for (let i = 0; i < nodes.length - 1; i++) arrow(s, nodes[i][2] + 1.9, 2.55, nodes[i+1][2] - 0.08, 2.55, C.slate);
  nodes.forEach(([title, desc, x, y, color, fill]) => {
    box(s, title + '\n' + desc, x, y, 1.95, 1.12, color, { fill, bold: true, fontSize: 12 });
  });
  s.addText("The main advantage is traceability: during the demonstration, each agent's result can be inspected and the decision path can be explained.", { x: 1.25, y: 4.4, w: 10.8, h: 0.78, fontSize: 20, bold: true, color: C.ink, align: 'center', breakLine: false, fit: 'shrink' });
  validate(s);
}

// Slide 4
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Architecture', 'A simple sequential flow designed to demonstrate agent-based programming.');
  // connectors first
  arrow(s, 2.2, 2.15, 4.05, 2.15, C.slate);
  arrow(s, 2.2, 4.2, 4.05, 4.2, C.slate);
  arrow(s, 6.0, 2.15, 7.35, 3.12, C.slate);
  arrow(s, 6.0, 4.2, 7.35, 3.3, C.slate);
  arrow(s, 9.55, 3.2, 10.65, 3.2, C.slate);
  arrow(s, 11.9, 3.2, 12.35, 3.2, C.slate);

  box(s, 'Input:\nResume', 0.8, 1.65, 1.4, 1.0, C.blue, { fill: 'EFF6FF', bold: true });
  box(s, 'Input:\nJob', 0.8, 3.7, 1.4, 1.0, C.purple, { fill: 'F5F3FF', bold: true });
  box(s, 'Resume\nAgent', 4.1, 1.65, 1.9, 1.0, C.blue, { fill: 'EFF6FF', bold: true });
  box(s, 'Job\nAgent', 4.1, 3.7, 1.9, 1.0, C.purple, { fill: 'F5F3FF', bold: true });
  box(s, 'Matching\nAgent', 7.45, 2.68, 2.0, 1.05, C.teal, { fill: 'ECFDF5', bold: true });
  box(s, 'Advisor', 10.68, 2.78, 1.2, 0.82, C.orange, { fill: 'FFF7ED', bold: true, fontSize: 12 });
  box(s, 'Reviewer', 12.37, 2.78, 0.8, 0.82, C.green, { fill: 'F0FDF4', bold: true, fontSize: 11 });
  s.addText('Output: compatibility, matched skills, missing skills, and recommendations.', { x: 3.25, y: 5.58, w: 6.85, h: 0.5, fontSize: 18, bold: true, color: C.ink, align: 'center', margin: 0, fit: 'shrink' });
  validate(s);
}

// Slide 5
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Implementation', 'A Python project with a simple web interface for a classroom demonstration.');
  s.addText('Technologies', { x: 0.85, y: 1.7, w: 2.0, h: 0.4, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  box(s, 'Python', 0.9, 2.35, 1.35, 0.58, C.blue, { fill: 'EFF6FF', bold: true });
  box(s, 'Streamlit', 2.55, 2.35, 1.65, 0.58, C.teal, { fill: 'ECFDF5', bold: true });
  box(s, 'pandas', 4.55, 2.35, 1.25, 0.58, C.purple, { fill: 'F5F3FF', bold: true });
  box(s, 'pdfplumber', 6.12, 2.35, 1.62, 0.58, C.orange, { fill: 'FFF7ED', bold: true });
  s.addText('Project structure', { x: 0.85, y: 3.65, w: 2.8, h: 0.35, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  s.addText('app.py\npipeline.py\nagents/\nutils/\nexamples/\ndocs/', { x: 0.95, y: 4.15, w: 2.35, h: 1.55, fontFace: 'Courier New', fontSize: 16, color: C.slate, margin: 0.08, fill: { color: 'FFFFFF' }, line: { color: C.subtle } });
  s.addText('The code is organized so that each agent has a clear responsibility. This makes the project easier to explain and extend.', { x: 4.15, y: 4.25, w: 6.9, h: 1.0, fontSize: 20, bold: true, color: C.ink, breakLine: false, fit: 'shrink' });
  validate(s);
}

// Slide 6
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Demonstration', 'The application accepts pasted text or files and displays the complete agent execution trace.');
  box(s, '1\nPaste resume', 0.9, 2.0, 1.9, 1.0, C.blue, { fill: 'EFF6FF', bold: true });
  box(s, '2\nPaste job', 3.4, 2.0, 1.9, 1.0, C.purple, { fill: 'F5F3FF', bold: true });
  box(s, '3\nRun agents', 5.9, 2.0, 2.05, 1.0, C.teal, { fill: 'ECFDF5', bold: true });
  box(s, '4\nReview result', 8.55, 2.0, 1.9, 1.0, C.green, { fill: 'F0FDF4', bold: true });
  arrow(s, 2.83, 2.5, 3.32, 2.5, C.slate);
  arrow(s, 5.33, 2.5, 5.82, 2.5, C.slate);
  arrow(s, 7.98, 2.5, 8.48, 2.5, C.slate);
  s.addText('During the presentation, use the files in the examples/ directory to avoid typing errors and show the complete result quickly.', { x: 1.15, y: 4.35, w: 10.5, h: 0.7, fontSize: 20, bold: true, color: C.ink, align: 'center', breakLine: false, fit: 'shrink' });
  validate(s);
}

// Slide 7
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Expected result', 'The output combines a score, an explanation, and recommendations.');
  s.addShape(pptx.ShapeType.arc, { x: 0.95, y: 1.75, w: 2.5, h: 2.5, adjustPoint: 0.42, line: { color: C.green, width: 4 }, fill: { color: 'F0FDF4', transparency: 20 } });
  s.addText('88%', { x: 1.28, y: 2.45, w: 1.85, h: 0.6, fontSize: 34, bold: true, color: C.green, align: 'center', margin: 0 });
  s.addText('Sample\ncompatibility', { x: 1.35, y: 3.05, w: 1.7, h: 0.4, fontSize: 11, color: C.muted, align: 'center', margin: 0, fit: 'shrink' });
  box(s, 'Matched\nPython • SQL • Git • ML', 4.25, 1.85, 3.0, 1.0, C.green, { fill: 'F0FDF4', bold: true });
  box(s, 'Missing\nAPI • AWS • Teamwork', 8.2, 1.85, 2.7, 1.0, C.orange, { fill: 'FFF7ED', bold: true });
  box(s, 'Recommendation\nHighlight projects and address key skill gaps', 4.85, 4.15, 5.6, 0.9, C.teal, { fill: 'ECFDF5', bold: true, fontSize: 13 });
  arrow(s, 7.2, 2.35, 8.12, 2.35, C.slate);
  arrow(s, 7.55, 2.92, 7.55, 4.05, C.slate);
  validate(s);
}

// Slide 8
{
  const s = pptx.addSlide('BASE');
  addTitle(s, 'Conclusion', 'The multi-agent architecture makes the system explainable and easy to extend.');
  box(s, 'Current delivery\n• functional code\n• Streamlit interface\n• examples\n• documentation\n• slides', 0.9, 1.75, 3.0, 2.65, C.blue, { fill: 'EFF6FF', bold: true, align: 'left', fontSize: 15, margin: 0.12 });
  box(s, 'Limitations\n• uses keywords\n• depends on text quality\n• does not replace human review', 5.05, 1.75, 3.1, 2.65, C.orange, { fill: 'FFF7ED', bold: true, align: 'left', fontSize: 15, margin: 0.12 });
  box(s, 'Next steps\n• embeddings\n• language model\n• platform integration\n• automatic resume tailoring', 9.25, 1.75, 3.15, 2.65, C.green, { fill: 'F0FDF4', bold: true, align: 'left', fontSize: 14, margin: 0.12 });
  s.addText('Final message: the system does not try to solve everything as a black box; it organizes the problem into specialized agents and shows the decision path.', { x: 1.15, y: 5.35, w: 11.0, h: 0.6, fontSize: 18, bold: true, color: C.ink, align: 'center', breakLine: false, fit: 'shrink' });
  validate(s);
}

const outputPath = path.resolve(__dirname, '..', 'Multi_Agent_Resume_Analysis_Presentation.pptx');
pptx.writeFile({ fileName: outputPath });
