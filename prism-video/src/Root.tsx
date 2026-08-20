import {Composition, Folder, Still} from 'remotion';
import './index.css';
import {PrismChapter, PrismEpilogue} from './compositions/PrismChapter';
import {film, getScenesDuration, PrismFullFilm} from './compositions/PrismFullFilm';
import {PrismThumbnail} from './compositions/PrismThumbnail';

const mainScenes = film.scenes.filter((scene) => !scene.isEpilogue);
const epilogueScenes = film.scenes.filter((scene) => scene.isEpilogue);
const chapters = [...new Set(mainScenes.map((scene) => scene.chapter))];

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="PRISM-Paper-Explained-4K" component={PrismFullFilm} durationInFrames={getScenesDuration(mainScenes)} fps={30} width={3840} height={2160} />
    <Composition id="PRISM-Paper-Explained-1080p" component={PrismFullFilm} durationInFrames={getScenesDuration(mainScenes)} fps={30} width={1920} height={1080} />
    <Composition id="PRISM-Experiment-Epilogue" component={PrismEpilogue} durationInFrames={getScenesDuration(epilogueScenes)} fps={30} width={3840} height={2160} />
    <Folder name="PRISM-Chapters">
      {chapters.map((chapter) => {
        const scenes = mainScenes.filter((scene) => scene.chapter === chapter);
        return <Composition key={chapter} id={`PRISM-${chapter.replace(/[^A-Za-z0-9-]/g, '-')}`} component={PrismChapter} durationInFrames={getScenesDuration(scenes)} fps={30} width={3840} height={2160} defaultProps={{chapter}} />;
      })}
    </Folder>
    <Folder name="PRISM-Thumbnails">
      <Still id="PRISM-Thumbnail" component={PrismThumbnail} width={3840} height={2160} defaultProps={{variant: 1}} />
      <Still id="PRISM-Thumbnail-2" component={PrismThumbnail} width={3840} height={2160} defaultProps={{variant: 2}} />
      <Still id="PRISM-Thumbnail-3" component={PrismThumbnail} width={3840} height={2160} defaultProps={{variant: 3}} />
    </Folder>
  </>
);
