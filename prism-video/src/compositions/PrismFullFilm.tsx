import {Series} from 'remotion';
import audioManifestRaw from '../data/audioManifest.json';
import filmRaw from '../data/film.json';
import {DocumentaryScene} from '../scenes/DocumentaryScene';
import type {AudioManifest, FilmDefinition, PrismScene} from '../types';

const film = filmRaw as FilmDefinition;
const audioManifest = audioManifestRaw as AudioManifest;

export const getSceneDuration = (scene: PrismScene, fps = 30) => {
  const measured = audioManifest.scenes[scene.id];
  if (measured) return measured.durationInFrames;
  const words = scene.spokenText.trim().split(/\s+/).length;
  return Math.ceil((words / 138) * 60 * fps) + 30;
};

export const getScenesDuration = (scenes: PrismScene[]) => scenes.reduce((sum, scene) => sum + getSceneDuration(scene, film.fps), 0);

export const PrismFullFilm: React.FC<{chapter?: string; epilogueOnly?: boolean}> = ({chapter, epilogueOnly = false}) => {
  const scenes = film.scenes.filter((scene) => {
    if (epilogueOnly) return scene.isEpilogue;
    if (chapter) return scene.chapter === chapter;
    return !scene.isEpilogue;
  });
  return (
    <Series>
      {scenes.map((scene) => {
        const measured = audioManifest.scenes[scene.id];
        const durationInFrames = getSceneDuration(scene, film.fps);
        return (
          <Series.Sequence key={scene.id} durationInFrames={durationInFrames} name={scene.title}>
            <DocumentaryScene
              scene={scene}
              audioDurationInFrames={measured ? Math.ceil(measured.durationSeconds * film.fps) : Math.max(1, durationInFrames - 30)}
              captions={measured?.captions || scene.captionCues}
            />
          </Series.Sequence>
        );
      })}
    </Series>
  );
};

export {film};

