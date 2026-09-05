import * as THREE from 'https://cdn.skypack.dev/three@0.136.0';

let scene, camera, renderer, mesh, wireframeMesh, particles, epicenterLight;
let kappaTarget = 0.0;
let currentKappa = 0.0;
let cameraMode = 'perspective'; // 'perspective' | 'top' | 'orbit'
let orbitAngle = 0;

export function initManifold() {
    const canvas = document.getElementById('manifold-canvas');
    if (!canvas) return;

    scene = new THREE.Scene();
    // Deep obsidian cyber-industrial fog
    scene.fog = new THREE.FogExp2(0x030712, 0.024);

    camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 1000);
    setCameraPreset('perspective');

    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Symplectic Manifold Geometry
    const geometry = new THREE.PlaneGeometry(36, 36, 72, 72);
    geometry.rotateX(-Math.PI / 2);

    // Deep obsidian cyber-industrial surface with phosphor cyan specular
    const surfaceMaterial = new THREE.MeshPhongMaterial({
        color: 0x050C1A,
        emissive: 0x001B2E,
        emissiveIntensity: 0.35,
        specular: 0x00F3FF,
        shininess: 90,
        transparent: true,
        opacity: 0.88,
        side: THREE.DoubleSide,
        flatShading: false
    });

    mesh = new THREE.Mesh(geometry, surfaceMaterial);
    scene.add(mesh);

    // High-contrast Phosphor Cyan Wireframe grid
    const wireframeMaterial = new THREE.MeshBasicMaterial({
        color: 0x00F3FF,
        wireframe: true,
        transparent: true,
        opacity: 0.65
    });

    wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial);
    scene.add(wireframeMesh);

    // Ambient floating quantum dust particles in phosphor cyan
    createQuantumParticles();

    // Cyber-industrial lighting setup
    const ambientLight = new THREE.AmbientLight(0x0A192F, 0.7);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00F3FF, 0.8);
    dirLight1.position.set(20, 35, 20);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x0284C7, 0.5);
    dirLight2.position.set(-20, 20, -20);
    scene.add(dirLight2);

    // Epicenter dynamic point light at the Gaussian deformation origin
    epicenterLight = new THREE.PointLight(0x00F3FF, 1.2, 35);
    epicenterLight.position.set(0, 3.5, 0);
    scene.add(epicenterLight);

    window.addEventListener('resize', onWindowResize, false);
    animate();
}

function createQuantumParticles() {
    const count = 350;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 45;
        positions[i + 1] = (Math.random() - 0.2) * 22;
        positions[i + 2] = (Math.random() - 0.5) * 45;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
        color: 0x00F3FF,
        size: 0.16,
        transparent: true,
        opacity: 0.65
    });

    particles = new THREE.Points(geometry, material);
    scene.add(particles);
}

export function updateKappaVisuals(kappa) {
    kappaTarget = Math.max(0.0, Math.min(kappa, 2.5));
    
    // Dynamic transition: Phosphor Cyan (Equilibrium) <-> Violent Infrared Crimson (Paradox)
    if (kappaTarget > 0.05) {
        mesh.material.color.setHex(0x1F050A);      // Deep obsidian crimson
        mesh.material.emissive.setHex(0xFF1E44);   // Violent infrared crimson
        mesh.material.specular.setHex(0xFF3355);   // High-intensity crimson specular
        wireframeMesh.material.color.setHex(0xFF1E44);
        wireframeMesh.material.opacity = 0.95;
        if (epicenterLight) {
            epicenterLight.color.setHex(0xFF1E44);
        }
        if (particles) {
            particles.material.color.setHex(0xFF1E44);
        }
    } else {
        mesh.material.color.setHex(0x050C1A);      // Deep obsidian base
        mesh.material.emissive.setHex(0x001B2E);   // Subtle cyan-indigo glow
        mesh.material.specular.setHex(0x00F3FF);   // Brilliant phosphor cyan specular
        wireframeMesh.material.color.setHex(0x00F3FF);
        wireframeMesh.material.opacity = 0.65;
        if (epicenterLight) {
            epicenterLight.color.setHex(0x00F3FF);
        }
        if (particles) {
            particles.material.color.setHex(0x00F3FF);
        }
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

    // Dynamic light intensity and emissive response scaling with kappa
    if (epicenterLight) {
        if (currentKappa > 0.05) {
            epicenterLight.intensity = 1.5 + currentKappa * 5.0;
            mesh.material.emissiveIntensity = 0.35 + currentKappa * 0.85;
        } else {
            epicenterLight.intensity = 1.2 + Math.sin(time * 2.0) * 0.2;
            mesh.material.emissiveIntensity = 0.35;
        }
    }

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
        let y = Math.sin(u * 0.4 + time * 0.8) * Math.cos(v * 0.4 + time * 0.8) * 1.3;
        
        // Concentrated Gaussian paradox peak at origin (Violent Infrared Spike)
        const distSq = (u * u + v * v) * 0.12;
        y += currentKappa * 7.5 * Math.exp(-distSq);

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
