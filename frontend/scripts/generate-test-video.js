/**
 * Test video generator for chart export
 * Uses @napi-rs/canvas to draw frames matching the frontend lightweight-charts design
 * Then uses ffmpeg to encode into high-quality WebM video
 * 
 * This generates realistic portfolio data matching the Coliseum ChartDataPoint schema
 * and uses HQ settings (1920x1080 @ 30fps) for smooth, professional output.
 */

const { createCanvas } = require("canvas");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

// Color constants matching the lightweight-charts design exactly
const COLORS = {
  bg: "#07060a",
  grid: "#1a1728",
  text: "#8e8b98",
  amber: "#d97706",
  positive: "#16a34a",
  negative: "#dc2626",
};

// HQ Quality profile (1920x1080 @ 30fps, 6s duration)
const PROFILE = {
  width: 1920,
  height: 1080,
  fps: 30,
  duration: 6000, // 6 seconds for smoother animation
  padding: { top: 60, right: 120, bottom: 100, left: 100 },
  fontSize: 14,
  lineWidth: 3,
};

/**
 * Generate realistic portfolio NAV data matching Coliseum's ChartDataPoint schema
 * Format: { timestamp: ISO string, nav: number, cash: number, positions_value: number }
 * 
 * Simulates 45 days of trading with:
 * - Intraday snapshots every 4 hours (trading hours focus)
 * - Realistic market volatility and position updates
 * - Slight upward drift from winning strategy
 * - Floor protection to prevent unrealistic crashes
 */
function generateRealisticData() {
  const data = [];
  const baseValue = 10000; // Starting portfolio NAV
  
  const startDate = new Date("2024-01-01T00:00:00Z");
  const days = 45; // 1.5 months of data
  
  let currentValue = baseValue;
  
  for (let i = 0; i <= days; i++) {
    // Multiple snapshots per day (every 4 hours during trading day)
    for (let hour of [0, 4, 8, 12, 16, 20]) {
      const timestamp = new Date(startDate);
      timestamp.setDate(startDate.getDate() + i);
      timestamp.setHours(hour, 0, 0, 0);
      
      // Realistic portfolio movements:
      // - Small intraday drift (market noise)
      // - Occasional larger moves from position updates (every 3 days)
      // - Slight daily upward bias (winning strategy)
      const intradayDrift = (Math.random() - 0.47) * 50;
      
      // Larger moves every few days (position entry/exit updates)
      const positionMove = (i % 3 === 0 && hour === 16) 
        ? (Math.random() - 0.4) * 300 
        : 0;
      
      // Small consistent daily trend
      const dailyTrend = i * 12;
      
      currentValue = baseValue + dailyTrend + intradayDrift + positionMove;
      currentValue = Math.max(currentValue, 9500); // Floor protection at 95%
      
      // Add micro-noise for realism
      currentValue += (Math.random() - 0.5) * 20;
      
      data.push({ 
        timestamp: timestamp.toISOString(),
        nav: Math.round(currentValue * 100) / 100,
        cash: Math.round(currentValue * 0.3 * 100) / 100,
        positions_value: Math.round(currentValue * 0.7 * 100) / 100
      });
    }
  }
  
  return data;
}

// Parse ISO timestamp to milliseconds (matches chart-utils.ts)
function parseTimestamp(iso) {
  return new Date(iso).getTime();
}

// Bucketize by day (matches getBucketMs in chart-utils.ts)
function getBucketMs(timestampMs) {
  const DAY_MS = 24 * 60 * 60 * 1000;
  return Math.floor(timestampMs / DAY_MS) * DAY_MS;
}

/**
 * Bucketize data for chart display (matches getChartSeries in chart-utils.ts)
 * Groups by day, keeping first and last NAV per day
 */
