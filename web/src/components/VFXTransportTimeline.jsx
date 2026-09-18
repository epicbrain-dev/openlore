import React, { useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  ChevronLeft,
  ChevronRight,
  Repeat,
  Film,
  Clock,
  Zap,
} from 'lucide-react';

export default function VFXTransportTimeline({
  startFrame = 1001,
  endFrame = 1150,
  currentFrame = 1042,
  onFrameChange,
  isPlaying = false,
  onTogglePlay,
  fps = 24.0,
}) {
  const keyframes = [1001, 1024, 1045, 1080, 1120, 1150];
  const timelineRef = useRef(null);

  // Playback timer (runs at target FPS)
  useEffect(() => {
    if (!isPlaying) return;
    const intervalMs = 1000 / fps;
    const timer = setInterval(() => {
      onFrameChange((prev) => {
        if (prev >= endFrame) return startFrame;
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, fps, startFrame, endFrame, onFrameChange]);

  // Keyboard navigation shortcuts: Space for Play/Pause, Left/Right for Step Frame
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input or select
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        onTogglePlay();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        onFrameChange((f) => Math.max(startFrame, f - 1));
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        onFrameChange((f) => Math.min(endFrame, f + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onTogglePlay, onFrameChange, startFrame, endFrame]);

  // Calculate SMPTE Timecode (HH:MM:SS:FF) based on frame number
  const formatTimecode = (frame) => {
    const totalFrames = Math.max(0, frame);
    const ff = totalFrames % Math.round(fps);
    const totalSeconds = Math.floor(totalFrames / Math.round(fps));
    const ss = totalSeconds % 60;
    const mm = Math.floor(totalSeconds / 60) % 60;
    const hh = Math.floor(totalSeconds / 3600);

    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(hh)}:${pad(mm)}:${pad(ss)}:${pad(ff)}`;
  };

  const handleTimelineClick = (e) => {
    if (!timelineRef.current) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const newFrame = Math.round(startFrame + ratio * (endFrame - startFrame));
    onFrameChange(newFrame);
  };

  const stepKeyframe = (direction) => {
    if (direction < 0) {
      const prevKeys = keyframes.filter((k) => k < currentFrame);
      if (prevKeys.length > 0) onFrameChange(prevKeys[prevKeys.length - 1]);
      else onFrameChange(startFrame);
    } else {
      const nextKeys = keyframes.filter((k) => k > currentFrame);
      if (nextKeys.length > 0) onFrameChange(nextKeys[0]);
      else onFrameChange(endFrame);
    }
  };

  const totalFrames = endFrame - startFrame;
  const progressRatio = Math.max(0, Math.min(1, (currentFrame - startFrame) / totalFrames));

  return (
    <div className="bg-neutral-900/95 border-t border-neutral-800 px-3 py-1.5 flex flex-col gap-1.5 shrink-0 select-none z-20 min-w-0">
      {/* Top Scrubber Track & Markers */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Start Frame Tag */}
        <span className="text-[10px] sm:text-[11px] font-mono text-neutral-400 w-8 sm:w-10 text-right shrink-0">{startFrame}</span>

        {/* Timeline Interactive Scrubber */}
        <div
          ref={timelineRef}
          onClick={handleTimelineClick}
          className="relative flex-1 h-5 sm:h-6 bg-neutral-950 border border-neutral-800 rounded cursor-pointer group flex items-center overflow-hidden min-w-0"
        >
          {/* Subtle Grid Frame Ticks every 25 frames */}
          <div className="absolute inset-0 flex justify-between px-2 pointer-events-none opacity-20">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-full border-r border-neutral-400 w-px" />
            ))}
          </div>

          {/* Cached Range Bar */}
          <div
            className="absolute left-0 top-0 bottom-0 bg-indigo-500/10 border-r border-indigo-500/30 pointer-events-none"
            style={{ width: `${progressRatio * 100}%` }}
          />

          {/* Keyframe Diamond Ticks */}
          {keyframes.map((kf) => {
            const kfRatio = (kf - startFrame) / totalFrames;
            const isCurrent = kf === currentFrame;
            return (
              <div
                key={kf}
                onClick={(e) => {
                  e.stopPropagation();
                  onFrameChange(kf);
                }}
                style={{ left: `calc(${kfRatio * 100}% - 4px)` }}
                className={`absolute w-2 h-2 rotate-45 transition-transform hover:scale-150 z-10 ${
                  isCurrent
                    ? 'bg-amber-400 shadow-md shadow-amber-400/50 scale-125'
                    : 'bg-amber-600/70 hover:bg-amber-300'
                }`}
                title={`Keyframe: ${kf}`}
              />
            );
          })}

          {/* Playhead Marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-amber-400 shadow-lg shadow-amber-400/80 z-20 pointer-events-none"
            style={{ left: `${progressRatio * 100}%` }}
          >
            <div className="absolute -top-1.5 -left-1.5 w-3.5 h-3 bg-amber-400 text-[8px] font-mono font-bold text-neutral-950 flex items-center justify-center rounded-sm">
              ▼
            </div>
          </div>
        </div>

        {/* End Frame Tag */}
        <span className="text-[10px] sm:text-[11px] font-mono text-neutral-400 w-8 sm:w-10 shrink-0">{endFrame}</span>
      </div>

      {/* Bottom Transport Controls, Current Frame, Timecode & Rates */}
      <div className="flex items-center justify-between gap-2 min-w-0">
        {/* Left: Frame & Timecode Readout */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
          <div className="flex items-center gap-1 bg-neutral-950 border border-neutral-800 px-2 py-0.5 rounded text-xs font-mono">
            <Film className="w-3 h-3 text-amber-400 shrink-0" />
            <span className="text-neutral-400 text-[10px] hidden sm:inline">FRAME:</span>
            <input
              type="number"
              value={currentFrame}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val)) onFrameChange(Math.max(startFrame, Math.min(endFrame, val)));
              }}
              className="w-12 bg-transparent text-amber-300 font-bold text-center focus:outline-none focus:bg-neutral-900 rounded text-xs"
            />
            <span className="text-neutral-500 text-[10px]">/{endFrame}</span>
          </div>

          <div className="flex items-center gap-1 bg-neutral-950 border border-neutral-800 px-2 py-0.5 rounded text-xs font-mono">
            <Clock className="w-3 h-3 text-sky-400 shrink-0" />
            <span className="text-neutral-400 text-[10px] hidden sm:inline">TC:</span>
            <span className="text-sky-300 font-semibold text-xs">{formatTimecode(currentFrame)}</span>
          </div>

          <div className="hidden xl:flex items-center gap-1 text-[10px] font-mono text-neutral-400 px-1.5 shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>24 FPS</span>
          </div>
        </div>

        {/* Center: Playback Transport Buttons */}
        <div className="flex items-center gap-0.5 sm:gap-1 bg-neutral-950 p-0.5 rounded-lg border border-neutral-800 shrink-0">
          <button
            onClick={() => onFrameChange(startFrame)}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-300 hover:text-white transition-colors cursor-pointer"
            title="First Frame [Home]"
          >
            <SkipBack className="w-3 h-3" />
          </button>

          <button
            onClick={() => stepKeyframe(-1)}
            className="px-1 py-0.5 text-[9px] font-mono rounded hover:bg-neutral-800 text-amber-400 hover:text-amber-300 transition-colors cursor-pointer hidden sm:inline"
            title="Previous Keyframe"
          >
            ◆◄
          </button>

          <button
            onClick={() => onFrameChange((f) => Math.max(startFrame, f - 1))}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-300 hover:text-white transition-colors cursor-pointer"
            title="Step Back 1 Frame [Left Arrow]"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onTogglePlay}
            className={`px-2.5 py-1 rounded flex items-center gap-1 text-xs font-mono font-bold transition-all cursor-pointer ${
              isPlaying
                ? 'bg-amber-500 text-neutral-950 shadow-md shadow-amber-500/20'
                : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-100'
            }`}
            title="Play / Pause [Spacebar]"
          >
            {isPlaying ? <Pause className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
            <span className="text-[11px]">{isPlaying ? 'PAUSE' : 'PLAY'}</span>
          </button>

          <button
            onClick={() => onFrameChange((f) => Math.min(endFrame, f + 1))}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-300 hover:text-white transition-colors cursor-pointer"
            title="Step Forward 1 Frame [Right Arrow]"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => stepKeyframe(1)}
            className="px-1 py-0.5 text-[9px] font-mono rounded hover:bg-neutral-800 text-amber-400 hover:text-amber-300 transition-colors cursor-pointer hidden sm:inline"
            title="Next Keyframe"
          >
            ►◆
          </button>

          <button
            onClick={() => onFrameChange(endFrame)}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-300 hover:text-white transition-colors cursor-pointer"
            title="Last Frame [End]"
          >
            <SkipForward className="w-3 h-3" />
          </button>
        </div>

        {/* Right: Quick Action Pill */}
        <div className="hidden 2xl:flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400">
            <Repeat className="w-3 h-3 text-emerald-400" />
            <span>Loop</span>
          </div>
          <div className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400">
            <Zap className="w-3 h-3 text-amber-400" />
            <span>6 Keys</span>
          </div>
        </div>
      </div>
    </div>
  );
}
