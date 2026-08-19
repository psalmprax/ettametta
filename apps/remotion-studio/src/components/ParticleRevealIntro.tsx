import React, { useEffect, useRef, useState, useMemo } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

// ─────────────────────────────────────────────────────────────────────────────
// GPU Shader (full quality - particles, chromatic aberration, bend, drift)
// ─────────────────────────────────────────────────────────────────────────────
const VERT = `#version 300 es
precision highp float;
layout(location = 0) in vec2 aPos;
out vec2 vUv;
void main () {
  vUv = aPos * 0.5 + 0.5;
  gl_Position = vec4(aPos, 0.0, 1.0);
}`;

const FRAG_GPU = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 outColor;
uniform sampler2D uContent;
uniform vec2 uRes;
uniform float uDpr;
uniform vec2 uPointer;
uniform float uActive;
uniform float uRadius;
uniform float uSoftness;
uniform float uSize;
uniform float uScatter;
uniform float uDrift;
uniform float uAberration;
uniform float uBend;
uniform float uFade;
uniform float uThreshold;
uniform vec3 uBg;
uniform float uTime;
uniform float uMaxX;
uniform float uCrisp;

float hash (vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec4 samp (vec2 p) {
  vec2 uv = p / uRes;
  uv = clamp(uv, vec2(0.001), vec2(uMaxX - 0.001, 0.999));
  return texture(uContent, uv);
}

void main () {
  vec2 pc = vec2(vUv.x, 1.0 - vUv.y) * uRes;
  if (pc.x > uMaxX * uRes.x) {
    outColor = vec4(0.0);
    return;
  }
  if (uCrisp > 0.5) {
    outColor = samp(pc);
    return;
  }

  float dist = length(pc - uPointer);
  float radius = max(uRadius, 1.0);
  float inner = radius * (1.0 - clamp(uSoftness, 0.02, 1.0));
  float e = (1.0 - smoothstep(inner, radius, dist)) * uActive;

  float band = radius * 0.9;
  float ring = smoothstep(inner, radius, dist)
    * (1.0 - smoothstep(radius, radius + band, dist))
    * uActive;

  vec2 dir = (pc - uPointer) / max(dist, 1e-3);
  vec2 tang = vec2(-dir.y, dir.x);
  vec2 warp = (dir * -1.0 + tang * 0.6) * uBend * ring;
  float ca = uAberration * ring;

  float cellPx = max(uSize, 0.5) * uDpr;
  vec2 cell = floor(gl_FragCoord.xy / cellPx);
  float n1 = hash(cell);
  float n2 = hash(cell + vec2(3.1, 7.7));
  float n3 = hash(cell + vec2(9.3, 1.3));
  float ft = floor(uTime * (2.0 + uDrift * 6.0));
  float n4 = hash(cell + vec2(ft * 0.613, ft * 0.831));

  float g0 = uThreshold * 0.6;
  float g1 = uThreshold * 1.6 + 0.01;
  vec3 lw = vec3(0.299, 0.587, 0.114);

  vec2 bp = pc + warp;
  vec4 bR = samp(bp + dir * ca);
  vec4 bC = samp(bp);
  vec4 bB = samp(bp - dir * ca);
  vec3 baseRgb = vec3(bR.r, bC.g, bB.b);
  float uiHome = smoothstep(g0, g1, dot(abs(baseRgb - uBg), lw));

  float rad = uScatter * pow(n1, 2.5) * (1.0 - e);
  float ang = n2 * 6.2832 + uTime * uDrift * (0.5 + n3 * 1.5);
  vec2 dustP = bp + vec2(cos(ang), sin(ang)) * rad;

  vec4 dR = samp(dustP + dir * ca);
  vec4 dC = samp(dustP);
  vec4 dB = samp(dustP - dir * ca);
  vec3 dustRgb = vec3(dR.r, dC.g, dB.b);
  float lumD = dot(dustRgb, lw);
  float dDust = dot(abs(dustRgb - uBg), lw);

  float gate = smoothstep(g0, g1, dDust);
  float falloff = 1.0 - 0.7 * rad / max(uScatter, 1.0);
  float prob = clamp(gate * (0.15 + 1.2 * sqrt(dDust)) * falloff, 0.0, 1.0) * uiHome;
  float speck = step(n4 * 0.999, prob);

  float shade = pow(lumD, 0.4) * (0.8 + 0.4 * n3);
  vec3 dustCol = mix(uBg, vec3(shade), clamp(uFade, 0.0, 1.0));

  vec3 unrevealed = mix(mix(baseRgb, uBg, uiHome), dustCol, speck);
  vec3 col = mix(unrevealed, baseRgb, e);
  float alpha = mix(bC.a, dC.a, speck * (1.0 - e));
  outColor = vec4(col, alpha);
}`;

// ─────────────────────────────────────────────────────────────────────────────
// CPU Shader (simplified - no particles, no aberration, no bend, larger cells)
// ─────────────────────────────────────────────────────────────────────────────
const FRAG_CPU = `#version 300 es
precision highp float;
in vec2 vUv;
out vec4 outColor;
uniform sampler2D uContent;
uniform vec2 uRes;
uniform float uDpr;
uniform vec2 uPointer;
uniform float uActive;
uniform float uRadius;
uniform float uSoftness;
uniform float uTime;
uniform float uMaxX;
uniform float uCrisp;

vec4 samp (vec2 p) {
  vec2 uv = p / uRes;
  uv = clamp(uv, vec2(0.001), vec2(uMaxX - 0.001, 0.999));
  return texture(uContent, uv);
}

void main () {
  vec2 pc = vec2(vUv.x, 1.0 - vUv.y) * uRes;
  if (pc.x > uMaxX * uRes.x) {
    outColor = vec4(0.0);
    return;
  }
  if (uCrisp > 0.5) {
    outColor = samp(pc);
    return;
  }

  float dist = length(pc - uPointer);
  float radius = max(uRadius, 1.0);
  float inner = radius * (1.0 - clamp(uSoftness, 0.02, 1.0));
  float e = (1.0 - smoothstep(inner, radius, dist)) * uActive;

  // Simple radial reveal with soft edge - no particles, no warp, no CA
  vec2 bp = pc;
  vec4 base = samp(bp);
  vec3 baseRgb = base.rgb;

  // Subtle vignette at edge for visual interest
  float vignette = 1.0 - smoothstep(0.7, 1.0, dist / max(uRadius * 1.5, 1.0));
  vec3 col = mix(baseRgb, vec3(0.0), (1.0 - e) * 0.3 * vignette);
  float alpha = base.a * e;

  outColor = vec4(col, alpha);
}`;

// ─────────────────────────────────────────────────────────────────────────────
// CSS Fallback Keyframes (for environments without WebGL or extremely slow)
// ─────────────────────────────────────────────────────────────────────────────
const CSS_FALLBACK_STYLES = `
@keyframes particle-reveal-center-out {
  0% { clip-path: circle(0% at 50% 50%); opacity: 0; }
  50% { clip-path: circle(70% at 50% 50%); opacity: 1; }
  100% { clip-path: circle(150% at 50% 50%); opacity: 1; }
}
@keyframes particle-reveal-left-right {
  0% { clip-path: inset(0 100% 0 0); opacity: 0; }
  50% { clip-path: inset(0 30% 0 0); opacity: 1; }
  100% { clip-path: inset(0 -50% 0 0); opacity: 1; }
}
@keyframes particle-reveal-top-bottom {
  0% { clip-path: inset(0 0 100% 0); opacity: 0; }
  50% { clip-path: inset(0 0 30% 0); opacity: 1; }
  100% { clip-path: inset(0 0 -50% 0); opacity: 1; }
}
@keyframes particle-reveal-spiral {
  0% { clip-path: circle(0% at 50% 50%); transform: rotate(0deg); opacity: 0; }
  100% { clip-path: circle(150% at 50% 50%); transform: rotate(720deg); opacity: 1; }
}
@keyframes particle-reveal-wave {
  0% { clip-path: polygon(0 100%, 100% 100%, 100% 100%, 0 100%); opacity: 0; }
  50% { clip-path: polygon(0 100%, 50% 30%, 100% 100%, 0 100%); opacity: 1; }
  100% { clip-path: polygon(0 -50%, 50% -50%, 100% -50%, 0 -50%); opacity: 1; }
}
`;

function parseColor(input: string): [number, number, number] {
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true })!;
  ctx.fillStyle = '#000000';
  ctx.fillStyle = input;
  ctx.clearRect(0, 0, 1, 1);
  ctx.fillRect(0, 0, 1, 1);
  const data = ctx.getImageData(0, 0, 1, 1).data;
  return [data[0] / 255, data[1] / 255, data[2] / 255];
}

type QualityMode = 'auto' | 'high' | 'medium' | 'low' | 'css';

interface QualityConfig {
  useGPUShader: boolean;
  size: number;
  scatter: number;
  drift: number;
  aberration: number;
  bend: number;
  name: string;
}

const QUALITY_PRESETS: Record<Exclude<QualityMode, 'auto'>, QualityConfig> = {
  high: {     // Full GPU quality
    useGPUShader: true,
    size: 1,
    scatter: 30,
    drift: 1.5,
    aberration: 30,
    bend: 40,
    name: 'high (GPU)',
  },
  medium: {   // GPU with reduced particles
    useGPUShader: true,
    size: 1.5,
    scatter: 15,
    drift: 1.0,
    aberration: 15,
    bend: 20,
    name: 'medium (GPU)',
  },
  low: {      // CPU-optimized shader
    useGPUShader: false,
    size: 3,
    scatter: 0,
    drift: 0,
    aberration: 0,
    bend: 0,
    name: 'low (CPU shader)',
  },
  css: {      // Pure CSS fallback
    useGPUShader: false,
    size: 0,
    scatter: 0,
    drift: 0,
    aberration: 0,
    bend: 0,
    name: 'css fallback',
  },
};

interface ParticleRevealIntroProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  /** Animation duration in frames */
  durationInFrames?: number;
  /** Reveal animation type */
  animationType?: 'center-out' | 'left-right' | 'top-bottom' | 'spiral' | 'wave';
  /** Quality mode: 'auto' detects GPU vs CPU, or force a specific level */
  quality?: QualityMode;
  /** Particle effect options (used when quality='high' or 'medium') */
  radius?: number;
  softness?: number;
  size?: number;
  scatter?: number;
  drift?: number;
  aberration?: number;
  bend?: number;
  fade?: number;
  threshold?: number;
  background?: string;
  /** Primary color for text shadow (passed through for content styling) */
  primaryColor?: string;
  /** Called when quality mode is auto-detected */
  onQualityDetected?: (mode: Exclude<QualityMode, 'auto'>, renderer: string) => void;
}

export const ParticleRevealIntro: React.FC<ParticleRevealIntroProps> = ({
  children,
  className,
  style,
  durationInFrames = 120,
  animationType = 'center-out',
  quality = 'auto',
  radius = 400,
  softness = 0.7,
  // User-provided overrides (used when quality !== 'auto')
  size: userSize,
  scatter: userScatter,
  drift: userDrift,
  aberration: userAberration,
  bend: userBend,
  fade = 0.85,
  threshold = 0.1,
  background = '#000000',
  primaryColor,
  onQualityDetected,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sourceRef = useRef<HTMLCanvasElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const glRef = useRef<WebGL2RenderingContext | null>(null);
  const programRef = useRef<WebGLProgram | null>(null);
  const textureRef = useRef<WebGLTexture | null>(null);
  const uniformsRef = useRef<Record<string, WebGLUniformLocation>>({});
  const bgRef = useRef<[number, number, number]>([0, 0, 0]);
  const bgKeyRef = useRef<string>('');
  const [initialized, setInitialized] = useState(false);
  const [htmlInCanvasSupported, setHtmlInCanvasSupported] = useState(false);
  const [rendererInfo, setRendererInfo] = useState<{ renderer: string; isSoftware: boolean } | null>(null);
  const [activeQuality, setActiveQuality] = useState<Exclude<QualityMode, 'auto'>>('high');

  // ─────────────────────────────────────────────────────────────────────────
  // Detect renderer and select quality
  // ─────────────────────────────────────────────────────────────────────────
  const detectQuality = useMemo(() => {
    if (quality !== 'auto') {
      return quality;
    }
    // Default to high; will be overridden after WebGL init
    return 'high';
  }, [quality]);

  const effectiveQuality = activeQuality;

  // Merge user props with quality preset
  const config = useMemo(() => {
    const preset = QUALITY_PRESETS[effectiveQuality];
    return {
      useGPUShader: preset.useGPUShader,
      size: userSize ?? preset.size,
      scatter: userScatter ?? preset.scatter,
      drift: userDrift ?? preset.drift,
      aberration: userAberration ?? preset.aberration,
      bend: userBend ?? preset.bend,
    };
  }, [effectiveQuality, userSize, userScatter, userDrift, userAberration, userBend]);

  // ─────────────────────────────────────────────────────────────────────────
  // Check HTML-in-Canvas support
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const probe = document.createElement('canvas') as HTMLCanvasElement & { onpaint?: () => void; requestPaint?: () => void };
    const ctx = probe.getContext('2d') as CanvasRenderingContext2D & { drawElementImage?: (element: Element, x: number, y: number) => void };
    const supported = Boolean(
      ctx &&
      typeof ctx.drawElementImage === 'function' &&
      typeof probe.requestPaint === 'function'
    );
    setHtmlInCanvasSupported(supported);
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // Initialize WebGL and detect renderer
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    const source = sourceRef.current;
    if (!canvas || !source) return;

    const gl = canvas.getContext('webgl2', {
      alpha: true,
      depth: false,
      stencil: false,
      antialias: false,
      premultipliedAlpha: false,
    });
    if (!gl) {
      // No WebGL2 - fall back to CSS
      setActiveQuality('css');
      if (quality === 'auto' && onQualityDetected) {
        onQualityDetected('css', 'no-webgl2');
      }
      return;
    }

    glRef.current = gl;

    // ─── Detect software renderer (SwiftShader, llvmpipe, etc.) ───
    const renderer = gl.getParameter(gl.RENDERER) || '';
    const vendor = gl.getParameter(gl.VENDOR) || '';
    const isSoftware = /swiftshader|llvmpipe|mesa|software/i.test(renderer) ||
                       /swiftshader|mesa/i.test(vendor);

    setRendererInfo({ renderer, isSoftware });

    // Auto-select quality based on renderer
    if (quality === 'auto') {
      let detectedQuality: Exclude<QualityMode, 'auto'> = isSoftware ? 'low' : 'high';
      setActiveQuality(detectedQuality);
      if (onQualityDetected) {
        onQualityDetected(detectedQuality, renderer);
      }
    }

    // ─── Compile appropriate shader ───
    const compile = (type: number, text: string) => {
      const shader = gl.createShader(type)!;
      gl.shaderSource(shader, text);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('ParticleReveal shader error:', gl.getShaderInfoLog(shader));
      }
      return shader;
    };

    const vertexShader = compile(gl.VERTEX_SHADER, VERT);
    const fragmentShader = compile(gl.FRAGMENT_SHADER, config.useGPUShader ? FRAG_GPU : FRAG_CPU);
    const program = gl.createProgram()!;
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(program));
      // Fallback to CSS on shader failure
      setActiveQuality('css');
      if (quality === 'auto' && onQualityDetected) {
        onQualityDetected('css', `shader-fail: ${renderer}`);
      }
      return;
    }

    programRef.current = program;

    // Get uniforms
    const uniforms: Record<string, WebGLUniformLocation> = {};
    const count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < count; i++) {
      const info = gl.getActiveUniform(program, i)!;
      uniforms[info.name] = gl.getUniformLocation(program, info.name)!;
    }
    uniformsRef.current = uniforms;

    // Quad buffer
    const quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    // Texture
    const texture = gl.createTexture()!;
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
    textureRef.current = texture;

    setInitialized(true);

    return () => {
      gl.deleteTexture(texture);
      gl.deleteProgram(program);
      gl.deleteShader(vertexShader);
      gl.deleteShader(fragmentShader);
      gl.deleteBuffer(quad);
    };
  }, [config.useGPUShader, quality, onQualityDetected]);

  // ─────────────────────────────────────────────────────────────────────────
  // Inject CSS fallback styles if needed
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (effectiveQuality === 'css') {
      const styleEl = document.createElement('style');
      styleEl.textContent = CSS_FALLBACK_STYLES;
      document.head.appendChild(styleEl);
      return () => {
        document.head.removeChild(styleEl);
      };
    }
  }, [effectiveQuality]);

  // ─────────────────────────────────────────────────────────────────────────
  // Calculate animation progress
  // ─────────────────────────────────────────────────────────────────────────
  const progress = durationInFrames > 0 ? frame / durationInFrames : 1;
  const clampedProgress = Math.min(Math.max(progress, 0), 1);

  const pointerX = (() => {
    const w = width;
    const h = height;
    switch (animationType) {
      case 'center-out':
        return w / 2;
      case 'left-right':
        return w * clampedProgress;
      case 'top-bottom':
        return w / 2;
      case 'spiral': {
        const angle = clampedProgress * 4 * Math.PI;
        const r = Math.min(w, h) * 0.4 * clampedProgress;
        return w / 2 + Math.cos(angle) * r;
      }
      case 'wave': {
        return w / 2 + Math.sin(clampedProgress * 6 * Math.PI) * w * 0.3;
      }
      default:
        return w / 2;
    }
  })();

  const pointerY = (() => {
    const w = width;
    const h = height;
    switch (animationType) {
      case 'center-out':
        return h / 2;
      case 'left-right':
        return h / 2;
      case 'top-bottom':
        return h * clampedProgress;
      case 'spiral': {
        const angle = clampedProgress * 4 * Math.PI;
        const r = Math.min(w, h) * 0.4 * clampedProgress;
        return h / 2 + Math.sin(angle) * r;
      }
      case 'wave':
        return h / 2 + Math.cos(clampedProgress * 4 * Math.PI) * h * 0.2;
      default:
        return h / 2;
    }
  })();

  const currentRadius = animationType === 'center-out'
    ? radius * Math.min(1, clampedProgress * 3)
    : radius;

  const active = clampedProgress < 1 ? 1 : Math.max(0, 1 - (progress - 1) * 2);
  const time = frame / (fps || 30);

  // ─────────────────────────────────────────────────────────────────────────
  // CSS Fallback animation class
  // ─────────────────────────────────────────────────────────────────────────
  const cssAnimationClass = effectiveQuality === 'css' ? `particle-reveal-${animationType}` : '';

  // ─────────────────────────────────────────────────────────────────────────
  // Render WebGL effect (only for GPU/CPU shader modes)
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (effectiveQuality === 'css' || !initialized || !glRef.current || !programRef.current ||
        !canvasRef.current || !sourceRef.current || !contentRef.current) return;

    const gl = glRef.current;
    const program = programRef.current;
    const canvas = canvasRef.current;
    const source = sourceRef.current;
    const content = contentRef.current;
    const uniforms = uniformsRef.current;
    const texture = textureRef.current!;

    // Sync canvas sizes
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssWidth = Math.max(1, Math.round(canvas.clientWidth));
    const cssHeight = Math.max(1, Math.round(canvas.clientHeight));
    const glWidth = Math.max(1, Math.round(cssWidth * dpr));
    const glHeight = Math.max(1, Math.round(cssHeight * dpr));

    if (canvas.width !== glWidth || canvas.height !== glHeight) {
      canvas.width = glWidth;
      canvas.height = glHeight;
    }
    if (source.width !== glWidth || source.height !== glHeight) {
      source.width = glWidth;
      source.height = glHeight;
    }

    // Draw content to source canvas (HTML-in-Canvas)
    if (htmlInCanvasSupported) {
      const sourceCtx = source.getContext('2d') as CanvasRenderingContext2D & { drawElementImage?: (element: Element, x: number, y: number) => void };
      const paintable = source as HTMLCanvasElement & { requestPaint?: () => void };
      if (sourceCtx && typeof sourceCtx.drawElementImage === 'function' && typeof paintable.requestPaint === 'function') {
        sourceCtx.reset();
        sourceCtx.drawElementImage!(content, 0, 0);
      }
    }

    // Upload content to texture
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);

    // Render
    const w = Math.max(canvas.clientWidth, 1);
    const h = Math.max(canvas.clientHeight, 1);
    const renderDpr = canvas.width / w;
    const contentMaxX = Math.min(1, Math.max(0.05, content.clientWidth / Math.max(w, 1)));

    gl.useProgram(program);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(uniforms.uContent, 0);
    gl.uniform2f(uniforms.uRes, w, h);
    gl.uniform1f(uniforms.uDpr, renderDpr);
    gl.uniform2f(uniforms.uPointer, pointerX, pointerY);
    gl.uniform1f(uniforms.uActive, active);
    gl.uniform1f(uniforms.uRadius, Math.max(currentRadius, 1));
    gl.uniform1f(uniforms.uSoftness, softness);
    gl.uniform1f(uniforms.uTime, time);
    gl.uniform1f(uniforms.uMaxX, contentMaxX);
    gl.uniform1f(uniforms.uCrisp, htmlInCanvasSupported ? 0 : 1);

    // GPU-only uniforms
    if (config.useGPUShader) {
      gl.uniform1f(uniforms.uSize, Math.max(config.size, 0.5));
      gl.uniform1f(uniforms.uScatter, Math.max(config.scatter, 0));
      gl.uniform1f(uniforms.uDrift, Math.max(config.drift, 0));
      gl.uniform1f(uniforms.uAberration, Math.max(config.aberration, 0));
      gl.uniform1f(uniforms.uBend, Math.max(config.bend, 0));
      gl.uniform1f(uniforms.uFade, fade);
      gl.uniform1f(uniforms.uThreshold, Math.max(threshold, 0));
    }

    if (background !== bgKeyRef.current) {
      bgKeyRef.current = background;
      bgRef.current = parseColor(background);
    }
    gl.uniform3f(uniforms.uBg, bgRef.current[0], bgRef.current[1], bgRef.current[2]);

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }, [
    effectiveQuality,
    initialized,
    frame,
    pointerX,
    pointerY,
    currentRadius,
    active,
    time,
    htmlInCanvasSupported,
    config,
    softness,
    fade,
    threshold,
    background,
  ]);

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  const showWebGL = effectiveQuality !== 'css';
  const showFallback = !htmlInCanvasSupported && showWebGL;

  return (
    <div className={className} style={{ position: 'relative', width: '100%', height: '100%', ...style }}>
      {/* Source canvas - captures HTML content (for WebGL modes) */}
      {showWebGL && (
        <canvas
          ref={sourceRef}
          // @ts-expect-error experimental html-in-canvas attribute
          layoutsubtree="true"
          suppressHydrationWarning
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            display: htmlInCanvasSupported ? 'block' : 'none',
          }}
        >
          {htmlInCanvasSupported ? (
            <div
              ref={contentRef}
              style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                overflow: 'hidden',
              }}
            >
              {children}
            </div>
          ) : null}
        </canvas>
      )}

      {/* Fallback content for non-supported browsers or CSS mode */}
      {(showFallback || effectiveQuality === 'css') && (
        <div
          ref={contentRef}
          className={cssAnimationClass}
          style={{
            position: 'relative',
            width: '100%',
            height: '100%',
            overflow: 'hidden',
            animationDuration: `${durationInFrames / (fps || 30)}s`,
            animationTimingFunction: 'ease-out',
            animationFillMode: 'forwards',
          }}
        >
          {children}
        </div>
      )}

      {/* Output canvas - WebGL effect (GPU or CPU shader) */}
      {showWebGL && (
        <canvas
          ref={canvasRef}
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            display: htmlInCanvasSupported || effectiveQuality !== 'high' ? 'block' : 'none',
          }}
        />
      )}

      {/* Debug indicator (development only) */}
      {process.env.NODE_ENV !== 'production' && rendererInfo && (
        <div style={{
          position: 'absolute',
          top: 8, right: 8,
          padding: '4px 8px',
          background: 'rgba(0,0,0,0.7)',
          color: '#0f0',
          fontSize: '10px',
          fontFamily: 'monospace',
          borderRadius: 4,
          zIndex: 100,
          pointerEvents: 'none',
        }}>
          {rendererInfo.isSoftware ? '🖥️ CPU' : '🎮 GPU'} • {activeQuality} • {rendererInfo.renderer.slice(0, 40)}
        </div>
      )}
    </div>
  );
};

export default ParticleRevealIntro;