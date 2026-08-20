import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const audioDir = path.join(root, 'public/audio');
const files = fs.existsSync(audioDir) ? fs.readdirSync(audioDir).filter((name) => name.endsWith('.wav')) : [];
const report = files.map((name) => {
  const buffer = fs.readFileSync(path.join(audioDir, name));
  if (buffer.toString('ascii', 0, 4) !== 'RIFF' || buffer.toString('ascii', 8, 12) !== 'WAVE') throw new Error(name + ' is not RIFF/WAVE');
  let offset = 12, sampleRate = 0, channels = 0, bitsPerSample = 0, dataBytes = 0;
  while (offset + 8 <= buffer.length) {
    const chunk = buffer.toString('ascii', offset, offset + 4);
    const size = buffer.readUInt32LE(offset + 4);
    if (chunk === 'fmt ') {
      channels = buffer.readUInt16LE(offset + 10);
      sampleRate = buffer.readUInt32LE(offset + 12);
      bitsPerSample = buffer.readUInt16LE(offset + 22);
    }
    if (chunk === 'data') dataBytes = size;
    offset += 8 + size + (size % 2);
  }
  const bytesPerFrame = Math.max(1, channels * (bitsPerSample / 8));
  return {name, sampleRate, channels, bitsPerSample, durationSeconds: dataBytes / bytesPerFrame / sampleRate};
});
const invalid = report.filter((entry) => entry.sampleRate !== 24000 || entry.channels !== 1 || entry.bitsPerSample !== 16);
fs.mkdirSync(path.join(root, 'public/data'), {recursive: true});
fs.writeFileSync(path.join(root, 'public/data/audio-qc.json'), JSON.stringify({files: report, invalid}, null, 2) + '\n');
console.log('Measured ' + report.length + ' WAV files; invalid=' + invalid.length);
if (invalid.length) process.exitCode = 1;
