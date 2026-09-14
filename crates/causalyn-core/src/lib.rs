//! Causalyn Core: Native Performance Acceleration Kernel
//! 
//! High-throughput native routines for:
//! 1. Shannon entropy calculation for credentials/secret leakage detection (>1 GB/s)
//! 2. SHA-256 pairwise Merkle root calculation over candidate file states
//! 3. Continuous Symplectic Curvature tensor and Paradox Index (\u{03ba}) computation

use sha2::{Digest, Sha256};
use std::slice;

/// Computes Shannon entropy of a byte slice: H = - \sum p_i * log2(p_i)
#[no_mangle]
pub extern "C" fn causalyn_compute_entropy(data_ptr: *const u8, data_len: usize) -> f64 {
    if data_ptr.is_null() || data_len == 0 {
        return 0.0;
    }
    let data = unsafe { slice::from_raw_parts(data_ptr, data_len) };
    let mut counts = [0usize; 256];
    for &b in data {
        counts[b as usize] += 1;
    }

    let len_f = data_len as f64;
    let mut entropy = 0.0f64;
    for &count in &counts {
        if count > 0 {
            let p = count as f64 / len_f;
            entropy -= p * p.log2();
        }
    }
    entropy
}

/// Computes a pairwise SHA-256 Merkle root over 32-byte leaf hashes.
/// Output is written to `out_root_ptr` (must point to a 32-byte mutable buffer).
#[no_mangle]
pub extern "C" fn causalyn_compute_merkle_root(
    leaf_hashes_ptr: *const u8,
    num_leaves: usize,
    out_root_ptr: *mut u8,
) -> i32 {
    if leaf_hashes_ptr.is_null() || out_root_ptr.is_null() {
        return -1;
    }
    if num_leaves == 0 {
        // Empty tree hash: SHA256("")
        let empty_hash = Sha256::digest(b"");
        unsafe {
            std::ptr::copy_nonoverlapping(empty_hash.as_ptr(), out_root_ptr, 32);
        }
        return 0;
    }

    let leaf_slice = unsafe { slice::from_raw_parts(leaf_hashes_ptr, num_leaves * 32) };
    let mut current_layer: Vec<[u8; 32]> = Vec::with_capacity(num_leaves);
    for chunk in leaf_slice.chunks_exact(32) {
        let mut arr = [0u8; 32];
        arr.copy_from_slice(chunk);
        current_layer.push(arr);
    }

    while current_layer.len() > 1 {
        let mut next_layer = Vec::with_capacity((current_layer.len() + 1) / 2);
        for chunk in current_layer.chunks(2) {
            let mut hasher = Sha256::new();
            hasher.update(&chunk[0]);
            if chunk.len() > 1 {
                hasher.update(&chunk[1]);
            } else {
                // Odd leaf: duplicate
                hasher.update(&chunk[0]);
            }
            let res = hasher.finalize();
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&res);
            next_layer.push(arr);
        }
        current_layer = next_layer;
    }

    unsafe {
        std::ptr::copy_nonoverlapping(current_layer[0].as_ptr(), out_root_ptr, 32);
    }
    0
}

/// Computes continuous symplectic curvature metric for the Vaishak Continuum:
/// \u{03ba} = ||\u{2207} I|| * (1.0 - tanh(c_s * c_c))
#[no_mangle]
pub extern "C" fn causalyn_compute_symplectic_curvature(
    t: f64,
    cs: f64,
    cc: f64,
    grad_x: f64,
    grad_y: f64,
    grad_z: f64,
) -> f64 {
    let grad_norm = (grad_x * grad_x + grad_y * grad_y + grad_z * grad_z).sqrt();
    let semantic_admissibility = (cs * cc).tanh().max(0.0).min(1.0);
    let time_decay = 1.0 / (1.0 + 0.05 * t.max(0.0));
    let curvature = grad_norm * (1.0 - semantic_admissibility) * time_decay;
    curvature.max(0.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shannon_entropy() {
        let low_entropy = b"aaaaaaaaaaaaaaaaaaaaaaaa";
        let score_low = causalyn_compute_entropy(low_entropy.as_ptr(), low_entropy.len());
        assert_eq!(score_low, 0.0);

        let high_entropy = b"sK_93jd71!aL#001zq?_P8$!kLz0";
        let score_high = causalyn_compute_entropy(high_entropy.as_ptr(), high_entropy.len());
        assert!(score_high > 3.8);
    }

    #[test]
    fn test_merkle_root() {
        let mut leaf = [0u8; 32];
        leaf[0] = 1;
        let mut out = [0u8; 32];
        let res = causalyn_compute_merkle_root(leaf.as_ptr(), 1, out.as_mut_ptr());
        assert_eq!(res, 0);
        assert_ne!(out, [0u8; 32]);
    }

    #[test]
    fn test_symplectic_curvature() {
        let k = causalyn_compute_symplectic_curvature(0.0, 1.0, 1.0, 0.0, 0.0, 0.0);
        assert_eq!(k, 0.0);

        let k_spike = causalyn_compute_symplectic_curvature(0.0, 0.0, 0.0, 1.0, 1.0, 1.0);
        assert!(k_spike > 1.5);
    }
}
