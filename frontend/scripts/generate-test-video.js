/**
 * Test video generator for chart export
 * Uses node-canvas to draw frames matching the frontend lightweight-charts design
 * Then uses ffmpeg to encode into WebM video
 */

const { createCanvas } = require("@napi-rs/canvas");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

// Color constants matching the lightweight-charts design
const COLORS = {
  bg: "#07060a",
  grid: "#1a1728",
  text: "#8e8b98",
  amber: "#d97706",
  positive: "#16a34a",
  negative: "#dc2626",
};

// Quality profile (balanced)
const PROFILE = {
  width: 1280,
  height: 720,
  fps: 18,
  duration: 4000, // 4s
  padding: { top: 50, right: 100, bottom: 80, left: 80 },
  fontSize: 12,
  lineWidth: 2.5,
};

// Generate sample NAV data (simulating portfolio value over time)
function generateSampleData() {
  const data = [];
  const baseValue = 10500;
  const startTime = new Date("2024-01-01").getTime() / 1000;
  const days = 30;

  for (let i = 0; i <= days; i++) {
    const time = startTime + i * 86400;
    // Random walk with slight upward trend
    const randomChange = (Math.random() - 0.48) * 200;
    const trend = i * 15;
    const value = baseValue + randomChange + trend;
    data.push({ time, value });
  }
  return data;
}

// Generate sample P&L histogram data
function generateHistogramData(data) {
  return data.slice(1).map((point, i) => ({
    time: point.time,
    value: point.value - data[i].value,
  }));
}

function formatPrice(value) {
  return `$${value.toFixed(2)}`;
}

