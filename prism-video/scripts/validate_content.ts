import fs from 'node:fs';
import path from 'node:path';

type Scene = Record<string, unknown> & {
  id: string; chapterTitle: string; spokenText: string; source: string;
  graphId?: string; graphSource?: Record<string, unknown>; isEpilogue?: boolean;
  paperFigures?: number[]; paperTables?: number[]; algorithms?: number[];
};

const root = process.cwd();
const film = JSON.parse(fs.readFileSync(path.join(root, 'src/data/film.json'), 'utf8')) as {scenes: Scene[]};
const graphs = JSON.parse(fs.readFileSync(path.join(root, 'src/data/graphExtracts.json'), 'utf8')) as Record<string, unknown>;
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'src/data/audioManifest.json'), 'utf8')) as {scenes: Record<string, {durationSeconds: number}>};
const required = ['id', 'chapter', 'chapterTitle', 'title', 'audio', 'spokenText', 'captionCues', 'finding', 'limitation', 'downstreamDecision', 'claimStatus', 'source', 'sampleSize', 'caveat', 'altDescription'];
const errors: string[] = [];

for (const scene of film.scenes) {
  for (const field of required) {
    if (!(field in scene) || scene[field] === '') errors.push(scene.id + ': missing ' + field);
  }
  if (scene.graphId && !scene.graphSource) errors.push(scene.id + ': graph has no source');
  if (scene.graphId && !graphs[scene.graphId]) errors.push(scene.id + ': missing graph extract ' + scene.graphId);
  if (scene.isEpilogue && scene.source !== 'Post-paper research update') errors.push(scene.id + ': epilogue boundary missing');
}

for (const letter of 'ABCDEFGHIJKLMNOPQR') {
  const found = film.scenes.some((scene) =>
    scene.chapterTitle.includes('Experiment ' + letter) ||
    scene.chapterTitle.includes('Experiments ' + letter) ||
    (['B', 'C', 'D'].includes(letter) && scene.chapterTitle.includes('Experiments B, C, and D'))
  );
  if (!found) errors.push('Experiment ' + letter + ' is absent');
}

const figures = new Set(film.scenes.flatMap((scene) => scene.paperFigures ?? []));
const tables = new Set(film.scenes.flatMap((scene) => scene.paperTables ?? []));
const algorithms = new Set(film.scenes.flatMap((scene) => scene.algorithms ?? []));
for (let i = 1; i <= 12; i++) if (!figures.has(i)) errors.push('Paper Figure ' + i + ' absent');
for (let i = 1; i <= 8; i++) if (!tables.has(i)) errors.push('Paper Table ' + i + ' absent');
for (let i = 1; i <= 3; i++) if (!algorithms.has(i)) errors.push('Paper Algorithm ' + i + ' absent');

const duration = (scenes: Scene[]) => scenes.reduce((sum, scene) => sum + (manifest.scenes[scene.id]?.durationSeconds ?? (scene.spokenText.split(/\s+/).length / 137) * 60), 0) / 60;
const mainMinutes = duration(film.scenes.filter((scene) => !scene.isEpilogue));
const epilogueMinutes = duration(film.scenes.filter((scene) => scene.isEpilogue));
if (mainMinutes < 90 || mainMinutes > 120) errors.push('Main duration outside 90–120: ' + mainMinutes.toFixed(1));
if (epilogueMinutes < 15 || epilogueMinutes > 25) errors.push('Epilogue duration outside 15–25: ' + epilogueMinutes.toFixed(1));

const report = {
  generatedAt: new Date().toISOString(), passed: errors.length === 0,
  sceneCount: film.scenes.length, mainMinutes, epilogueMinutes,
  graphCount: Object.keys(graphs).length,
  figures: [...figures].sort((a, b) => a - b),
  tables: [...tables].sort((a, b) => a - b),
  algorithms: [...algorithms].sort((a, b) => a - b), errors,
};
fs.mkdirSync(path.join(root, 'public/data'), {recursive: true});
fs.writeFileSync(path.join(root, 'public/data/content-audit.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
if (errors.length) process.exitCode = 1;
