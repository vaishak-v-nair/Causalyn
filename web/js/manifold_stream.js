import * as THREE from 'https://cdn.skypack.dev/three@0.136.0';

let scene, camera, renderer, mesh, wireframeMesh, particles;
let kappaTarget = 0.0;
let currentKappa = 0.0;
let cameraMode = 'perspective'; // 'perspective' | 'top' | 'orbit'
let orbitAngle = 0;

export function initManifold() {
    const canvas = document.getElementById('manifold-canvas');
    if (!canvas) return;

    scene = new THREE.Scene();
    // Bright luminous fog matching alabaster body
    scene.fog = new THREE.FogExp2(0xF8FAFD, 0.025);

    camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 1000);
    setCameraPreset('perspective');

    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Symplectic Manifold Geometry
    const geometry = new THREE.PlaneGeometry(36, 36, 72, 72);
    geometry.rotateX(-Math.PI / 2);

    // High-density luminous surface
    const surfaceMaterial = new THREE.MeshPhongMaterial({
        color: 0x4F46E5,
        emissive: 0xEEF2FF,
        emissiveIntensity: 0.25,
        specular: 0x818CF8,
        shininess: 60,
        transparent: true,
        opacity: 0.82,
        side: THREE.DoubleSide,
        flatShading: false
    });

    mesh = new THREE.Mesh(geometry, surfaceMaterial);
    scene.add(mesh);

    // Crystalline Wireframe overlay for mathematical grid lines
    const wireframeMaterial = new THREE.MeshBasicMaterial({
        color: 0x312E81,
        wireframe: true,
        transparent: true,
        opacity: 0.45
    });

    wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial);
    scene.add(wireframeMesh);

    // Ambient floating quantum particles
    createQuantumParticles();

    // Lighting setup for bright, pristine look
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xEEF2FF, 0.8);
    dirLight1.position.set(20, 40, 20);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x0284C7, 0.4);
    dirLight2.position.set(-20, 20, -20);
    scene.add(dirLight2);

    window.addEventListener('resize', onWindowResize, false);
    animate();
}

function createQuantumParticles() {
    const count = 300;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 45;
        positions[i + 1] = (Math.random() - 0.2) * 20;
        positions[i + 2] = (Math.random() - 0.5) * 45;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
        color: 0x6366F1,
        size: 0.18,
        transparent: true,
        opacity: 0.45
    });

    particles = new THREE.Points(geometry, material);
    scene.add(particles);
}

export function updateKappaVisuals(kappa) {
    kappaTarget = Math.max(0.0, Math.min(kappa, 2.5));
    
    // Smooth transition between Safe Cobalt and Paradox Crimson
    if (kappaTarget > 0.05) {
        mesh.material.color.setHex(0xE11D48); // Vivid Rose Crimson
        mesh.material.emissive.setHex(0xFFF1F2);
        mesh.material.specular.setHex(0xF43F5E);
        wireframeMesh.material.color.setHex(0xBE123C);
    } else {
        mesh.material.color.setHex(0x4F46E5); // Royal Electric Indigo
        mesh.material.emissive.setHex(0xEEF2FF);
        mesh.material.specular.setHex(0x6366F1);
        wireframeMesh.material.color.setHex(0x3730A3);
    }
}

export function setCameraPreset(preset) {
    cameraMode = preset;
    if (preset === 'perspective') {
        camera.position.set(0, 11, 19);
        camera.lookAt(0, 1.5, 0);
    } else if (preset === 'top') {
        camera.position.set(0, 24, 0.01);
        camera.lookAt(0, 0, 0);
    } else if (preset === 'orbit') {
        camera.position.set(16, 11, 16);
        camera.lookAt(0, 1, 0);
    }
}

export function playManimVideo(b64VideoData) {
    const video = document.getElementById('manim-video-player');
    const placeholder = document.getElementById('manim-placeholder');
    
    if (video && b64VideoData) {
        if (placeholder) placeholder.style.display = 'none';
        video.style.display = 'block';
        video.src = 'data:video/mp4;base64,' + b64VideoData;
        video.currentTime = 0;
        video.play().catch(e => console.warn("Video auto-play suppressed", e));
    }
}

export function resetManimVideo() {
    const video = document.getElementById('manim-video-player');
    const placeholder = document.getElementById('manim-placeholder');
    
    if (video) {
        video.style.display = 'none';
        video.src = "";
    }
    if (placeholder) {
        placeholder.style.display = 'flex';
    }
}

function onWindowResize() {
    if (!camera || !renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);

    // Smooth asymptotic damping towards kappaTarget
    currentKappa += (kappaTarget - currentKappa) * 0.08;

    const time = Date.now() * 0.001;

    // Camera orbit animation if selected
    if (cameraMode === 'orbit') {
        orbitAngle += 0.004;
        camera.position.x = Math.cos(orbitAngle) * 24;
        camera.position.z = Math.sin(orbitAngle) * 24;
        camera.position.y = 12;
        camera.lookAt(0, 0, 0);
    }

    // Distort surface according to VPSN: z = sin(u)cos(v) + kappa * e^{-(u^2+v^2)}
    const posAttr = mesh.geometry.attributes.position;
    for (let i = 0; i < posAttr.count; i++) {
        const u = posAttr.getX(i);
        const v = posAttr.getZ(i);
        
        // Continuous wave
        let y = Math.sin(u * 0.4 + time * 0.8) * Math.cos(v * 0.4 + time * 0.8) * 1.4;
        
        // Concentrated Gaussian paradox peak at origin
        const distSq = (u * u + v * v) * 0.12;
        y += currentKappa * 6.5 * Math.exp(-distSq);

        posAttr.setY(i, y);
    }
    posAttr.needsUpdate = true;
    mesh.geometry.computeVertexNormals();

    // Subtle ambient particle floating
    if (particles) {
        particles.rotation.y = time * 0.02;
    }

    renderer.render(scene, camera);
}