function formatDate(timestamp) {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function drawGrid(ctx, chartArea, minValue, maxValue) {
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;

  // Horizontal grid lines (6 lines)
  const hSteps = 6;
  for (let i = 0; i <= hSteps; i++) {
    const y = chartArea.y + (chartArea.height * i) / hSteps;
    ctx.beginPath();
    ctx.moveTo(chartArea.x, y);
    ctx.lineTo(chartArea.x + chartArea.width, y);
    ctx.stroke();
  }

  // Vertical grid lines (8 lines)
  const vSteps = 8;
  for (let i = 0; i <= vSteps; i++) {
    const x = chartArea.x + (chartArea.width * i) / vSteps;
    ctx.beginPath();
    ctx.moveTo(x, chartArea.y);
    ctx.lineTo(x, chartArea.y + chartArea.height);
    ctx.stroke();
  }
}

function drawLabels(ctx, chartArea, minValue, maxValue, points, dims) {
  ctx.font = `${dims.fontSize}px "JetBrains Mono", monospace`;
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  // Price labels (right side)
  const hSteps = 6;
  for (let i = 0; i <= hSteps; i++) {
    const value = minValue + ((maxValue - minValue) * (hSteps - i)) / hSteps;
    const y = chartArea.y + (chartArea.height * i) / hSteps;
    ctx.fillStyle = COLORS.text;
    ctx.fillText(
      formatPrice(value),
      chartArea.x + chartArea.width + dims.padding.right - 10,
      y
    );
  }

  // Time labels (bottom)
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const vSteps = Math.min(points.length - 1, 6);
  for (let i = 0; i <= vSteps; i++) {
    const pointIndex = Math.floor(((points.length - 1) * i) / vSteps);
    const point = points[pointIndex];
    const x = chartArea.x + (chartArea.width * i) / vSteps;
    ctx.fillStyle = COLORS.text;
    ctx.fillText(formatDate(point.time), x, chartArea.y + chartArea.height + 10);
  }
}

function drawAreaChart(
  ctx,
  chartArea,
  points,
  minValue,
  maxValue,
  progress,
  lineWidth
) {
  if (points.length === 0) return;

  const visiblePoints = Math.max(1, Math.floor(points.length * progress));
  const visibleData = points.slice(0, visiblePoints);

  // Create gradient for fill
  const gradient = ctx.createLinearGradient(
    0,
    chartArea.y,
    0,
    chartArea.y + chartArea.height
  );
  gradient.addColorStop(0, "rgba(217, 119, 6, 0.25)");
  gradient.addColorStop(1, "rgba(217, 119, 6, 0.02)");

  // Draw filled area
  ctx.beginPath();
  ctx.moveTo(chartArea.x, chartArea.y + chartArea.height);

  for (const point of visibleData) {
    const x =
      chartArea.x +
      ((point.time - points[0].time) /
        (points[points.length - 1].time - points[0].time)) *
        chartArea.width;
    const y =
      chartArea.y +
      chartArea.height -
      ((point.value - minValue) / (maxValue - minValue)) * chartArea.height;
    ctx.lineTo(x, y);
  }

  if (visibleData.length > 0) {
    const lastPoint = visibleData[visibleData.length - 1];
    const lastX =
      chartArea.x +
      ((lastPoint.time - points[0].time) /
        (points[points.length - 1].time - points[0].time)) *
        chartArea.width;
    ctx.lineTo(lastX, chartArea.y + chartArea.height);
  }

  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Draw line on top
  if (visibleData.length > 1) {
    ctx.beginPath();
    const first = visibleData[0];
    const firstX =
      chartArea.x +
      ((first.time - points[0].time) /
        (points[points.length - 1].time - points[0].time)) *
        chartArea.width;
    const firstY =
      chartArea.y +
      chartArea.height -
      ((first.value - minValue) / (maxValue - minValue)) * chartArea.height;
    ctx.moveTo(firstX, firstY);

    for (let i = 1; i < visibleData.length; i++) {
      const point = visibleData[i];
      const x =
        chartArea.x +
        ((point.time - points[0].time) /
          (points[points.length - 1].time - points[0].time)) *
          chartArea.width;
      const y =
        chartArea.y +
        chartArea.height -
        ((point.value - minValue) / (maxValue - minValue)) * chartArea.height;
      ctx.lineTo(x, y);
    }

    ctx.strokeStyle = COLORS.amber;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
  }
}

function drawHistogram(ctx, chartArea, histData, progress) {
  if (histData.length === 0) return;

  const visiblePoints = Math.max(1, Math.floor(histData.length * progress));
  const visibleData = histData.slice(0, visiblePoints);

  // Find max absolute value for scaling
  const maxValue = Math.max(...histData.map((p) => Math.abs(p.value)), 0.01);
  const zeroY = chartArea.y + chartArea.height / 2;

  const barWidth = (chartArea.width / histData.length) * 0.6;

  for (let i = 0; i < visibleData.length; i++) {
    const point = visibleData[i];
    const x =
      chartArea.x + (i / histData.length) * chartArea.width + barWidth * 0.3;
    const barHeight = (Math.abs(point.value) / maxValue) * (chartArea.height / 2);

    const y = point.value >= 0 ? zeroY - barHeight : zeroY;

    const color =
      point.value >= 0 ? "rgba(22, 163, 74, 0.65)" : "rgba(220, 38, 38, 0.65)";

    ctx.fillStyle = color;
    ctx.fillRect(x, y, barWidth, barHeight);
  }
}

function drawTitle(ctx, chartArea, currentNav, fontSize) {
  // Title
  ctx.font = `bold ${fontSize + 2}px "JetBrains Mono", monospace`;
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillStyle = COLORS.text;
  ctx.fillText("PORTFOLIO VALUE", chartArea.x, 15);

  // Current NAV value
  ctx.font = `bold ${fontSize + 4}px "JetBrains Mono", monospace`;
  ctx.fillStyle = COLORS.amber;
  ctx.fillText(formatPrice(currentNav), chartArea.x, 15 + fontSize + 6);

  // P&L label
  ctx.font = `${fontSize}px "JetBrains Mono", monospace`;
  ctx.fillStyle = COLORS.text;
  ctx.fillText(
    "DAILY P&L",
    chartArea.x,
    chartArea.y + chartArea.height + 35
  );
}

function drawFrame(canvas, ctx, data, histData, progress, dims) {
  // Clear and set background
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, dims.width, dims.height);

  if (data.length === 0) return;

  // Calculate value ranges
  const values = data.map((p) => p.value);
  const minValue = Math.min(...values) * 0.99;
  const maxValue = Math.max(...values) * 1.01;
  const currentNav = data[data.length - 1]?.value ?? 0;

  // Main chart area (65% of height)
  const mainChartArea = {
    x: dims.padding.left,
    y: dims.padding.top + 50,
    width: dims.width - dims.padding.left - dims.padding.right,
    height: (dims.height - dims.padding.top - dims.padding.bottom) * 0.65 - 50,
  };

  // Histogram area (35% of height)
  const histChartArea = {
    x: dims.padding.left,
    y: mainChartArea.y + mainChartArea.height + 40,
    width: mainChartArea.width,
    height: (dims.height - dims.padding.top - dims.padding.bottom) * 0.35 - 40,
  };

  // Draw main chart
  drawGrid(ctx, mainChartArea, minValue, maxValue);
  drawLabels(ctx, mainChartArea, minValue, maxValue, data, dims);
  drawAreaChart(
    ctx,
    mainChartArea,
    data,
    minValue,
    maxValue,
    progress,
    dims.lineWidth
  );
  drawTitle(ctx, mainChartArea, currentNav, dims.fontSize);

  // Draw histogram
  if (histData.length > 0) {
    drawHistogram(ctx, histChartArea, histData, progress);
  }
}

