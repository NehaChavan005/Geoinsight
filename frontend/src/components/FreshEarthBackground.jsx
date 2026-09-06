import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useTexture } from '@react-three/drei';
import * as THREE from 'three';

export default function FreshEarthBackground({ appState, isLightMode }) {
  const earthRef = useRef();
  const [colorMap] = useTexture(['/earth-bg.png']);

  useFrame((state, delta) => {
    if (!earthRef.current) return;

    let targetPosition = new THREE.Vector3(0, -0.5, 0);
    let targetScale = 2.8;
    let rotationSpeed = 0.005;

    if (appState === 'intro') {
      targetPosition.set(0, -1.5, 0);
      targetScale = 2.5;
    } else if (appState === 'zooming') {
      targetPosition.set(2, 0, 2);
      targetScale = 6.0;
      rotationSpeed = 0.02;
    } else if (appState === 'dashboard') {
      targetPosition.set(0, -1.0, 0);
      targetScale = 1.8;
    }

    earthRef.current.position.lerp(targetPosition, delta * 3);

    const currentScale = earthRef.current.scale.x;
    const newScale = THREE.MathUtils.lerp(currentScale, targetScale, delta * 3);
    earthRef.current.scale.set(newScale, newScale, newScale);

    earthRef.current.rotation.y += rotationSpeed;
  });

  return (
    <>
      <ambientLight intensity={isLightMode ? 1.5 : 0.7} color={isLightMode ? '#ffffff' : '#e0f2fe'} />
      <directionalLight position={[5, 3, 5]} intensity={isLightMode ? 1.2 : 0.8} color="#f8fafc" />
      <pointLight position={[-5, 0, 5]} intensity={isLightMode ? 0.6 : 0.3} color="#38bdf8" distance={20} />

      <mesh ref={earthRef} scale={2.5} position={[0, -1.5, 0]}>
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial map={colorMap} roughness={0.7} metalness={0.05} />
      </mesh>
    </>
  );
}
