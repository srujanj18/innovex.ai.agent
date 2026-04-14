tsx
import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const vertexShader = `
uniform float uTime;
uniform float uAmp;
uniform float uSpeed;
varying vec2 vUv;
varying float vElevation;

// Classic Perlin 3D Noise 
// by Stefan Gustavson
vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}
vec3 fade(vec3 t) {return t*t*t*(t*(t*6.0-15.0)+10.0);}

float cnoise(vec3 P){
  vec3 Pi0 = floor(P);
  vec3 Pi1 = Pi0 + vec3(1.0);
  Pi0 = mod(Pi0, 289.0);
  Pi1 = mod(Pi1, 289.0);
  vec3 Pf0 = fract(P);
  vec3 Pf1 = Pf0 - vec3(1.0);
  vec4 ix = vec4(Pi0.x, Pi1.x, Pi0.x, Pi1.x);
  vec4 iy = vec4(Pi0.yy, Pi1.yy);
  vec4 iz0 = Pi0.zzzz;
  vec4 iz1 = Pi1.zzzz;

  vec4 ixy = permute(permute(ix) + iy);
  vec4 ixy0 = permute(ixy + iz0);
  vec4 ixy1 = permute(ixy + iz1);

  vec4 gx0 = ixy0 / 7.0;
  vec4 gy0 = fract(floor(gx0) / 7.0) - 0.5;
  gx0 = fract(gx0);
  vec4 gz0 = vec4(0.5) - abs(gx0) - abs(gy0);
  vec4 sz0 = step(gz0, vec4(0.0));
  gx0 -= sz0 * (step(0.0, gx0) - 0.5);
  gy0 -= sz0 * (step(0.0, gy0) - 0.5);

  vec4 gx1 = ixy1 / 7.0;
  vec4 gy1 = fract(floor(gx1) / 7.0) - 0.5;
  gx1 = fract(gx1);
  vec4 gz1 = vec4(0.5) - abs(gx1) - abs(gy1);
  vec4 sz1 = step(gz1, vec4(0.0));
  gx1 -= sz1 * (step(0.0, gx1) - 0.5);
  gy1 -= sz1 * (step(0.0, gy1) - 0.5);

  vec3 g000 = vec3(gx0.x,gy0.x,gz0.x);
  vec3 g100 = vec3(gx0.y,gy0.y,gz0.y);
  vec3 g010 = vec3(gx0.z,gy0.z,gz0.z);
  vec3 g110 = vec3(gx0.w,gy0.w,gz0.w);
  vec3 g001 = vec3(gx1.x,gy1.x,gz1.x);
  vec3 g101 = vec3(gx1.y,gy1.y,gz1.y);
  vec3 g011 = vec3(gx1.z,gy1.z,gz1.z);
  vec3 g111 = vec3(gx1.w,gy1.w,gz1.w);

  vec4 norm0 = taylorInvSqrt(vec4(dot(g000, g000), dot(g010, g010), dot(g100, g100), dot(g110, g110)));
  g000 *= norm0.x;
  g010 *= norm0.y;
  g100 *= norm0.z;
  g110 *= norm0.w;
  vec4 norm1 = taylorInvSqrt(vec4(dot(g001, g001), dot(g011, g011), dot(g101, g101), dot(g111, g111)));
  g001 *= norm1.x;
  g011 *= norm1.y;
  g101 *= norm1.z;
  g111 *= norm1.w;

  float n000 = dot(g000, Pf0);
  float n100 = dot(g100, vec3(Pf1.x, Pf0.yz));
  float n010 = dot(g010, vec3(Pf0.x, Pf1.y, Pf0.z));
  float n110 = dot(g110, vec3(Pf1.xy, Pf0.z));
  float n001 = dot(g001, vec3(Pf0.xy, Pf1.z));
  float n101 = dot(g101, vec3(Pf1.x, Pf0.y, Pf1.z));
  float n011 = dot(g011, vec3(Pf0.x, Pf1.yz));
  float n111 = dot(g111, Pf1);

  vec3 fade_xyz = fade(Pf0);
  vec4 n_z = mix(vec4(n000, n100, n010, n110), vec4(n001, n101, n011, n111), fade_xyz.z);
  vec2 n_yz = mix(n_z.xy, n_z.zw, fade_xyz.y);
  float n_xyz = mix(n_yz.x, n_yz.y, fade_xyz.x); 
  return 2.2 * n_xyz;
}

void main() {
  vUv = uv;
  vec3 pos = position;

  float time = uTime * uSpeed;
  
  // Add multiple layers of noise for complex displacement
  float n1 = cnoise(vec3(pos.x * 2.5 + time * 0.2, pos.y * 2.5 - time * 0.1, time * 0.1));
  float n2 = cnoise(vec3(pos.x * 5.0 - time * 0.3, pos.y * 5.0 + time * 0.2, time * 0.2));
  float n3 = cnoise(vec3(pos.x * 10.0, pos.y * 10.0, time * 0.4));
  
  float elevation = (n1 * 0.15 + n2 * 0.05 + n3 * 0.02) * uAmp;
  
  pos.z += elevation;
  vElevation = elevation;

  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
`;