async function generateVideo() {
  console.log("Generating test chart video...");

  // Create output directory
  const outputDir = path.join(__dirname, "../test-output");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate sample data
  const data = generateSampleData();
  const histData = generateHistogramData(data);

  // Calculate total frames
  const totalFrames = Math.round((PROFILE.duration / 1000) * PROFILE.fps);
  console.log(`Generating ${totalFrames} frames at ${PROFILE.fps} fps...`);

  // Create canvas
  const canvas = createCanvas(PROFILE.width, PROFILE.height);
  const ctx = canvas.getContext("2d");

  // Generate frames
  const framesDir = path.join(outputDir, "frames");
  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  for (let i = 0; i < totalFrames; i++) {
    const progress = i / (totalFrames - 1);
    drawFrame(canvas, ctx, data, histData, progress, PROFILE);

    // Save frame as PNG
    const framePath = path.join(framesDir, `frame_${i.toString().padStart(4, "0")}.png`);
    const buffer = canvas.toBuffer("image/png");
    fs.writeFileSync(framePath, buffer);

    if (i % 10 === 0) {
      console.log(`Progress: ${((i / totalFrames) * 100).toFixed(1)}%`);
    }
  }

  console.log("Encoding video with ffmpeg...");

  // Use ffmpeg to encode frames into WebM video
  const outputVideoPath = path.join(outputDir, "chart-export-demo.webm");
  const ffmpegCmd = `ffmpeg -y -framerate ${PROFILE.fps} -i ${path.join(
    framesDir,
    "frame_%04d.png"
  )} -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 2.5M ${outputVideoPath}`;

  try {
    execSync(ffmpegCmd, { stdio: "inherit" });
    console.log(`\n✅ Video generated: ${outputVideoPath}`);
    console.log(`   Resolution: ${PROFILE.width}x${PROFILE.height}`);
    console.log(`   Duration: ${PROFILE.duration / 1000}s`);
    console.log(`   FPS: ${PROFILE.fps}`);

    // Copy to public directory for easy viewing
    const publicPath = path.join(__dirname, "../public/chart-export-demo.webm");
    fs.copyFileSync(outputVideoPath, publicPath);
    console.log(`\n📁 Also copied to: ${publicPath}`);

    // Clean up frames
    fs.rmSync(framesDir, { recursive: true, force: true });
    console.log("🧹 Cleaned up temporary frames");
  } catch (error) {
    console.error("❌ Failed to encode video:", error.message);
    process.exit(1);
  }
}

generateVideo().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
