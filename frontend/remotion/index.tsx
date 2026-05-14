import {
  Composition,
  registerRoot,
  type CalculateMetadataFunction,
} from "remotion";
import { ChartVideo, type ChartVideoProps } from "./ChartVideo";

type ChartVideoInputProps = ChartVideoProps & {
  durationInFrames?: number;
};

const DEFAULT_DURATION_IN_FRAMES = 330;

const defaultProps: ChartVideoInputProps = {
  interval: "1M",
  points: [
    { timestamp: "2026-01-01T00:00:00+00:00", nav: 100 },
    { timestamp: "2026-01-02T00:00:00+00:00", nav: 101.25 },
    { timestamp: "2026-01-03T00:00:00+00:00", nav: 100.8 },
    { timestamp: "2026-01-04T00:00:00+00:00", nav: 103.1 },
  ],
};

const calculateMetadata: CalculateMetadataFunction<ChartVideoInputProps> = ({
  props,
}) => ({
  durationInFrames: props.durationInFrames ?? DEFAULT_DURATION_IN_FRAMES,
});

function RemotionRoot() {
  return (
    <Composition
      id="ChartVideo"
      component={ChartVideo}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={defaultProps}
      calculateMetadata={calculateMetadata}
    />
  );
}

registerRoot(RemotionRoot);