const fragmentShader = `
uniform float uTime;
uniform float uSpeed;
uniform vec3 uColorStart;
uniform vec3 uColorEnd;
uniform vec3 uColorGrid;
uniform float uWireframeStr;
varying vec2 vUv;
varying float vElevation;

void main() {
  float mixStrength = (vElevation + 0.15) * 3.5;
  mixStrength = smoothstep(0.0, 1.0, mixStrength);
  
  float time = uTime * uSpeed;
  float pulse = sin(time * 2.0 - vElevation * 15.0) * 0.5 + 0.5;
  
  vec3 color = mix(uColorStart, uColorEnd, mixStrength);
  
  // Peaks bright
  vec3 glowColor = mix(uColorEnd, vec3(1.0), 0.5);
  float glowStrength = pow(mixStrength, 2.5) * (0.8 + 0.4 * pulse);
  color = mix(color, glowColor, glowStrength);
  
  // Grid
  vec2 grid = fract(vUv * 50.0);
  float edge = 0.08;
  float isGrid = step(grid.x, edge) + step(grid.y, edge);
  isGrid = clamp(isGrid, 0.0, 1.0);
  
  float gridFade = mix(0.05, uWireframeStr, mixStrength);
  color = mix(color, uColorGrid, isGrid * gridFade * uWireframeStr);

  // Vignette
  float dist = distance(vUv, vec2(0.5));
  float alpha = 1.0 - smoothstep(0.35, 0.5, dist);
  
  gl_FragColor = vec4(color, alpha * 0.9);
}
`;

// Dynamic states mapped to App.tsx sections
const SECTIONS_CONFIG: Record<string, any> = {
  hero: { start: '#0a0200', end: '#ff3300', grid: '#ff1100', speed: 1.0, wireframe: 0.15, amp: 1.0 },
  about: { start: '#000814', end: '#00aaff', grid: '#0044ff', speed: 0.4, wireframe: 0.8, amp: 0.4 },
  services: { start: '#080014', end: '#aa00ff', grid: '#5500ff', speed: 1.2, wireframe: 0.4, amp: 1.5 },
  projects: { start: '#000a02', end: '#00ff44', grid: '#00aa22', speed: 1.8, wireframe: 0.6, amp: 0.8 },
  whychoose: { start: '#0a0800', end: '#ffaa00', grid: '#ff6600', speed: 0.6, wireframe: 0.3, amp: 0.7 },
  student: { start: '#080010', end: '#ff00aa', grid: '#aa00ff', speed: 1.4, wireframe: 0.7, amp: 1.2 },
  contact: { start: '#1a0000', end: '#ff0000', grid: '#aa0000', speed: 2.0, wireframe: 0.1, amp: 2.0 },
  footer: { start: '#020202', end: '#333333', grid: '#111111', speed: 0.2, wireframe: 0.05, amp: 0.2 },
};

function LavaMesh({ activeSection }: { activeSection: string }) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uColorStart: { value: new THREE.Color() },
      uColorEnd: { value: new THREE.Color() },
      uColorGrid: { value: new THREE.Color() },
      uSpeed: { value: 0 },
      uWireframeStr: { value: 0 },
      uAmp: { value: 0 },
    }),
    []
  );

  useFrame((state, delta) => {
    if (!materialRef.current) return;
    
    // Increment time
    materialRef.current.uniforms.uTime.value += delta;
    
    // Get target config based on active section
    const target = SECTIONS_CONFIG[activeSection] || SECTIONS_CONFIG['hero'];
    
    // Smoothly interpolate towards target values for a seamless transition
    const lerpFactor = 2.0 * delta; // Adjust transition speed here
    
    const m = materialRef.current;
    
    const targetStart = new THREE.Color(target.start);
    const targetEnd = new THREE.Color(target.end);
    const targetGrid = new THREE.Color(target.grid);
    
    m.uniforms.uColorStart.value.lerp(targetStart, lerpFactor);
    m.uniforms.uColorEnd.value.lerp(targetEnd, lerpFactor);
    m.uniforms.uColorGrid.value.lerp(targetGrid, lerpFactor);
    
    m.uniforms.uSpeed.value = THREE.MathUtils.lerp(m.uniforms.uSpeed.value, target.speed, lerpFactor);
    m.uniforms.uWireframeStr.value = THREE.MathUtils.lerp(m.uniforms.uWireframeStr.value, target.wireframe, lerpFactor);
    m.uniforms.uAmp.value = THREE.MathUtils.lerp(m.uniforms.uAmp.value, target.amp, lerpFactor);
  });

  return (
    <mesh rotation={[-Math.PI / 2.3, 0, 0]} position={[0, -0.2, -1.0]} scale={[3.0, 3.0, 1.0]}>
      <planeGeometry args={[1, 1, 256, 256]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent={true}
        depthWrite={false}
      />
    </mesh>
  );
}

const LavaBackground = ({ activeSection = 'hero' }: { activeSection?: string }) => {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none opacity-90">
      <Canvas
        camera={{ position: [0, 0.3, 0.8], fov: 60 }}
        gl={{ alpha: true, antialias: false, powerPreference: 'high-performance' }}
        dpr={[1, 2]}
      >
        <color attach="background" args={['#020202']} />
        <fog attach="fog" args={['#020202', 0.5, 2.0]} />
        <LavaMesh activeSection={activeSection} />
      </Canvas>
    </div>
  );
};

export default LavaBackground;