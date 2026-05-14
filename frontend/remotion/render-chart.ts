import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import type { ChartVideoProps } from "./ChartVideo";

type RenderInputProps = ChartVideoProps & {
  durationInFrames?: number;
};

type RenderArgs = {
  propsPath: string;
  outputPath: string;
};

const COMPOSITION_ID = "ChartVideo";

function readArgValue(args: string[], name: string): string | null {
  const inline = args.find((arg) => arg.startsWith(`${name}=`));
  if (inline) return inline.slice(name.length + 1);

  const index = args.indexOf(name);
  if (index === -1) return null;
  return args[index + 1] ?? null;
}

function parseArgs(args: string[]): RenderArgs {
  const propsPath = readArgValue(args, "--props");
  const outputPath = readArgValue(args, "--output");

  if (!propsPath || !outputPath) {
    throw new Error(
      "Usage: npm run render:chart-video -- --props <props.json> --output <chart.mp4>",
    );
  }

  return {
    propsPath: path.resolve(propsPath),
    outputPath: path.resolve(outputPath),
  };
}

function loadProps(propsPath: string): RenderInputProps {
  if (!existsSync(propsPath)) {
    throw new Error(`Props file does not exist: ${propsPath}`);
  }

  const parsed = JSON.parse(readFileSync(propsPath, "utf-8")) as RenderInputProps;
  if (!Array.isArray(parsed.points)) {
    throw new Error("Props file must include a points array");
  }
  if (!["1D", "1W", "1M", "ALL"].includes(parsed.interval)) {
    throw new Error("Props file must include a valid interval");
  }

  return parsed;
}

async function main() {
  const { propsPath, outputPath } = parseArgs(process.argv.slice(2));
  const inputProps = loadProps(propsPath);
  const entryPoint = path.resolve(process.cwd(), "remotion", "index.tsx");

  console.error(`[chart-render] bundling ${entryPoint}`);
  const serveUrl = await bundle({
    entryPoint,
    rootDir: process.cwd(),
    enableCaching: true,
    onProgress: (progress) => {
      console.error(`[chart-render] bundle ${Math.round(progress)}%`);
    },
  });

  const composition = await selectComposition({
    serveUrl,
    id: COMPOSITION_ID,
    inputProps,
    logLevel: "warn",
  });

  console.error(
    `[chart-render] rendering ${composition.width}x${composition.height} ${composition.durationInFrames}f`,
  );
  await renderMedia({
    composition,
    serveUrl,
    codec: "h264",
    outputLocation: outputPath,
    inputProps,
    logLevel: "warn",
  });

  console.error(`[chart-render] wrote ${outputPath}`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.stack || error.message : String(error);
  console.error(`[chart-render] failed\n${message}`);
  process.exitCode = 1;
});
