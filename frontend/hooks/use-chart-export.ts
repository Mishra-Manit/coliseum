"use client";

import { useState, useCallback, useRef } from "react";

export type ChartExportFormat = "mp4" | "png";
export type ChartExportQuality = "fast" | "balanced" | "hq";

interface QualityProfile {
  width: number;
  height: number;
  fps: number;
  duration: number;
  videoBitsPerSecond: number;
}

const QUALITY_PROFILES: Record<ChartExportQuality, QualityProfile> = {
  fast: {
    width: 960,
    height: 540,
    fps: 12,
    duration: 3000, // 3s
    videoBitsPerSecond: 1500000,
  },
  balanced: {
    width: 1280,
    height: 720,
    fps: 18,
    duration: 4000, // 4s
    videoBitsPerSecond: 2500000,
  },
  hq: {
    width: 1920,
    height: 1080,
    fps: 24,
    duration: 5000, // 5s
    videoBitsPerSecond: 5000000,
  },
};

interface UseChartExportReturn {
  isRecording: boolean;
  progress: number;
  error: string | null;
  quality: ChartExportQuality;
  format: ChartExportFormat;
  setQuality: (quality: ChartExportQuality) => void;
  setFormat: (format: ChartExportFormat) => void;
  startRecording: (canvas: HTMLCanvasElement) => Promise<Blob>;
  stopRecording: () => void;
  downloadBlob: (blob: Blob, filename: string) => void;
  getProfile: () => QualityProfile;
  isSupported: boolean;
}

export function useChartExport(
  initialFormat: ChartExportFormat = "mp4",
  initialQuality: ChartExportQuality = "balanced",
): UseChartExportReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [quality, setQualityState] = useState<ChartExportQuality>(initialQuality);
  const [format, setFormatState] = useState<ChartExportFormat>(initialFormat);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const animationRef = useRef<number | null>(null);

  const getProfile = useCallback(() => QUALITY_PROFILES[quality], [quality]);

  const setQuality = useCallback((newQuality: ChartExportQuality) => {
    setQualityState(newQuality);
  }, []);

  const setFormat = useCallback((newFormat: ChartExportFormat) => {
    setFormatState(newFormat);
  }, []);

  const stopRecording = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      try {
        recorderRef.current.stop();
      } catch {
        // Ignore errors when stopping
      }
    }
    recorderRef.current = null;
    setIsRecording(false);
    setProgress(0);
  }, []);

  const downloadBlob = useCallback((blob: Blob, filename: string) => {
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  }, []);

  const startRecording = useCallback(
    async (canvas: HTMLCanvasElement): Promise<Blob> => {
      return new Promise((resolve, reject) => {
        setError(null);
        const profile = QUALITY_PROFILES[quality];

        // Check for MediaRecorder support
        if (!window.MediaRecorder) {
          const err = "MediaRecorder not supported in this browser";
          setError(err);
          reject(new Error(err));
          return;
        }

        // Check for canvas captureStream support
        if (!canvas.captureStream) {
          const err = "Canvas captureStream not supported in this browser";
          setError(err);
          reject(new Error(err));
          return;
        }

        chunksRef.current = [];
        setIsRecording(true);
        setProgress(0);

        try {
          const stream = canvas.captureStream(profile.fps);

          // Try VP9 first (better quality/smaller size), fall back to VP8
          const mimeTypes = [
            "video/webm;codecs=vp9",
            "video/webm;codecs=vp8",
            "video/webm",
          ];
          let selectedMimeType = "";
          for (const mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
              selectedMimeType = mimeType;
              break;
            }
          }

          if (!selectedMimeType) {
            const err = "No supported video MIME type found";
            setError(err);
            setIsRecording(false);
            reject(new Error(err));
            return;
          }

          const recorder = new MediaRecorder(stream, {
            mimeType: selectedMimeType,
            videoBitsPerSecond: profile.videoBitsPerSecond,
          });

          recorderRef.current = recorder;

          recorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
              chunksRef.current.push(e.data);
            }
          };

          recorder.onstop = () => {
            const blob = new Blob(chunksRef.current, {
              type: selectedMimeType,
            });
            resolve(blob);
          };

          recorder.onerror = (e) => {
            const err = `Recording error: ${e}`;
            setError(err);
            setIsRecording(false);
            reject(new Error(err));
          };

          // Start recording
          recorder.start(100); // Collect data every 100ms

          // Animate progress
          const startTime = performance.now();
          const animateProgress = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const newProgress = Math.min((elapsed / profile.duration) * 100, 100);
            setProgress(newProgress);

            if (elapsed < profile.duration) {
              animationRef.current = requestAnimationFrame(animateProgress);
            } else {
              // Stop recording after duration
              if (recorder.state !== "inactive") {
                recorder.stop();
              }
              setIsRecording(false);
              setProgress(100);
            }
          };

          animationRef.current = requestAnimationFrame(animateProgress);

          // Safety timeout
          setTimeout(() => {
            if (recorder.state !== "inactive") {
              recorder.stop();
            }
          }, profile.duration + 500);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : "Unknown error";
          setError(errorMsg);
          setIsRecording(false);
          reject(new Error(errorMsg));
        }
      });
    },
    [quality],
  );

  // Check browser support
  const isSupported =
    typeof window !== "undefined" &&
    !!window.MediaRecorder &&
    !!HTMLCanvasElement.prototype.captureStream;

  return {
    isRecording,
    progress,
    error,
    quality,
    format,
    setQuality,
    setFormat,
    startRecording,
    stopRecording,
    downloadBlob,
    getProfile,
    isSupported,
  };
}
