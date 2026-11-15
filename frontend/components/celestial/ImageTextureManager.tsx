"use client";

import { useEffect, useState, useRef } from "react";
import * as THREE from "three";

/**
 * Hook to manage loading, caching, and clean disposal of Three.js textures
 * from Data URIs or image URLs without leaking WebGL GPU memory.
 */
export function useAstronomicalTexture(dataUri: string | null) {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const prevTextureRef = useRef<THREE.Texture | null>(null);

  useEffect(() => {
    if (!dataUri) {
      if (prevTextureRef.current) {
        prevTextureRef.current.dispose();
        prevTextureRef.current = null;
      }
      setTexture(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    const loader = new THREE.TextureLoader();
    let isCancelled = false;

    loader.load(
      dataUri,
      (loadedTex) => {
        if (isCancelled) {
          loadedTex.dispose();
          return;
        }

        // Astronomical texture configuration
        loadedTex.wrapS = THREE.ClampToEdgeWrapping;
        loadedTex.wrapT = THREE.ClampToEdgeWrapping;
        loadedTex.minFilter = THREE.LinearMipmapLinearFilter;
        loadedTex.magFilter = THREE.LinearFilter;
        loadedTex.generateMipmaps = true;
        loadedTex.needsUpdate = true;

        // Dispose previous texture
        if (prevTextureRef.current) {
          prevTextureRef.current.dispose();
        }

        prevTextureRef.current = loadedTex;
        setTexture(loadedTex);
        setIsLoading(false);
      },
      undefined,
      (err) => {
        if (!isCancelled) {
          setError("Failed to load astronomical image texture");
          setIsLoading(false);
        }
      }
    );

    return () => {
      isCancelled = true;
    };
  }, [dataUri]);

  // Clean disposal on unmount
  useEffect(() => {
    return () => {
      if (prevTextureRef.current) {
        prevTextureRef.current.dispose();
        prevTextureRef.current = null;
      }
    };
  }, []);

  return { texture, isLoading, error };
}