function bucketizeData(data) {
  const buckets = new Map();
  
  for (const point of data) {
    const timestampMs = parseTimestamp(point.timestamp);
    const bucketMs = getBucketMs(timestampMs);
    const time = Math.floor(bucketMs / 1000);
    
    if (!buckets.has(time)) {
      buckets.set(time, {
        time,
        firstNav: point.nav,
        lastNav: point.nav
      });
    } else {
      const bucket = buckets.get(time);
      // Update last NAV - this gives us closing value per day
      bucket.lastNav = point.nav;
    }
  }
  
  return Array.from(buckets.values()).sort((a, b) => a.time - b.time);
}

/**
 * Generate daily P&L histogram data from bucketized series
 * P&L = current day close - previous day close
 */
function generateHistogramData(bucketized) {
  return bucketized.map((bucket, i) => {
    if (i === 0) return { time: bucket.time, value: 0 };
    const prev = bucketized[i - 1];
    return {
      time: bucket.time,
      value: Math.round((bucket.lastNav - prev.lastNav) * 100) / 100
    };
  });
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

  // Create gradient for fill (amber with fade)
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

  // Current NAV value (amber)
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
  console.log("🎬 Generating HQ test chart video...");
  console.log(`   Quality: ${PROFILE.width}x${PROFILE.height} @ ${PROFILE.fps}fps`);
  console.log(`   Duration: ${PROFILE.duration / 1000}s`);
  
  // Create output directory
  const outputDir = path.join(__dirname, "../test-output");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate realistic data matching Coliseum schema
  console.log("\n📊 Generating realistic portfolio data...");
  const rawData = generateRealisticData();
  const bucketized = bucketizeData(rawData);
  
  // Convert to area series format (daily closing NAV values)
  const data = bucketized.map(b => ({ time: b.time, value: b.lastNav }));
  
  // Generate daily P&L histogram
  const histData = generateHistogramData(bucketized);
  
  console.log(`   Generated ${data.length} days of NAV data`);
  console.log(`   Date range: ${formatDate(data[0].time)} - ${formatDate(data[data.length - 1].time)}`);
  console.log(`   NAV range: $${Math.min(...data.map(d => d.value)).toFixed(2)} - $${Math.max(...data.map(d => d.value)).toFixed(2)}`);

  // Calculate total frames
  const totalFrames = Math.round((PROFILE.duration / 1000) * PROFILE.fps);
  console.log(`\n🎞️  Generating ${totalFrames} frames...`);

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

    if (i % 30 === 0) {
      console.log(`   ${((i / totalFrames) * 100).toFixed(0)}%`);
    }
  }

  console.log("\n🎥 Encoding video with ffmpeg...");

  // Use ffmpeg to encode frames into high-quality WebM video
  const outputVideoPath = path.join(outputDir, "chart-export-demo.webm");
  
  // Higher bitrate for HQ
  const videoBitrate = "5M";
  
  const ffmpegCmd = `ffmpeg -y -framerate ${PROFILE.fps} -i ${path.join(
    framesDir,
    "frame_%04d.png"
  )} -c:v libvpx-vp9 -pix_fmt yuva420p -b:v ${videoBitrate} -quality good -speed 0 ${outputVideoPath}`;

  try {
    execSync(ffmpegCmd, { stdio: "inherit" });
    
    const stats = fs.statSync(outputVideoPath);
    
    console.log(`\n✅ Video generated successfully!`);
    console.log(`   File: ${outputVideoPath}`);
    console.log(`   Size: ${(stats.size / 1024).toFixed(1)} KB`);
    console.log(`   Resolution: ${PROFILE.width}x${PROFILE.height}`);
    console.log(`   Duration: ${PROFILE.duration / 1000}s`);
    console.log(`   FPS: ${PROFILE.fps}`);
    console.log(`   Bitrate: ${videoBitrate}`);

    // Copy to public directory
    const publicPath = path.join(__dirname, "../public/chart-export-demo.webm");
    fs.copyFileSync(outputVideoPath, publicPath);
    console.log(`\n📁 Copied to: ${publicPath}`);

    // Clean up frames
    fs.rmSync(framesDir, { recursive: true, force: true });
    console.log("🧹 Cleaned up temporary frames");
  } catch (error) {
    console.error("\n❌ Failed to encode video:", error.message);
    process.exit(1);
  }
}

generateVideo().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
